#!/usr/bin/python
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
Common utilities and patterns for SUSE Multi-Linux Manager Ansible modules.

This module provides standardized patterns, utilities, and base classes to
eliminate code duplication and ensure consistency across all MLM modules.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    format_error_message,
    format_success_message,
)


class MLMModuleBase:
    """
    Base class for SUSE Multi-Linux Manager Ansible modules.

    This class provides common functionality and standardizes the module execution
    pattern to reduce code duplication across all MLM modules.
    """

    def __init__(self, module: Any, entity_type: str = "resource") -> None:
        """
        Initialize the MLM module base.

        Args:
            module: The AnsibleModule instance.
            entity_type: The type of entity this module manages (e.g., "activation key", "organization").
        """
        self.module = module
        self.entity_type = entity_type
        self.client: Optional[MLMClient] = None
        self.changed = False
        self.result: Optional[Dict[str, Any]] = None
        self.msg = ""

    def run(self, operation_func: Callable[[Any, MLMClient], Tuple[bool, Optional[Dict[str, Any]], str]]) -> None:
        """
        Execute the module operation with standardized error handling and client management.

        Args:
            operation_func: Function that performs the actual operation.
                           Should accept (module, client) and return (changed, result, msg).
        """
        try:
            # Create and login to MLM client
            self.client = MLMClient(self.module)
            self.client.login()

            # Execute the operation
            self.changed, self.result, self.msg = operation_func(self.module, self.client)

            # Return results
            if self.result:
                self.module.exit_json(
                    changed=self.changed,
                    msg=self.msg,
                    **{self._get_result_key(): self.result}
                )
            else:
                self.module.exit_json(changed=self.changed, msg=self.msg)

        except Exception as e:
            error_msg = format_error_message(
                "manage {}".format(self.entity_type),
                str(e),
                context=self.module.params.get("state", "unknown")
            )
            self.module.fail_json(msg=error_msg)
        finally:
            # Ensure logout even on errors
            if self.client:
                self.client.logout()

    def _get_result_key(self) -> str:
        """
        Get the key name for the result in the module output.

        Returns:
            str: The key name based on entity type.
        """
        # Convert entity type to snake_case key
        return self.entity_type.lower().replace(" ", "_").replace("-", "_")


class MLMAPIError(Exception):
    """Custom exception for MLM API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


def standardize_api_response(
    response: Union[Dict[str, Any], List[Any], Any],
    operation_name: str,
    expected_type: str = "dict"
) -> Union[Dict[str, Any], List[Any]]:
    """
    Standardize API response handling across all modules.

    Args:
        response: The raw API response.
        operation_name: Name of the operation for error messages.
        expected_type: Expected response type ("dict", "list", or "any").

    Returns:
        The standardized response.

    Raises:
        MLMAPIError: If the response is invalid or indicates an error.
    """
    if response is None:
        raise MLMAPIError("No response received for {}".format(operation_name))

    # Handle wrapped responses with "result" key
    if isinstance(response, dict) and "result" in response:
        actual_response = response["result"]

        # Check for API errors even in wrapped responses
        if response.get("success") is False:
            error_msg = response.get("message", "Unknown API error")
            raise MLMAPIError("{} failed: {}".format(operation_name, error_msg), response=response)

        response = actual_response

    # Handle error responses
    if isinstance(response, dict):
        if response.get("error"):
            raise MLMAPIError("{} failed: {}".format(operation_name, response['error']), response=response)

        if response.get("success") is False:
            error_msg = response.get("message", "Unknown API error")
            raise MLMAPIError("{} failed: {}".format(operation_name, error_msg), response=response)

    # Validate expected type
    if expected_type == "dict" and not isinstance(response, dict):
        if response is None or (isinstance(response, list) and len(response) == 0):
            return {}
        raise MLMAPIError("{} returned unexpected type: expected dict, got {}".format(operation_name, type(response).__name__))

    if expected_type == "list" and not isinstance(response, list):
        if response is None:
            return []
        if isinstance(response, dict):
            # Sometimes APIs return a single item as dict instead of list
            return [response]
        raise MLMAPIError("{} returned unexpected type: expected list, got {}".format(operation_name, type(response).__name__))

    return response


def handle_module_errors(func: Callable) -> Callable:
    """
    Decorator to standardize error handling in module functions.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function with standardized error handling.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MLMAPIError as e:
            # MLM API specific errors
            if hasattr(args[0], 'fail_json'):  # module is first argument
                args[0].fail_json(
                    msg=str(e),
                    status_code=getattr(e, 'status_code', None),
                    api_response=getattr(e, 'response', None)
                )
            else:
                raise
        except Exception as e:
            # General errors
            if hasattr(args[0], 'fail_json'):  # module is first argument
                operation_name = getattr(func, '__name__', 'operation')
                error_msg = format_error_message(operation_name, str(e))
                args[0].fail_json(msg=error_msg)
            else:
                raise
    return wrapper


def validate_required_params(module: Any, required_params: List[str], state: Optional[str] = None) -> None:
    """
    Validate that required parameters are present for the current operation.

    Args:
        module: The AnsibleModule instance.
        required_params: List of parameter names that are required.
        state: Optional state to include in error message context.

    Raises:
        AnsibleFailJson: If any required parameters are missing.
    """
    missing_params = []

    for param in required_params:
        if not module.params.get(param):
            missing_params.append(param)

    if missing_params:
        context = "state={}".format(state) if state else "current operation"
        error_msg = format_error_message(
            "parameter validation",
            "Missing required parameters: {}".format(', '.join(missing_params)),
            context=context
        )
        module.fail_json(msg=error_msg, missing_parameters=missing_params)


def format_module_result(
    changed: bool,
    entity_data: Optional[Dict[str, Any]],
    operation: str,
    entity_name: str,
    entity_type: str = "resource"
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Format module results in a standardized way.

    Args:
        changed: Whether the operation made changes.
        entity_data: The entity data to return.
        operation: The operation that was performed ("created", "updated", "deleted", etc.).
        entity_name: The name/identifier of the entity.
        entity_type: The type of entity.

    Returns:
        Tuple of (changed, result, msg).
    """
    if changed and operation in ["created", "updated"]:
        msg = format_success_message(operation, "'{} successfully".format(entity_name), entity_type)
    elif changed and operation == "deleted":
        msg = format_success_message("deleted", "'{} successfully".format(entity_name), entity_type)
    elif not changed and operation == "exists":
        msg = "{} '{}' already exists with specified configuration".format(entity_type.title(), entity_name)
    elif not changed and operation == "not_found":
        msg = "{} '{}' does not exist".format(entity_type.title(), entity_name)
    else:
        msg = "{} '{}' {}".format(entity_type.title(), entity_name, operation)

    return changed, entity_data, msg


def extract_entity_identifier(module: Any, id_param: str, name_param: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Extract entity identifier from module parameters.

    Args:
        module: The AnsibleModule instance.
        id_param: Name of the ID parameter.
        name_param: Name of the name parameter.

    Returns:
        Tuple of (id, name) values.
    """
    entity_id = module.params.get(id_param)
    entity_name = module.params.get(name_param)

    # Convert ID to int if provided as string
    if entity_id is not None:
        try:
            entity_id = int(entity_id)
        except (ValueError, TypeError):
            error_msg = format_error_message(
                "parameter validation",
                "Invalid {}: must be a valid integer".format(id_param)
            )
            module.fail_json(msg=error_msg, invalid_parameter=id_param)

    return entity_id, entity_name


def ensure_list_param(module: Any, param_name: str) -> List[Any]:
    """
    Ensure a parameter is returned as a list.

    Args:
        module: The AnsibleModule instance.
        param_name: Name of the parameter.

    Returns:
        List value of the parameter, or empty list if None.
    """
    value = module.params.get(param_name)
    if value is None:
        return []
    if not isinstance(value, list):
        return [value]
    return value


def check_mode_exit(module: Any, changed: bool, operation: str, entity_name: str, entity_type: str = "resource") -> None:
    """
    Exit with appropriate message if in check mode.

    Args:
        module: The AnsibleModule instance.
        changed: Whether the operation would make changes.
        operation: The operation that would be performed.
        entity_name: The name/identifier of the entity.
        entity_type: The type of entity.
    """
    if module.check_mode:
        if changed:
            msg = "{} '{}' would be {}".format(entity_type.title(), entity_name, operation)
        else:
            msg = "No changes needed for {} '{}'".format(entity_type, entity_name)

        module.exit_json(changed=changed, msg=msg)
