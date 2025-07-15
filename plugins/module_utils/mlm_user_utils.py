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
This module provides utility functions for working with users in SUSE Multi-Linux Manager.

It contains common functions used by the user and user_info modules to avoid code duplication.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Dict, List, Optional, Any, Tuple
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    check_api_response,
    format_error_message,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_api_utils import (
    get_entity_by_field,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_common import (
    standardize_api_response,
    validate_required_params,
    format_module_result,
    check_mode_exit,
    MLMAPIError,
    handle_module_errors,
)


def standardize_user_data(user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Standardize the user data format.

    Args:
        user_data: The raw user data from the API.

    Returns:
        dict: The standardized user data.
    """
    if not user_data:
        return {}

    return {
        "id": user_data.get("id"),
        "login": user_data.get("login"),
        "login_uc": user_data.get("login_uc"),
        "enabled": user_data.get("enabled", True),
        "first_name": user_data.get("first_name", ""),
        "last_name": user_data.get("last_name", ""),
        "email": user_data.get("email", ""),
        "prefix": user_data.get("prefix", ""),
        "last_login_date": user_data.get("last_login_date", ""),
        "created_date": user_data.get("created_date", ""),
        "role_labels": user_data.get("role_labels", []),
        "roles": user_data.get("roles", []),
        "use_pam_authentication": user_data.get("use_pam_authentication", False),
        "read_only": user_data.get("read_only", False),
        "errata_notifications": user_data.get("errata_notifications", False),
    }


def list_users(client: Any) -> List[Dict[str, Any]]:
    """
    List all users.

    Args:
        client: The MLM client.

    Returns:
        list: A list of standardized user data.

    Raises:
        Exception: If there's an error retrieving users from the API.
    """
    try:
        path = "/user/listUsers"
        users = client.get(path)
        if not users:
            return []

        if isinstance(users, dict) and "result" in users:
            users = users["result"]

        if not isinstance(users, list):
            return []

        return [standardize_user_data(user) for user in users if isinstance(user, dict)]
    except Exception as e:
        raise Exception("Failed to list users: {}".format(str(e)))


def get_user_by_login(client: Any, login: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by login name.

    Args:
        client: The MLM client.
        login: The login name of the user to retrieve.

    Returns:
        dict: The user data, or None if not found.

    Raises:
        Exception: If there's an error retrieving the user from the API.
    """
    try:
        return get_entity_by_field(client, "/user/listUsers", "login", login)
    except Exception as e:
        raise Exception("Failed to get user by login: {}".format(str(e)))


def get_user_details(client: Any, login: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific user.

    Args:
        client: The MLM client.
        login: The login name of the user to get details for.

    Returns:
        dict: The standardized user details, or None if not found.

    Raises:
        Exception: If there's an error retrieving user details from the API.
    """
    try:
        path = "/user/getDetails"
        user_details = client.get(path, params={"login": login})

        if not user_details:
            return None

        if isinstance(user_details, dict) and "result" in user_details:
            user_details = user_details["result"]

        return standardize_user_data(user_details)
    except Exception as e:
        raise Exception("Failed to get user details: {}".format(str(e)))


def list_user_roles(client: Any, login: str) -> List[str]:
    """
    List roles assigned to a user.

    Args:
        client: The MLM client.
        login: The login name of the user.

    Returns:
        list: A list of role labels.

    Raises:
        Exception: If there's an error retrieving user roles from the API.
    """
    try:
        path = "/user/listRoles"
        roles = client.get(path, params={"login": login})

        if not roles:
            return []

        if isinstance(roles, dict) and "result" in roles:
            roles = roles["result"]

        if not isinstance(roles, list):
            return []

        return roles
    except Exception as e:
        raise Exception("Failed to list user roles: {}".format(str(e)))


def list_assignable_roles(client: Any) -> List[str]:
    """
    List roles that can be assigned to users.

    Args:
        client: The MLM client.

    Returns:
        list: A list of assignable role labels.

    Raises:
        Exception: If there's an error retrieving assignable roles from the API.
    """
    try:
        path = "/user/listAssignableRoles"
        roles = client.get(path)

        if not roles:
            return []

        if isinstance(roles, dict) and "result" in roles:
            roles = roles["result"]

        if not isinstance(roles, list):
            return []

        return roles
    except Exception as e:
        raise Exception("Failed to list assignable roles: {}".format(str(e)))


def list_user_assigned_system_groups(client: Any, login: str) -> List[Dict[str, Any]]:
    """
    List system groups assigned to a user.

    Args:
        client: The MLM client.
        login: The login name of the user.

    Returns:
        list: A list of system group data.

    Raises:
        Exception: If there's an error retrieving assigned system groups from the API.
    """
    try:
        path = "/user/listAssignedSystemGroups"
        groups = client.get(path, params={"login": login})

        if not groups:
            return []

        if isinstance(groups, dict) and "result" in groups:
            groups = groups["result"]

        if not isinstance(groups, list):
            return []

        return groups
    except Exception as e:
        raise Exception("Failed to list assigned system groups: {}".format(str(e)))


def list_user_default_system_groups(client: Any, login: str) -> List[Dict[str, Any]]:
    """
    List default system groups for a user.

    Args:
        client: The MLM client.
        login: The login name of the user.

    Returns:
        list: A list of system group data.

    Raises:
        Exception: If there's an error retrieving default system groups from the API.
    """
    try:
        path = "/user/listDefaultSystemGroups"
        groups = client.get(path, params={"login": login})

        if not groups:
            return []

        if isinstance(groups, dict) and "result" in groups:
            groups = groups["result"]

        if not isinstance(groups, list):
            return []

        return groups
    except Exception as e:
        raise Exception("Failed to list default system groups: {}".format(str(e)))


@handle_module_errors
def create_user(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Create a new user.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)

    Raises:
        MLMAPIError: If the API request fails.
    """
    # Validate required parameters
    required_params = ["login", "password", "first_name", "last_name", "email"]
    validate_required_params(module, required_params, "present")

    # Extract module parameters
    login = module.params["login"]
    password = module.params["password"]
    first_name = module.params["first_name"]
    last_name = module.params["last_name"]
    email = module.params["email"]
    prefix = module.params.get("prefix", "")
    use_pam_auth = module.params.get("use_pam_auth", False)

    # Check if user already exists
    try:
        existing_user = get_user_by_login(client, login)
        if existing_user:
            return format_module_result(False, standardize_user_data(existing_user), "exists", login, "user")
    except Exception as e:
        raise MLMAPIError(
            format_error_message("check existing user", str(e)),
            response={"login": login}
        )

    # Handle check mode
    check_mode_exit(module, True, "created", login, "user")

    # Prepare the request data
    create_data = {
        "login": login,
        "password": password,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "usePamAuth": 1 if use_pam_auth else 0,
    }

    # Make the API request with standardized response handling
    try:
        create_path = "/user/create"
        result = client.post(create_path, data=create_data)

        # User creation API returns int (1 on success), not dict
        standardized_result = standardize_api_response(result, "create user", expected_type="any")

        # Check if result is 1 (success)
        if standardized_result == 1:
            # Get the created user for return
            created_user = get_user_by_login(client, login)
            if created_user:
                return format_module_result(True, standardize_user_data(created_user), "created", login, "user")
            else:
                return format_module_result(True, None, "created", login, "user")
        else:
            raise MLMAPIError(
                format_error_message("create user", "API returned unexpected result: {}".format(standardized_result)),
                response={"create_data": create_data, "api_result": standardized_result}
            )

    except Exception as e:
        raise MLMAPIError(
            format_error_message("create user", str(e), context="login={}".format(login)),
            response={"create_data": create_data}
        )


@handle_module_errors
def delete_user(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Delete a user.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)

    Raises:
        MLMAPIError: If the API request fails.
    """
    # Extract module parameters
    login = module.params["login"]

    # Check if user exists
    try:
        existing_user = get_user_by_login(client, login)
        if not existing_user:
            return format_module_result(False, None, "not_found", login, "user")
    except Exception as e:
        raise MLMAPIError(
            format_error_message("check existing user", str(e)),
            response={"login": login}
        )

    # Handle check mode
    check_mode_exit(module, True, "deleted", login, "user")

    # Make the API request
    try:
        delete_path = "/user/delete"
        result = client.post(delete_path, data={"login": login})
        check_api_response(result, "Delete user", module)

        return format_module_result(True, None, "deleted", login, "user")

    except Exception as e:
        raise MLMAPIError(
            format_error_message("delete user", str(e), context="login={}".format(login)),
            response={"login": login}
        )


@handle_module_errors
def enable_user(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Enable a user.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)

    Raises:
        MLMAPIError: If the API request fails.
    """
    # Extract module parameters
    login = module.params["login"]

    # Check if user exists
    try:
        existing_user = get_user_by_login(client, login)
        if not existing_user:
            return format_module_result(False, None, "not_found", login, "user")
    except Exception as e:
        raise MLMAPIError(
            format_error_message("check existing user", str(e)),
            response={"login": login}
        )

    # Check if user is already enabled
    if existing_user.get("enabled", True):
        return format_module_result(False, standardize_user_data(existing_user), "exists", login, "user")

    # Handle check mode
    check_mode_exit(module, True, "enabled", login, "user")

    # Make the API request
    try:
        enable_path = "/user/enable"
        result = client.post(enable_path, data={"login": login})
        check_api_response(result, "Enable user", module)

        # Get the updated user
        updated_user = get_user_by_login(client, login)
        if updated_user:
            return format_module_result(True, standardize_user_data(updated_user), "enabled", login, "user")
        else:
            return format_module_result(True, None, "enabled", login, "user")

    except Exception as e:
        raise MLMAPIError(
            format_error_message("enable user", str(e), context="login={}".format(login)),
            response={"login": login}
        )


@handle_module_errors
def disable_user(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Disable a user.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)

    Raises:
        MLMAPIError: If the API request fails.
    """
    # Extract module parameters
    login = module.params["login"]

    # Check if user exists
    try:
        existing_user = get_user_by_login(client, login)
        if not existing_user:
            return format_module_result(False, None, "not_found", login, "user")
    except Exception as e:
        raise MLMAPIError(
            format_error_message("check existing user", str(e)),
            response={"login": login}
        )

    # Check if user is already disabled
    if not existing_user.get("enabled", True):
        return format_module_result(False, standardize_user_data(existing_user), "exists", login, "user")

    # Handle check mode
    check_mode_exit(module, True, "disabled", login, "user")

    # Make the API request
    try:
        disable_path = "/user/disable"
        result = client.post(disable_path, data={"login": login})
        check_api_response(result, "Disable user", module)

        # Get the updated user
        updated_user = get_user_by_login(client, login)
        if updated_user:
            return format_module_result(True, standardize_user_data(updated_user), "disabled", login, "user")
        else:
            return format_module_result(True, None, "disabled", login, "user")

    except Exception as e:
        raise MLMAPIError(
            format_error_message("disable user", str(e), context="login={}".format(login)),
            response={"login": login}
        )


@handle_module_errors
def update_user_details(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Update user details.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)

    Raises:
        MLMAPIError: If the API request fails.
    """
    # Extract module parameters
    login = module.params["login"]

    # Check if user exists
    try:
        existing_user = get_user_by_login(client, login)
        if not existing_user:
            return format_module_result(False, None, "not_found", login, "user")
    except Exception as e:
        raise MLMAPIError(
            format_error_message("check existing user", str(e)),
            response={"login": login}
        )

    # Build update data from module parameters
    update_data = {}
    changed = False

    # Check each field for updates
    # Note: setDetails API may not support all fields that create API supports

    # Only update fields that are supported by setDetails API
    if module.params.get("email"):
        if existing_user.get("email") != module.params["email"]:
            update_data["email"] = module.params["email"]
            changed = True

    if module.params.get("prefix"):
        if existing_user.get("prefix") != module.params["prefix"]:
            update_data["prefix"] = module.params["prefix"]
            changed = True

    if module.params.get("password"):
        # Password is always updated if provided
        update_data["password"] = module.params["password"]
        changed = True

    if not changed:
        return format_module_result(False, standardize_user_data(existing_user), "exists", login, "user")

    # Handle check mode
    check_mode_exit(module, True, "updated", login, "user")

    # Make the API request
    try:
        update_path = "/user/setDetails"
        # Structure data according to setDetails API specification (similar to activation key)
        data = {"login": login, "details": update_data}

        result = client.post(update_path, data=data)
        check_api_response(result, "Update user details", module)

        # Get the updated user
        updated_user = get_user_by_login(client, login)
        if updated_user:
            return format_module_result(True, standardize_user_data(updated_user), "updated", login, "user")
        else:
            return format_module_result(True, None, "updated", login, "user")

    except Exception as e:
        raise MLMAPIError(
            format_error_message("update user details", str(e), context="login={}".format(login)),
            response={"login": login, "update_data": update_data}
        )


@handle_module_errors
def add_user_role(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Add a role to a user.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)

    Raises:
        MLMAPIError: If the API request fails.
    """
    # Extract module parameters
    login = module.params["login"]
    role = module.params["role"]

    # Check if user exists
    try:
        existing_user = get_user_by_login(client, login)
        if not existing_user:
            return format_module_result(False, None, "not_found", login, "user")
    except Exception as e:
        raise MLMAPIError(
            format_error_message("check existing user", str(e)),
            response={"login": login}
        )

    # Check if user already has the role
    try:
        user_roles = list_user_roles(client, login)
        if role in user_roles:
            return format_module_result(False, standardize_user_data(existing_user), "exists", "{} role {}".format(login, role), "user")
    except Exception as e:
        raise MLMAPIError(
            format_error_message("check user roles", str(e)),
            response={"login": login, "role": role}
        )

    # Handle check mode
    check_mode_exit(module, True, "role {} added".format(role), login, "user")

    # Make the API request
    try:
        add_role_path = "/user/addRole"
        result = client.post(add_role_path, data={"login": login, "role": role})
        check_api_response(result, "Add user role", module)

        # Get the updated user
        updated_user = get_user_by_login(client, login)
        if updated_user:
            return format_module_result(True, standardize_user_data(updated_user), "role {} added".format(role), login, "user")
        else:
            return format_module_result(True, None, "role {} added".format(role), login, "user")

    except Exception as e:
        raise MLMAPIError(
            format_error_message("add user role", str(e), context="login={}, role={}".format(login, role)),
            response={"login": login, "role": role}
        )


@handle_module_errors
def remove_user_role(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Remove a role from a user.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)

    Raises:
        MLMAPIError: If the API request fails.
    """
    # Extract module parameters
    login = module.params["login"]
    role = module.params["role"]

    # Check if user exists
    try:
        existing_user = get_user_by_login(client, login)
        if not existing_user:
            return format_module_result(False, None, "not_found", login, "user")
    except Exception as e:
        raise MLMAPIError(
            format_error_message("check existing user", str(e)),
            response={"login": login}
        )

    # Check if user has the role
    try:
        user_roles = list_user_roles(client, login)
        if role not in user_roles:
            return format_module_result(False, standardize_user_data(existing_user), "not_found", "{} role {}".format(login, role), "user")
    except Exception as e:
        raise MLMAPIError(
            format_error_message("check user roles", str(e)),
            response={"login": login, "role": role}
        )

    # Handle check mode
    check_mode_exit(module, True, "role {} removed".format(role), login, "user")

    # Make the API request
    try:
        remove_role_path = "/user/removeRole"
        result = client.post(remove_role_path, data={"login": login, "role": role})
        check_api_response(result, "Remove user role", module)

        # Get the updated user
        updated_user = get_user_by_login(client, login)
        if updated_user:
            return format_module_result(True, standardize_user_data(updated_user), "role {} removed".format(role), login, "user")
        else:
            return format_module_result(True, None, "role {} removed".format(role), login, "user")

    except Exception as e:
        raise MLMAPIError(
            format_error_message("remove user role", str(e), context="login={}, role={}".format(login, role)),
            response={"login": login, "role": role}
        )
