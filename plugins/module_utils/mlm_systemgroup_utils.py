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
This module provides utility functions for working with system groups in SUSE Multi-Linux Manager.

It contains common functions used by the systemgroup and systemgroup_info modules to avoid code duplication.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Dict, List, Optional, Any, Tuple
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    check_api_response,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_api_utils import (
    get_entity_by_field,
)


def get_systemgroup_by_name(client: Any, group_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a system group by name.

    Args:
        client: The MLM client.
        group_name: The name of the system group to find.

    Returns:
        dict: The system group if found, None otherwise.
    """
    return get_entity_by_field(client, "/systemgroup/listAllGroups", "name", group_name)


def get_systemgroup_by_id(client: Any, group_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a system group by ID.

    Args:
        client: The MLM client.
        group_id: The ID of the system group to find.

    Returns:
        dict: The system group if found, None otherwise.
    """
    return get_entity_by_field(client, "/systemgroup/listAllGroups", "id", group_id)


def standardize_systemgroup_data(group_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Standardize the system group data format.

    Args:
        group_data: The raw system group data from the API.

    Returns:
        dict: The standardized system group data.
    """
    if not group_data:
        return {}

    standardized_group = {
        "id": group_data.get("id"),
        "name": group_data.get("name", ""),
        "description": group_data.get("description", ""),
        "org_id": group_data.get("org_id", 0),
        "system_count": group_data.get("system_count", 0),
        "current_members": group_data.get("current_members", 0),
        "max_members": group_data.get("max_members", 0),
    }

    # Add optional fields if they exist
    if "systems" in group_data:
        standardized_group["systems"] = group_data["systems"]
    if "admins" in group_data:
        standardized_group["admins"] = group_data["admins"]

    return standardized_group


def list_systemgroups(client: Any) -> List[Dict[str, Any]]:
    """
    List all system groups.

    Args:
        client: The MLM client.

    Returns:
        list: A list of standardized system group data.
    """
    path = "/systemgroup/listAllGroups"
    groups = client.get(path)
    if not groups:
        return []

    if isinstance(groups, dict) and "result" in groups:
        groups = groups["result"]

    if not isinstance(groups, list):
        return []

    return [standardize_systemgroup_data(group) for group in groups if isinstance(group, dict)]


def get_systemgroup_details(
    client: Any,
    group_id: Optional[int] = None,
    group_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific system group.

    Args:
        client: The MLM client.
        group_id: The ID of the system group to get details for.
        group_name: The name of the system group to get details for.

    Returns:
        dict: The standardized system group details.
    """
    try:
        # Try to get the system group by ID or name
        if group_id is not None:
            group = get_systemgroup_by_id(client, group_id)
        elif group_name:
            group = get_systemgroup_by_name(client, group_name)
        else:
            return None

        if group:
            return standardize_systemgroup_data(group)

        return None
    except Exception:
        return None


def create_systemgroup(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Create a new system group.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    group_name = module.params["name"]
    description = module.params["description"]

    # Check if the system group already exists
    group = get_systemgroup_by_name(client, group_name)
    if group:
        return False, group, "System group '{}' already exists".format(group_name)

    # If check_mode is enabled, return now
    if module.check_mode:
        return (
            True,
            {"name": group_name, "description": description},
            "System group '{}' would be created".format(group_name),
        )

    # Create the system group
    try:
        # Make the API request
        create_path = "/systemgroup/create"
        data = {"name": group_name, "description": description}
        result = client.post(create_path, data=data)
        check_api_response(result, "Create system group", module)

        return (
            True,
            result,
            "System group '{}' created successfully".format(group_name),
        )
    except Exception as e:
        module.fail_json(msg="Failed to create system group: {}".format(str(e)))


def update_systemgroup(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Update an existing system group.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    group_name = module.params["name"]
    new_description = module.params["description"]

    # Check if the system group exists
    group = get_systemgroup_by_name(client, group_name)
    if not group:
        module.fail_json(msg="System group '{}' does not exist".format(group_name))

    # Check if description needs to be updated
    current_description = group.get("description", "")
    if current_description == new_description:
        return False, group, "System group '{}' already has the specified description".format(group_name)

    # If check_mode is enabled, return now
    if module.check_mode:
        return (
            True,
            {"name": group_name, "description": new_description},
            "System group '{}' description would be updated".format(group_name),
        )

    # Update the system group
    try:
        # Make the API request
        update_path = "/systemgroup/update"
        data = {"sgid": group["id"], "description": new_description}
        result = client.post(update_path, data=data)
        check_api_response(result, "Update system group", module)

        return (
            True,
            result,
            "System group '{}' updated successfully".format(group_name),
        )
    except Exception as e:
        module.fail_json(msg="Failed to update system group: {}".format(str(e)))


def delete_systemgroup(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Delete a system group.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    group_name = module.params["name"]

    # Check if the system group exists
    group = get_systemgroup_by_name(client, group_name)
    if not group:
        return False, None, "System group '{}' does not exist".format(group_name)

    # If check_mode is enabled, return now
    if module.check_mode:
        return (
            True,
            None,
            "System group '{}' would be deleted".format(group_name),
        )

    # Delete the system group
    try:
        # Make the API request
        delete_path = "/systemgroup/delete"
        data = {"sgid": group["id"]}
        result = client.post(delete_path, data=data)
        check_api_response(result, "Delete system group", module)

        return (
            True,
            None,
            "System group '{}' deleted successfully".format(group_name),
        )
    except Exception as e:
        module.fail_json(msg="Failed to delete system group: {}".format(str(e)))


def manage_systemgroup_systems(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Manage systems in a system group.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    group_name = module.params["name"]
    systems = module.params.get("systems", [])
    systems_state = module.params.get("systems_state", "present")

    # Check if the system group exists
    group = get_systemgroup_by_name(client, group_name)
    if not group:
        module.fail_json(msg="System group '{}' does not exist".format(group_name))

    group_id = group["id"]

    # If check_mode is enabled, return now
    if module.check_mode:
        action = "added to" if systems_state == "present" else "removed from"
        return (
            True,
            {"systems": systems},
            "Systems would be {} system group '{}'".format(action, group_name),
        )

    # Manage systems in the group
    try:
        changed = False
        results = []

        for system_id in systems:
            try:
                if systems_state == "present":
                    # Add system to group
                    path = "/systemgroup/addOrRemoveSystems"
                    data = {"sgid": group_id, "add": [system_id], "remove": []}
                    result = client.post(path, data=data)
                    results.append({"system_id": system_id, "action": "added", "result": result})
                    changed = True
                elif systems_state == "absent":
                    # Remove system from group
                    path = "/systemgroup/addOrRemoveSystems"
                    data = {"sgid": group_id, "add": [], "remove": [system_id]}
                    result = client.post(path, data=data)
                    results.append({"system_id": system_id, "action": "removed", "result": result})
                    changed = True
            except Exception as e:
                results.append({"system_id": system_id, "action": "failed", "error": str(e)})

        action = "managed in" if systems_state == "present" else "removed from"
        return (
            changed,
            {"systems": results},
            "Systems {} system group '{}'".format(action, group_name),
        )
    except Exception as e:
        module.fail_json(msg="Failed to manage systems in group: {}".format(str(e)))


def manage_systemgroup_administrators(module: Any, client: Any) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Manage administrators in a system group.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    group_name = module.params["name"]
    administrators = module.params.get("administrators", [])
    administrators_state = module.params.get("administrators_state", "present")

    # Check if the system group exists
    group = get_systemgroup_by_name(client, group_name)
    if not group:
        module.fail_json(msg="System group '{}' does not exist".format(group_name))

    group_id = group["id"]

    # If check_mode is enabled, return now
    if module.check_mode:
        action = "added to" if administrators_state == "present" else "removed from"
        return (
            True,
            {"administrators": administrators},
            "Administrators would be {} system group '{}'".format(action, group_name),
        )

    # Manage administrators in the group
    try:
        changed = False
        results = []

        for admin_login in administrators:
            try:
                if administrators_state == "present":
                    # Add administrator to group
                    path = "/systemgroup/addOrRemoveAdmins"
                    data = {"sgid": group_id, "add": [admin_login], "remove": []}
                    result = client.post(path, data=data)
                    results.append({"admin_login": admin_login, "action": "added", "result": result})
                    changed = True
                elif administrators_state == "absent":
                    # Remove administrator from group
                    path = "/systemgroup/addOrRemoveAdmins"
                    data = {"sgid": group_id, "add": [], "remove": [admin_login]}
                    result = client.post(path, data=data)
                    results.append({"admin_login": admin_login, "action": "removed", "result": result})
                    changed = True
            except Exception as e:
                results.append({"admin_login": admin_login, "action": "failed", "error": str(e)})

        action = "managed in" if administrators_state == "present" else "removed from"
        return (
            changed,
            {"administrators": results},
            "Administrators {} system group '{}'".format(action, group_name),
        )
    except Exception as e:
        module.fail_json(msg="Failed to manage administrators in group: {}".format(str(e)))
