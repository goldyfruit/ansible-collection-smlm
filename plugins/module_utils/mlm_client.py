# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Gaëtan Trellu <gaetan.trellu@suse.com>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module provides a client for interacting with the SUSE Multi-Linux Manager API.

It handles authentication, session management, and provides methods for making
REST API requests to manage systems and other resources in MLM.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import time
import json
from typing import Dict, List, Optional, Tuple, Union, Any
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native, to_text

# Try to import yaml, with fallback
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Define constants for environment variables
ENV_MLM_URL = "MLM_URL"
ENV_MLM_USERNAME = "MLM_USERNAME"
ENV_MLM_PASSWORD = "MLM_PASSWORD"
ENV_MLM_API_BASE_PATH = "MLM_API_BASE_PATH"

# Default API base path
DEFAULT_API_BASE_PATH = "/rhn/manager/api"

# HTTP status codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500

# Default timeout and retry values
DEFAULT_TIMEOUT = 60
DEFAULT_RETRIES = 3
DEFAULT_CACHE_TIMEOUT = 3600
MAX_BACKOFF_DELAY = 60

# Default API endpoints for REST API
DEFAULT_API_ENDPOINTS = {
    "login": "/auth/login",
    "logout": "/auth/logout",
    "systems": "/system/listSystems",
    "relevant_errata": "/system/getRelevantErrata",  # Used with ?sid={system_id}
    "registration_date": "/system/getRegistrationDate",  # Used with ?sid={system_id}
    "system_groups": "/system/listGroups",  # Used with ?sid={system_id}
    "org_list": "/org/listOrgs",
    "org_details": "/org/getDetails",  # Used with ?orgId={org_id} or ?name={org_name}
    "systems_reboot": "/system/listSuggestedReboot",  # Systems that require reboot
}

# Default field mappings for API responses
DEFAULT_FIELD_MAPPINGS = {
    "system": {
        "id": "id",
        "name": "name",
        "hostname": "hostname",
        "active": "active",
        "registration_date": ["created", "registered", "registrationDate"],
        "last_checkin": "lastCheckin",
        "last_boot": "lastBoot",
    }
}


def check_api_response(response: Union[Dict[str, Any], Any], operation_name: str, module: Any) -> Union[Dict[str, Any], Any]:
    """
    Check API response for success/failure and handle errors.

    This function provides a global way to validate API responses across all modules
    in the collection. Many SUSE Multi-Linux Manager API endpoints return HTTP 200 even for
    errors, but include error information in the response body.

    Args:
        response: The API response object.
        operation_name: The name of the operation being performed.
        module: The AnsibleModule instance.

    Returns:
        dict: The response if successful.

    Raises:
        AnsibleFailJson: If the API response indicates failure.
    """
    if isinstance(response, dict):
        # Check for API-level errors (success=false)
        if response.get("success") is False:
            error_msg = response.get("message", "Unknown API error")
            module.fail_json(
                msg=format_error_message(operation_name, error_msg),
                api_response=response,
            )

        # Check for other error indicators
        if "error" in response:
            module.fail_json(
                msg=format_error_message(operation_name, response["error"]),
                api_response=response,
            )

    return response


def format_error_message(operation_name: str, error_details: str, context: Optional[str] = None) -> str:
    """
    Create a standardized error message format.

    Args:
        operation_name: The name of the operation that failed
        error_details: Details about what went wrong
        context: Optional additional context

    Returns:
        str: Formatted error message
    """
    if context:
        return "SUSE Multi-Linux Manager API - {}: {} (Context: {})".format(
            operation_name, error_details, context
        )
    return "SUSE Multi-Linux Manager API - {}: {}".format(operation_name, error_details)


def format_success_message(operation_name: str, details: str, entity_type: Optional[str] = None) -> str:
    """
    Create a standardized success message format.

    Args:
        operation_name: The name of the operation that succeeded
        details: Details about what was accomplished
        entity_type: Optional type of entity that was operated on

    Returns:
        str: Formatted success message
    """
    if entity_type:
        return "{} {} {}".format(entity_type, operation_name.lower(), details)
    return "{} {}".format(operation_name, details)


class MLMClient:
    """
    Client for interacting with the SUSE Multi-Linux Manager API.

    This class provides methods for authenticating with the API, making
    requests, and handling common operations like pagination and error handling.
    """

    def __init__(self, module: Any) -> None:
        """
        Initialize the MLM client.

        Args:
            module: The AnsibleModule instance.
        """
        self.module = module
        self.url = None
        self.username = None
        self.password = None
        self.validate_certs = True
        self.timeout = DEFAULT_TIMEOUT
        self.retries = DEFAULT_RETRIES
        self.session_cookies = None
        self.api_base_path = DEFAULT_API_BASE_PATH
        self.api_endpoints = DEFAULT_API_ENDPOINTS
        self.field_mappings = DEFAULT_FIELD_MAPPINGS

        # Initialize parameters with safe defaults
        try:
            # First, attempt to load credentials from file if it exists
            self._load_credentials()

            # Get connection parameters with priority: module params > env vars > credentials file
            # Only override if not already set by credentials file
            if not self.url:
                self.url = self._get_param("url", ENV_MLM_URL)
            if not self.username:
                self.username = self._get_param("username", ENV_MLM_USERNAME)
            if not self.password:
                self.password = self._get_param("password", ENV_MLM_PASSWORD)

            # Ensure validate_certs is a boolean
            self.validate_certs = module.boolean(
                module.params.get("validate_certs", True)
            )

            self.timeout = module.params.get("timeout", DEFAULT_TIMEOUT)
            self.retries = module.params.get("retries", DEFAULT_RETRIES)

            # Get API configuration
            self.api_base_path = module.params.get(
                "api_base_path",
                os.environ.get(ENV_MLM_API_BASE_PATH, DEFAULT_API_BASE_PATH),
            )
            self.api_endpoints = module.params.get(
                "api_endpoints", DEFAULT_API_ENDPOINTS
            )
            # Ensure field_mappings is never None
            field_mappings = module.params.get("field_mappings")
            self.field_mappings = (
                field_mappings if field_mappings is not None else DEFAULT_FIELD_MAPPINGS
            )

            # Ensure we have the required parameters
            self._validate_required_params()

            # Ensure URL is not None before proceeding
            if self.url is None:
                self.module.fail_json(
                    msg="URL is not set. Please provide a valid URL via the 'url' parameter or MLM_URL environment variable."
                )

            # Ensure URL is a string
            self.url = str(self.url)

            # Ensure api_base_path is a string
            if self.api_base_path is None:
                self.api_base_path = DEFAULT_API_BASE_PATH
            else:
                self.api_base_path = str(self.api_base_path)

            # Normalize the URL (remove trailing slash)
            if self.url.endswith("/"):
                self.url = self.url[:-1]

            # Ensure URL ends with the API base path if not already
            if not self.url.endswith(self.api_base_path):
                self.url = self.url + self.api_base_path
        except Exception as e:
            self.module.fail_json(
                msg="Error initializing MLM client: {}".format(str(e))
            )

    def _load_credentials(self):
        """
        Load credentials from ~/.config/smlm/credentials.yaml if it exists and set instance variables.

        Returns:
            bool: True if credentials were loaded successfully, False otherwise.
        """
        if not HAS_YAML:
            self.module.log(
                msg="YAML library not available, cannot load credentials file"
            )
            return False

        credentials_path = os.path.expanduser("~/.config/smlm/credentials.yaml")

        if not os.path.exists(credentials_path):
            self.module.log(
                msg="Credentials file not found at {}".format(credentials_path)
            )
            return False

        try:
            with open(credentials_path, "r") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                self.module.log(
                    msg="Credentials file content is not a valid dictionary"
                )
                return False

            # Get the instance name from module params or use default
            instance_name = self.module.params.get("instance")
            if not instance_name:
                instance_name = config.get("default")

            # If still no instance name and there's only one instance, use it
            if not instance_name and "instances" in config:
                instances = config["instances"]
                if isinstance(instances, dict) and len(instances) == 1:
                    instance_name = list(instances.keys())[0]

            # Load credentials from the selected instance
            if "instances" in config:
                instances = config["instances"]
                if isinstance(instances, dict):
                    if instance_name and instance_name in instances:
                        instance_config = instances[instance_name]
                    elif len(instances) == 1:
                        instance_config = list(instances.values())[0]
                    else:
                        instance_config = None

                    if instance_config and isinstance(instance_config, dict):
                        if not self.url and "url" in instance_config:
                            self.url = instance_config["url"]
                        if not self.username and "username" in instance_config:
                            self.username = instance_config["username"]
                        if not self.password and "password" in instance_config:
                            self.password = instance_config["password"]
                        if "validate_certs" in instance_config:
                            self.validate_certs = instance_config["validate_certs"]

            self.module.log(msg="Credentials file loaded successfully")
            return True
        except Exception as e:
            self.module.log(msg="Error loading credentials file: {}".format(str(e)))
            return False

    def _get_default_instance_config(self, credentials_config):
        """
        Get the default instance configuration from credentials file.

        Args:
            credentials_config: The loaded credentials configuration.

        Returns:
            dict: The default instance configuration, or None if not found.
        """
        if not credentials_config:
            return None

        # Check if there's a default instance specified
        default_instance = credentials_config.get("default")
        if default_instance and "instances" in credentials_config:
            instances = credentials_config["instances"]
            if isinstance(instances, dict) and default_instance in instances:
                return instances[default_instance]

        # If no default specified but there's only one instance, use it
        if "instances" in credentials_config:
            instances = credentials_config["instances"]
            if isinstance(instances, dict) and len(instances) == 1:
                return list(instances.values())[0]

        return None

    def _get_param_with_credentials(self, param_name, env_var, credentials_config):
        """
        Get a parameter value with priority: module params > env vars > credentials file.

        Args:
            param_name: The name of the parameter in the module params.
            env_var: The name of the environment variable to check.
            credentials_config: The loaded credentials configuration.

        Returns:
            The parameter value or None if not found.
        """
        # First priority: module parameters
        value = self.module.params.get(param_name)
        if value:
            return value

        # Second priority: environment variables
        value = os.environ.get(env_var)
        if value:
            return value

        # Third priority: credentials file
        instance_name = self.module.params.get("instance")
        if credentials_config and "instances" in credentials_config:
            instances = credentials_config["instances"]
            if isinstance(instances, dict):
                if instance_name and instance_name in instances:
                    instance_config = instances[instance_name]
                else:
                    instance_config = self._get_default_instance_config(
                        credentials_config
                    )
                if instance_config and isinstance(instance_config, dict):
                    return instance_config.get(param_name)

        return None

    def _get_validate_certs_with_credentials(self, credentials_config):
        """
        Get validate_certs value with priority: module params > credentials file > default.

        Args:
            credentials_config: The loaded credentials configuration.

        Returns:
            bool: The validate_certs value.
        """
        # First priority: module parameters
        module_value = self.module.params.get("validate_certs")
        if module_value is not None:
            return self.module.boolean(module_value)

        # Second priority: credentials file
        instance_name = self.module.params.get("instance")
        if credentials_config and "instances" in credentials_config:
            instances = credentials_config["instances"]
            if isinstance(instances, dict):
                if instance_name and instance_name in instances:
                    instance_config = instances[instance_name]
                else:
                    instance_config = self._get_default_instance_config(
                        credentials_config
                    )
                if instance_config and isinstance(instance_config, dict):
                    file_value = instance_config.get("validate_certs")
                    if file_value is not None:
                        return self.module.boolean(file_value)

        # Default: True
        return True

    def _get_param(self, param_name, env_var):
        """
        Get a parameter value from module params or environment variable.

        Args:
            param_name: The name of the parameter in the module params.
            env_var: The name of the environment variable to check.

        Returns:
            The parameter value or None if not found.
        """
        value = self.module.params.get(param_name)
        if not value:
            value = os.environ.get(env_var)
        return value

    def _validate_required_params(self):
        """
        Validate that required parameters are present.

        Raises:
            AnsibleFailJson: If any required parameters are missing.
        """
        missing_params = []

        if not self.url:
            missing_params.append(
                "url (or {} environment variable)".format(ENV_MLM_URL)
            )
        if not self.username:
            missing_params.append(
                "username (or {} environment variable)".format(ENV_MLM_USERNAME)
            )
        if not self.password:
            missing_params.append(
                "password (or {} environment variable)".format(ENV_MLM_PASSWORD)
            )

        if missing_params:
            self.module.fail_json(
                msg="Missing required parameters: {}".format(", ".join(missing_params))
            )

    def login(self) -> str:
        """
        Authenticate with the MLM API and get session cookies.

        Returns:
            str: The session cookies.

        Raises:
            AnsibleFailJson: If authentication fails.
        """
        if self.session_cookies:
            return self.session_cookies

        try:
            login_data = {"login": self.username, "password": self.password}

            # Ensure api_endpoints is initialized and has the login key
            if self.api_endpoints is None:
                self.api_endpoints = DEFAULT_API_ENDPOINTS

            login_path = self.api_endpoints.get("login", "/auth/login")

            response, info = self._request("POST", login_path, data=login_data)

            # Check if info is None
            if info is None:
                self.module.fail_json(
                    msg="Failed to authenticate with MLM API: No response information returned"
                )

            # Check for successful authentication
            if info.get("status") != 200:
                self.module.fail_json(
                    msg="Failed to authenticate with MLM API: {}".format(
                        info.get("msg", "Unknown error")
                    ),
                    status_code=info.get("status", 0),
                )

            # Extract cookies from the response using a more streamlined approach
            for cookie_field in ["cookies_string", "cookies", "set-cookie"]:
                if cookie_field in info and info[cookie_field]:
                    self.session_cookies = info[cookie_field]
                    return self.session_cookies

            # If we get here, no cookies were found
            # Return an empty string as the session cookie
            self.session_cookies = ""
            return self.session_cookies

        except Exception as e:
            self.module.fail_json(msg="Error during authentication: {}".format(str(e)))

    def logout(self):
        """
        Log out from the MLM API and invalidate the session cookies.

        Returns:
            bool: True if logout was successful, False otherwise.
        """
        if not self.session_cookies:
            return True

        try:
            # Ensure api_endpoints is initialized and has the logout key
            if self.api_endpoints is None:
                self.api_endpoints = DEFAULT_API_ENDPOINTS

            logout_path = self.api_endpoints.get("logout", "/auth/logout")

            _, info = self._request("POST", logout_path)

            success = info["status"] == 200
            if success:
                self.session_cookies = None
            return success
        except Exception:
            return False

    def _apply_backoff(self, retry_count):
        """
        Apply exponential backoff with jitter.

        Args:
            retry_count: The current retry count.

        Returns:
            float: The delay in seconds.
        """
        # Use simple time-based jitter instead of random
        jitter = time.time() % 1.0  # Use fractional part of current time as jitter
        delay = min(MAX_BACKOFF_DELAY, 2**retry_count) + jitter
        time.sleep(delay)
        return delay

    def _request(self, method, path, data=None, headers=None, retries=None):
        """
        Make an HTTP request to the MLM API with retry logic.

        Args:
            method: The HTTP method (GET, POST, PUT, DELETE).
            path: The API endpoint path.
            data: Optional data to send with the request.
            headers: Optional headers to include with the request.
            retries: Number of retries (defaults to self.retries).

        Returns:
            tuple: (response, info) where response is the HTTP response and
                  info is a dict with status code and other metadata.

        Raises:
            AnsibleFailJson: If the request fails after all retries.
        """
        # Check if URL is None - this should never happen due to the check in __init__,
        # but we'll keep it as a safeguard
        if self.url is None:
            self.module.fail_json(
                msg="URL is not set. Please provide a valid URL via the 'url' parameter or MLM_URL environment variable."
            )

        # Ensure URL is a string
        if not isinstance(self.url, str):
            self.url = str(self.url)

        if retries is None:
            retries = self.retries

        if headers is None:
            headers = {}

        # Add session cookies to headers if available
        if self.session_cookies and "Cookie" not in headers:
            # Ensure api_endpoints is initialized
            if self.api_endpoints is None:
                self.api_endpoints = DEFAULT_API_ENDPOINTS

            login_path = self.api_endpoints.get("login", "/auth/login")

            if path != login_path:
                headers["Cookie"] = self.session_cookies

        # Prepare request URL and data
        url = self.url + path
        if data:
            data = json.dumps(data)
            headers["Content-Type"] = "application/json"

        # Initialize retry counter
        retry_count = 0

        while retry_count <= retries:
            try:
                # Use a try/except block to handle the validate_certs parameter
                try:
                    response, info = fetch_url(
                        self.module,
                        url,
                        data=data,
                        headers=headers,
                        method=method,
                        timeout=self.timeout,
                        validate_certs=self.validate_certs,
                    )
                except TypeError:
                    # If validate_certs is not supported, try without it
                    response, info = fetch_url(
                        self.module,
                        url,
                        data=data,
                        headers=headers,
                        method=method,
                        timeout=self.timeout,
                    )

                # Check if info is None
                if info is None:
                    if retry_count < retries:
                        retry_count += 1
                        self._apply_backoff(retry_count)
                        continue
                    else:
                        # Return empty response after max retries
                        return None, {
                            "status": 0,
                            "msg": "No response information returned",
                        }

                # Check for rate limiting (status code 429)
                if info.get("status") == 429 and retry_count < retries:
                    retry_count += 1
                    self._apply_backoff(retry_count)
                    continue

                # Check for server errors (5xx)
                if 500 <= info.get("status", 0) < 600 and retry_count < retries:
                    retry_count += 1
                    self._apply_backoff(retry_count)
                    continue

                # Return response for successful requests or after max retries
                return response, info

            except Exception as e:
                if retry_count < retries:
                    retry_count += 1
                    self._apply_backoff(retry_count)
                else:
                    error_msg = "Request failed after {} retries: {}".format(
                        retries, to_native(e)
                    )
                    self.module.fail_json(msg=error_msg)

        # This should not be reached, but just in case
        self.module.fail_json(
            msg="Request failed after {} retries with no response".format(retries)
        )

    def get(self, path, headers=None, params=None):
        """
        Make a GET request to the MLM API.

        Args:
            path: The API endpoint path.
            headers: Optional headers to include with the request.
            params: Optional query parameters to include in the URL.

        Returns:
            dict: The parsed JSON response.

        Raises:
            AnsibleFailJson: If the request fails or returns an error.
        """
        # Add query parameters to the path if provided
        if params:
            query_string = "&".join(["{}={}".format(k, v) for k, v in params.items()])
            if "?" in path:
                path = "{}{}".format(path, query_string)
            else:
                path = "{}?{}".format(path, query_string)

        response, info = self._request("GET", path, headers=headers)
        return self._handle_response(response, info, "GET", path)

    def post(self, path, data=None, headers=None):
        """
        Make a POST request to the MLM API.

        Args:
            path: The API endpoint path.
            data: Data to send with the request.
            headers: Optional headers to include with the request.

        Returns:
            dict: The parsed JSON response.

        Raises:
            AnsibleFailJson: If the request fails or returns an error.
        """
        response, info = self._request("POST", path, data=data, headers=headers)
        return self._handle_response(response, info, "POST", path, data)

    def put(self, path, data=None, headers=None):
        """
        Make a PUT request to the MLM API.

        Args:
            path: The API endpoint path.
            data: Data to send with the request.
            headers: Optional headers to include with the request.

        Returns:
            dict: The parsed JSON response.

        Raises:
            AnsibleFailJson: If the request fails or returns an error.
        """
        response, info = self._request("PUT", path, data=data, headers=headers)
        return self._handle_response(response, info, "PUT", path, data)

    def delete(self, path, headers=None):
        """
        Make a DELETE request to the MLM API.

        Args:
            path: The API endpoint path.
            headers: Optional headers to include with the request.

        Returns:
            dict: The parsed JSON response, or an empty dict if no content.

        Raises:
            AnsibleFailJson: If the request fails or returns an error.
        """
        response, info = self._request("DELETE", path, headers=headers)
        return self._handle_response(response, info, "DELETE", path)

    def _handle_response(self, response, info, method, path, data=None):
        """
        Handle the HTTP response and parse the JSON content.

        This helper method centralizes response handling logic for all HTTP methods.

        Args:
            response: The HTTP response object.
            info: Response info dictionary.
            method: The HTTP method used (for error messages).
            path: The API endpoint path.
            data: Optional data that was sent with the request.

        Returns:
            dict: The parsed JSON response.

        Raises:
            AnsibleFailJson: If the request fails or returns an error.
        """
        # Define expected success status codes for different methods
        success_codes = {
            "GET": [200],
            "POST": [200, 201, 202, 204],
            "PUT": [200, 201, 202, 204],
            "DELETE": [200, 202, 204],
        }

        # Check if status code indicates success
        if info["status"] not in success_codes.get(method, [200]):
            # Special handling for 400 errors on createProject endpoint
            if info["status"] == 400 and path == "/contentmanagement/createProject":
                # Try to get the response body for more details
                error_body = ""
                if response:
                    try:
                        error_body = to_text(response.read())
                    except Exception:
                        pass

                # Check if the project already exists
                if (
                    "already exists" in str(info.get("msg", "")).lower()
                    or "already exists" in error_body.lower()
                ):
                    # Return an empty dict to indicate success but no content
                    return {}

            # For updateProject 400 errors, provide more detailed error info
            if info["status"] == 400 and path == "/contentmanagement/updateProject":
                # Try to get the response body for more details
                error_body = ""
                if response:
                    try:
                        error_body = to_text(response.read())
                    except Exception:
                        pass

            # Standard error handling
            error_args = {
                "msg": "{} request failed: {}".format(
                    method, info.get("msg", "Unknown error")
                ),
                "status_code": info["status"],
                "path": path,
            }
            if data:
                error_args["data"] = data
            self.module.fail_json(**error_args)

        # Return empty dict for no content responses
        if not response or info["status"] == 204:
            return {}

        # Parse JSON response
        try:
            return json.loads(to_text(response.read()))
        except Exception as e:
            self.module.fail_json(
                msg="Failed to parse API response: {}".format(to_native(e)), path=path
            )

    def _get_field_value(self, data, field_path, default=None):
        """
        Extract a value from nested data using a field path.

        Args:
            data (dict): The data to extract from.
            field_path (str or list): The path to the field. If a list of strings, it will try each field in order.
                If a list of lists, it will try each nested path in order.
            default: The default value to return if the field is not found.

        Returns:
            The value at the specified path, or the default value if not found.
        """
        if not data:
            return default

        # Handle a single string field path
        if isinstance(field_path, str):
            return data.get(field_path, default)

        # Handle a list of alternative field paths
        if isinstance(field_path, list):
            # If the first element is a string, assume it's a list of alternative field names
            if len(field_path) > 0 and isinstance(field_path[0], str):
                # Check if this is a nested path (e.g., ['os', 'family']) or a list of alternatives
                # If all elements are strings and there's a nested path in the data, treat it as a nested path
                if (
                    all(isinstance(item, str) for item in field_path)
                    and field_path[0] in data
                    and isinstance(data[field_path[0]], dict)
                ):
                    # This is a nested path
                    value = data
                    for key in field_path:
                        if isinstance(value, dict) and key in value:
                            value = value[key]
                        else:
                            return default
                    return value
                else:
                    # This is a list of alternative field names
                    for field in field_path:
                        if field in data:
                            return data[field]
                    return default

            # If the first element is a list, assume it's a list of alternative nested paths
            elif len(field_path) > 0 and isinstance(field_path[0], list):
                for path in field_path:
                    value = self._get_field_value(data, path, None)
                    if value is not None:
                        return value
                return default

        # If we get here, the field path is not in a recognized format
        return default

    def get_paginated(
        self,
        path,
        headers=None,
        page_param="page",
        page_size_param="page_size",
        page_size=100,
    ):
        """
        Get all results from a paginated API endpoint.

        Args:
            path: The API endpoint path.
            headers: Optional headers to include with the request.
            page_param: The query parameter name for the page number.
            page_size_param: The query parameter name for the page size.
            page_size: The number of items per page.

        Returns:
            list: All items from all pages.

        Raises:
            AnsibleFailJson: If any request fails or returns an error.
        """
        all_items = []
        page = 1

        while True:
            # Add pagination parameters to the path
            paginated_path = path
            if "?" in path:
                paginated_path += "&{}={}&{}={}".format(
                    page_param, page, page_size_param, page_size
                )
            else:
                paginated_path += "?{}={}&{}={}".format(
                    page_param, page, page_size_param, page_size
                )

            # Make the request
            response = self.get(paginated_path, headers=headers)

            # Extract items from the response
            # Note: The actual structure may vary depending on the API
            items = response.get("items", [])
            if not items:
                items = response.get("results", [])
            if not items and isinstance(response, list):
                items = response

            # Add items to the result
            all_items.extend(items)

            # Check if there are more pages
            if len(items) < page_size:
                break

            page += 1

        return all_items

    # API methods for system management

    def get_systems(self) -> List[Dict[str, Any]]:
        """
        Get all systems (both active and inactive) from the MLM API.

        This method uses the systems endpoint to retrieve all systems
        registered with the MLM server, regardless of their active status.

        Returns:
            list: A list of dictionaries, each containing system information such as
                 id, name, hostname, IP address, OS details, and status.
        """
        try:
            # Ensure api_endpoints is initialized and has the systems key
            if self.api_endpoints is None:
                self.api_endpoints = DEFAULT_API_ENDPOINTS

            systems_path = self.api_endpoints.get("systems", "/system/listSystems")

            response = self.get(systems_path)
            # The API returns a structure with 'result' containing the systems
            if isinstance(response, dict) and "result" in response:
                systems = response["result"]
                return systems
            else:
                return []
        except Exception:
            raise

    def get_errata_counts_for_system(self, system_id):
        """
        Get the total number of errata (patches) available for a system.

        This method uses the relevant_errata endpoint to retrieve
        the total count of errata available for a specific system.

        Args:
            system_id (int): The unique identifier of the system to check.

        Returns:
            int: The total number of errata available for the system.
        """
        try:
            # Get relevant errata for the system using the correct query parameter format
            path = "{}?sid={}".format(self.api_endpoints["relevant_errata"], system_id)

            # Make the request directly to avoid 404 errors
            response, info = self._request("GET", path)

            # If the request failed, return 0
            if info["status"] != 200 or not response:
                return 0

            # Parse the response
            try:
                response_data = json.loads(to_text(response.read()))
            except Exception:
                return 0

            # The API returns a dict with 'success' and 'result' keys
            if isinstance(response_data, dict) and "result" in response_data:
                errata_list = response_data["result"]

                # If we got a list of errata, return the count
                if isinstance(errata_list, list):
                    return len(errata_list)

            # If the response is not in the expected format, return 0
            return 0
        except Exception:
            # Return 0 on error rather than failing
            return 0

    def get_registration_date_for_system(self, system_id):
        """
        Get the registration date for a system.

        This method uses the registration_date endpoint to retrieve
        the registration date for a specific system.

        Args:
            system_id (int): The unique identifier of the system to check.

        Returns:
            str: The registration date of the system, or None if not found.
        """
        try:
            path = "{}?sid={}".format(
                self.api_endpoints["registration_date"], system_id
            )
            response, info = self._request("GET", path)

            if info["status"] != 200 or not response:
                return None

            try:
                response_data = json.loads(to_text(response.read()))
                if isinstance(response_data, dict) and "result" in response_data:
                    return response_data["result"]
            except Exception:
                pass

            return None
        except Exception:
            return None

    def get_groups_for_system(self, system_id):
        """
        Get the groups a system belongs to.

        This method uses the system_groups endpoint to retrieve
        the list of groups for a specific system. It only includes
        groups where the system is subscribed (subscribed=1).

        Args:
            system_id (int): The unique identifier of the system to check.

        Returns:
            list: A list of group names the system belongs to, or an empty list if none found.
        """
        try:
            # Check if the system_groups endpoint is defined
            if "system_groups" not in self.api_endpoints:
                # Add it dynamically if not found
                self.api_endpoints["system_groups"] = "/system/listGroups"

            # Make the API request to get system groups
            path = "{}?sid={}".format(self.api_endpoints["system_groups"], system_id)
            response, info = self._request("GET", path)

            if info["status"] != 200 or not response:
                return []

            try:
                response_data = json.loads(to_text(response.read()))

                if isinstance(response_data, dict) and "result" in response_data:
                    groups_data = response_data["result"]

                    # Extract group names from the response
                    # The API returns a list of group objects with a 'system_group_name' field
                    # and a 'subscribed' field indicating if the system is a member of the group
                    if isinstance(groups_data, list):
                        group_names = []
                        for group in groups_data:
                            if isinstance(group, dict):
                                # Only include groups where subscribed is 1 (system is a member)
                                if (
                                    group.get("subscribed") == 1
                                    and "system_group_name" in group
                                ):
                                    # Remove the "system_group_" prefix if present
                                    group_name = group["system_group_name"]
                                    if group_name.startswith("system_group_"):
                                        group_name = group_name[
                                            13:
                                        ]  # Remove the prefix
                                    group_names.append(group_name)
                                elif "name" in group:
                                    # Fallback to 'name' field if present
                                    group_names.append(group["name"])
                            elif isinstance(group, str):
                                # Handle case where API returns group names directly as strings
                                group_names.append(group)
                        return group_names
                    elif isinstance(groups_data, str):
                        # Handle case where API returns a single group name as a string
                        return [groups_data]
            except Exception:
                pass

            return []
        except Exception:
            # Return empty list on error rather than failing
            return []

    def get_systems_requiring_reboot(self):
        """
        Get systems that require reboot after patching.

        This method uses the systems_reboot endpoint to retrieve
        systems that require a reboot after installing patches.

        Returns:
            list: A list of system IDs that require reboot, or an empty list if none found.
        """
        try:
            # Ensure api_endpoints is initialized and has the systems_reboot key
            if self.api_endpoints is None:
                self.api_endpoints = DEFAULT_API_ENDPOINTS

            reboot_path = self.api_endpoints.get(
                "systems_reboot", "/system/listSuggestedReboot"
            )

            response = self.get(reboot_path)

            # The API returns a structure with 'result' containing the systems
            if isinstance(response, dict) and "result" in response:
                systems_reboot = response["result"]
                if isinstance(systems_reboot, list):
                    # Extract system IDs from the response
                    return [
                        system.get("id")
                        for system in systems_reboot
                        if system.get("id")
                    ]
                return []
            elif isinstance(response, list):
                # Handle case where API returns systems directly as a list
                return [system.get("id") for system in response if system.get("id")]
            else:
                return []
        except Exception:
            # Return empty list on error rather than failing
            return []

    def get_systems_with_patch_status(self):
        """
        Get all systems with their patch status determined by errata counts and reboot requirements.

        This method retrieves all systems and then checks the errata counts for each
        system to determine if it needs patches. It also checks if systems require reboot.
        A system is considered to need patches if it has any errata (patches) available.
        A system is considered to need reboot if it appears in the suggested reboot list.
        It also retrieves the groups each system belongs to.

        Returns:
            list: A list of dictionaries, each containing system information with
                 patch status, groups, and other standardized fields.
        """
        systems = self.get_systems()

        # Get list of systems that require reboot
        reboot_required_ids = self.get_systems_requiring_reboot()

        # Process each system to add patch status and standardize fields
        for system in systems:
            # Set patch status based on errata count and reboot requirement
            if "id" in system:
                system_id = system["id"]

                # Get errata count
                errata_count = self.get_errata_counts_for_system(system_id)
                system["errata_count"] = errata_count

                # Determine patch status with reboot priority
                if system_id in reboot_required_ids:
                    system["patch_status"] = "needs_reboot"
                elif errata_count > 0:
                    system["patch_status"] = "needs_patches"
                else:
                    system["patch_status"] = "up_to_date"

                # Get registration date
                registration_date = self.get_registration_date_for_system(system_id)
                if registration_date:
                    system["registration_date"] = registration_date

                # Get system groups
                groups = self.get_groups_for_system(system_id)
                system["groups"] = groups
            else:
                system["errata_count"] = 0
                system["patch_status"] = "up_to_date"
                system["groups"] = []

            # Remove legacy field if it exists
            system.pop("errata_counts", None)

            # Standardize system fields using field mappings
            self._standardize_system_fields(system)

        return systems

    def _standardize_system_fields(self, system):
        """
        Standardize system fields using the configured field mappings.

        This helper method ensures all systems have consistent field names
        by applying the field mappings and setting default values where needed.

        Args:
            system (dict): The system dictionary to standardize.
        """
        # Ensure field_mappings is not None and has a system key
        if self.field_mappings is None:
            self.field_mappings = DEFAULT_FIELD_MAPPINGS

        if "system" not in self.field_mappings:
            return

        # Apply field mappings to ensure consistent field names
        for key, field_path in self.field_mappings["system"].items():
            if key not in system:
                value = self._get_field_value(system, field_path)
                if value is not None:
                    system[key] = value


def mlm_argument_spec():
    """
    Return a dict containing common MLM client parameters for Ansible modules.

    This function provides a standardized set of parameters that should be used
    by all Ansible modules that interact with the SUSE Multi-Linux Manager API.
    Using this function ensures consistent parameter naming and behavior across
    the collection.

    Returns:
        dict: A dictionary of parameter specifications that can be included in
              an AnsibleModule's argument_spec. Contains parameters for URL,
              authentication credentials, SSL verification, and request timeouts.
    """
    return dict(
        url=dict(type="str", required=False),
        username=dict(type="str", required=False),
        password=dict(type="str", required=False, no_log=True),
        instance=dict(type="str", required=False),
        validate_certs=dict(type="bool", default=True),
        timeout=dict(type="int", default=60),
        retries=dict(type="int", default=3),
        api_base_path=dict(type="str", required=False),
        api_endpoints=dict(type="dict", required=False),
        field_mappings=dict(type="dict", required=False),
    )
