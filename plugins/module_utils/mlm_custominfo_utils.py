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

from typing import Dict, List, Optional, Any, Union


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


def update_custom_key(client: Any, old_label: str, new_label: str, new_description: str) -> int:
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
            system_id = system.get('id')
            if system_id:
                # Get custom values for this system
                system_values = get_custom_values(client, system_id)

                # Check if this system has a value for the old key
                for key_value in system_values:
                    if isinstance(key_value, dict) and key_value.get('keyLabel') == old_label:
                        if system_id not in custom_values:
                            custom_values[system_id] = key_value.get('value', '')

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
    # Based on the SUSE Manager API documentation
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
    # Based on the SUSE Manager API documentation
    path = "/system/getCustomValues?sid={}".format(system_id)
    result = client.get(path)

    # Handle the case where the API returns a dictionary with a "result" key
    if result and isinstance(result, dict) and "result" in result:
        return result["result"]

    return result or []


def standardize_custom_key(key_data: Union[Dict[str, Any], str, None]) -> Dict[str, Any]:
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


def standardize_custom_value(value_data: Union[Dict[str, Any], str, None]) -> Dict[str, Any]:
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
