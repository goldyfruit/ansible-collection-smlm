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
This module provides utility functions for working with custom system information in SUSE Multi-Linux Manager.

It contains common functions used by the custominfo and custominfo_info modules to avoid code duplication.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Dict, List, Optional, Any, Union, Tuple
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    format_error_message,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_common import (
    standardize_api_response,
    validate_required_params,
    format_module_result,
    check_mode_exit,
    MLMAPIError,
    handle_module_errors,
)


def create_custom_key(client: Any, label: str, description: str) -> int:
    """
    Create a custom information key.

    Args:
        client: The MLM client.
        label: The label of the custom key.
        description: The description of the custom key.

    Returns:
        int: 1 on success.
    """
    # Make the API request
    path = "/system/custominfo/createKey"
    data = {"keyLabel": label, "keyDescription": description}
    result = client.post(path, data)
    return result


def delete_custom_key(client: Any, key_label: str) -> int:
    """
    Delete a custom information key.

    Args:
        client: The MLM client.
        key_label: The label of the custom key to delete.

    Returns:
        int: 1 on success.
    """
    # Make the API request
    path = "/system/custominfo/deleteKey"
    data = {"keyLabel": key_label}
    result = client.post(path, data)
    return result


def update_custom_key(
    client: Any, old_label: str, new_label: str, new_description: str
) -> int:
    """
    Update a custom information key.

    Args:
        client: The MLM client.
        old_label: The current label of the custom key.
        new_label: The new label for the custom key.
        new_description: The new description for the custom key.

    Returns:
        int: 1 on success.
    """
    # If the label is changing, we need to preserve custom values
    if old_label != new_label:
        # Get all systems
        systems = client.get("/system/listSystems")

        # Store custom values for the old key
        custom_values = {}
        for system in systems:
            system_id = system.get("id")
            if system_id:
                # Get custom values for this system
                system_values = get_custom_values(client, system_id)

                # Check if this system has a value for the old key
                for key_value in system_values:
                    if (
                        isinstance(key_value, dict)
                        and key_value.get("keyLabel") == old_label
                    ):
                        if system_id not in custom_values:
                            custom_values[system_id] = key_value.get("value", "")

        # Delete the old key
        delete_result = delete_custom_key(client, old_label)

        # Create a new key with the new label and description
        create_result = create_custom_key(client, new_label, new_description)

        # Restore custom values with the new key
        for system_id, value in custom_values.items():
            set_custom_value(client, system_id, new_label, value)

        return create_result
    else:
        # Just update the description
        # According to the API documentation, the correct endpoint is updateKey
        # with parameters keyLabel and keyDescription
        path = "/system/custominfo/updateKey"
        data = {"keyLabel": old_label, "keyDescription": new_description}
        result = client.post(path, data)
        return result


def list_all_keys(client: Any) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    List all custom information keys.

    Args:
        client: The MLM client.

    Returns:
        list or dict: A list of custom information keys as dictionaries,
                     or a dictionary with a "result" key containing the list.
    """
    # Make the API request
    path = "/system/custominfo/listAllKeys"
    result = client.get(path)

    # Handle the case where the API returns a dictionary with a "result" key
    # We'll return the raw result to let the caller handle it appropriately
    if result and isinstance(result, dict) and "result" in result:
        return result

    # Convert string results to dictionaries if needed
    if result and isinstance(result, list):
        processed_result = []
        for item in result:
            if isinstance(item, str):
                processed_result.append({"label": item})
            else:
                processed_result.append(item)
        return processed_result

    return result or []


def set_custom_value(client: Any, system_id: int, key_label: str, value: str) -> int:
    """
    Set a custom value for a system.

    Args:
        client: The MLM client.
        system_id: The ID of the system.
        key_label: The label of the custom key.
        value: The value to set.

    Returns:
        int: 1 on success.
    """
    # Make the API request
    # Based on the SUSE Multi-Linux Manager API documentation
    path = "/system/setCustomValues"
    data = {"sid": system_id, "values": {key_label: value}}
    result = client.post(path, data)
    return result


def get_custom_values(client: Any, system_id: int) -> List[Dict[str, Any]]:
    """
    Get all custom values for a system.

    Args:
        client: The MLM client.
        system_id: The ID of the system.

    Returns:
        list: A list of custom values for the system.
    """
    # Make the API request
    # Based on the SUSE Multi-Linux Manager API documentation
    path = "/system/getCustomValues?sid={}".format(system_id)
    result = client.get(path)

    # Handle the case where the API returns a dictionary with a "result" key
    if result and isinstance(result, dict) and "result" in result:
        return result["result"]

    return result or []


def standardize_custom_key(
    key_data: Union[Dict[str, Any], str, None],
) -> Dict[str, Any]:
    """
    Standardize the custom key data format.

    Args:
        key_data (dict or str): The raw key data from the API.

    Returns:
        dict: The standardized key data.
    """
    if not key_data:
        return {}

    # Handle string input
    if isinstance(key_data, str):
        return {
            "label": key_data,
            "description": "",
            "created": "",
            "modified": "",
            "creator": "",
            "modifier": "",
        }

    # Extract key information
    standardized_key = {
        "label": key_data.get("label", ""),
        "description": key_data.get("description", ""),
        "created": key_data.get("created", ""),
        "modified": key_data.get("modified", ""),
        "creator": key_data.get("creator", ""),
        "modifier": key_data.get("modifier", ""),
    }

    return standardized_key


def standardize_custom_value(
    value_data: Union[Dict[str, Any], str, None],
) -> Dict[str, Any]:
    """
    Standardize the custom value data format.

    Args:
        value_data (dict or str): The raw value data from the API.

    Returns:
        dict: The standardized value data.
    """
    if not value_data:
        return {}

    # Handle string input
    if isinstance(value_data, str):
        return {
            "key_label": "",
            "value": value_data,
            "created": "",
            "modified": "",
            "creator": "",
            "modifier": "",
        }

    # Extract value information
    standardized_value = {
        "key_label": value_data.get("keyLabel", ""),
        "value": value_data.get("value", ""),
        "created": value_data.get("created", ""),
        "modified": value_data.get("modified", ""),
        "creator": value_data.get("creator", ""),
        "modifier": value_data.get("modifier", ""),
    }

    return standardized_value


def get_existing_key(client: Any, key_label: str) -> Optional[Dict[str, Any]]:
    """
    Check if a custom information key exists.

    Args:
        client: The MLM client.
        key_label: The label of the key to check.

    Returns:
        dict or None: The existing key data if found, None otherwise.
    """
    existing_keys = list_all_keys(client)

    # Handle the case where the API returns a dictionary with a "result" key
    if isinstance(existing_keys, dict) and "result" in existing_keys:
        keys_to_check = existing_keys["result"]
    else:
        keys_to_check = existing_keys

    for key in keys_to_check:
        # Handle both string and dictionary keys
        if isinstance(key, str) and key == key_label:
            return {"label": key}
        elif isinstance(key, dict) and key.get("label") == key_label:
            return key

    return None


def validate_system_exists(client: Any, system_id: int) -> bool:
    """
    Validate that a system exists.

    Args:
        client: The MLM client.
        system_id: The ID of the system to validate.

    Returns:
        bool: True if the system exists, False otherwise.
    """
    try:
        # Get all systems
        systems = client.get_systems()

        # Check if the system exists
        for system in systems:
            if system.get("id") == system_id:
                return True
        return False
    except Exception:
        return False


def get_current_custom_value(
    client: Any, system_id: int, key_label: str
) -> Optional[str]:
    """
    Get the current value of a custom key for a system.

    Args:
        client: The MLM client.
        system_id: The ID of the system.
        key_label: The label of the custom key.

    Returns:
        str or None: The current value if found, None otherwise.
    """
    try:
        # Get the current value
        path = "/system/getCustomValues?sid={}".format(system_id)
        response = client.get(path)

        # Handle case where response is None or not a list/dict
        if response:
            if isinstance(response, list):
                for item in response:
                    if isinstance(item, dict) and item.get("key") == key_label:
                        return item.get("value")
            elif isinstance(response, dict):
                # Some APIs return a dict with a "result" key
                if "result" in response:
                    result = response["result"]
                    if isinstance(result, list):
                        for item in result:
                            if isinstance(item, dict) and item.get("key") == key_label:
                                return item.get("value")
                    elif isinstance(result, dict):
                        # Some APIs return a dict with key-value pairs
                        for key, val in result.items():
                            if key == key_label:
                                return val
                else:
                    # Some APIs return a dict with key-value pairs directly
                    for key, val in response.items():
                        if key == key_label:
                            return val
        return None
    except Exception:
        return None


@handle_module_errors
def create_or_update_custom_key(
    module: Any, client: Any
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Create or update a custom information key.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    key_label = module.params["key_label"]
    new_key_label = module.params.get("new_key_label")
    description = module.params.get("description")

    # Check if the key already exists
    existing_key = get_existing_key(client, key_label)
    key_exists = existing_key is not None

    # If check_mode is enabled, return now
    if module.check_mode:
        if key_exists:
            if new_key_label or (
                description and description != existing_key.get("description")
            ):
                return format_module_result(
                    True,
                    standardize_custom_key(existing_key),
                    "updated",
                    "custom information key",
                    "custom information keys",
                )
            return format_module_result(
                False,
                standardize_custom_key(existing_key),
                "no changes",
                "custom information key",
                "custom information keys",
            )
        return format_module_result(
            True,
            {"label": key_label, "description": description},
            "created",
            "custom information key",
            "custom information keys",
        )

    # Create or update the key
    try:
        if key_exists:
            # Update the key if new_key_label or description is provided
            if new_key_label or (
                description and description != existing_key.get("description")
            ):
                result = update_custom_key(
                    client,
                    key_label,
                    new_key_label or key_label,
                    description or existing_key.get("description", ""),
                )
                # Get the updated key
                updated_key = get_existing_key(client, new_key_label or key_label)
                return format_module_result(
                    True,
                    standardize_custom_key(updated_key),
                    "updated",
                    "custom information key",
                    "custom information keys",
                )
            return format_module_result(
                False,
                standardize_custom_key(existing_key),
                "no changes",
                "custom information key",
                "custom information keys",
            )
        else:
            # Create the key
            required_params = {"description": description}
            validate_required_params(required_params, "create custom information key")

            result = create_custom_key(client, key_label, description)
            # Get the created key
            created_key = get_existing_key(client, key_label)
            return format_module_result(
                True,
                standardize_custom_key(created_key),
                "created",
                "custom information key",
                "custom information keys",
            )
    except Exception as e:
        raise MLMAPIError(
            format_error_message("create or update custom information key", str(e)),
            response={"key_label": key_label},
        )


@handle_module_errors
def delete_custom_key_module(
    module: Any, client: Any
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Delete a custom information key.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    key_label = module.params["key_label"]

    # Check if the key exists
    existing_key = get_existing_key(client, key_label)
    key_exists = existing_key is not None

    # If check_mode is enabled, return now
    if module.check_mode:
        if key_exists:
            return format_module_result(
                True,
                None,
                "deleted",
                "custom information key",
                "custom information keys",
            )
        return format_module_result(
            False,
            None,
            "not found",
            "custom information key",
            "custom information keys",
        )

    # Delete the key
    try:
        if key_exists:
            delete_custom_key(client, key_label)
            return format_module_result(
                True,
                None,
                "deleted",
                "custom information key",
                "custom information keys",
            )
        return format_module_result(
            False,
            None,
            "not found",
            "custom information key",
            "custom information keys",
        )
    except Exception as e:
        raise MLMAPIError(
            format_error_message("delete custom information key", str(e)),
            response={"key_label": key_label},
        )


@handle_module_errors
def set_custom_value_module(
    module: Any, client: Any
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Set a custom value for a system.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    key_label = module.params["key_label"]
    system_id = module.params["system_id"]
    value = module.params["value"]

    # Check if the key exists
    if not get_existing_key(client, key_label):
        raise MLMAPIError(
            format_error_message(
                "set custom value", "Custom information key does not exist"
            ),
            response={"key_label": key_label},
        )

    # Check if the system exists
    if not validate_system_exists(client, system_id):
        raise MLMAPIError(
            format_error_message("set custom value", "System does not exist"),
            response={"system_id": system_id},
        )

    # Check if the value is already set to the desired value
    current_value = get_current_custom_value(client, system_id, key_label)
    if current_value == value:
        result = {"key_label": key_label, "value": value, "system_id": system_id}
        return format_module_result(
            False, result, "already set", "custom value", "custom values"
        )

    # If check_mode is enabled, return now
    if module.check_mode:
        result = {"key_label": key_label, "value": value, "system_id": system_id}
        return format_module_result(
            True, result, "set", "custom value", "custom values"
        )

    # Set the value
    try:
        set_custom_value(client, system_id, key_label, value)
        result = {"key_label": key_label, "value": value, "system_id": system_id}
        return format_module_result(
            True, result, "set", "custom value", "custom values"
        )
    except Exception as e:
        raise MLMAPIError(
            format_error_message("set custom value", str(e)),
            response={"key_label": key_label, "system_id": system_id},
        )
