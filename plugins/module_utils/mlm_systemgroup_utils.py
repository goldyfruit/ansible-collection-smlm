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

from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import check_api_response
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_api_utils import get_entity_by_field


def get_systemgroup_by_name(client, group_name):
    """
    Get a system group by name.

    Args:
        client: The MLM client.
        group_name: The name of the system group to find.

    Returns:
        dict: The system group if found, None otherwise.
    """
    return get_entity_by_field(client, "/systemgroup/listAllGroups", "name", group_name)


def get_systemgroup_by_id(client, group_id):
    """
    Get a system group by ID.

    Args:
        client: The MLM client.
        group_id: The ID of the system group to find.

    Returns:
        dict: The system group if found, None otherwise.
    """
    return get_entity_by_field(client, "/systemgroup/listAllGroups", "id", group_id)


def standardize_systemgroup_data(group_data):
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
        "name": group_data.get("name"),
        "description": group_data.get("description", ""),
        "org_id": group_data.get("org_id"),
        "system_count": group_data.get("system_count", 0),
    }

    return standardized_group


def list_systemgroups(client):
    """
    List all system groups.

    Args:
        client: The MLM client.

    Returns:
        list: A list of standardized system group data.
    """
    groups = client.get("/systemgroup/listAllGroups")
    if not groups:
        return []

    if isinstance(groups, dict) and "result" in groups:
        groups = groups["result"]

    if not isinstance(groups, list):
        return []

    return [standardize_systemgroup_data(group) for group in groups if isinstance(group, dict)]


def get_systemgroup_details(client, group_id=None, group_name=None):
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
        # If group_id is provided, try to get the system group by ID
        if group_id is not None:
            group = get_systemgroup_by_id(client, group_id)
            if group:
                return standardize_systemgroup_data(group)

        # If group_name is provided, try to get the system group by name
        if group_name:
            group = get_systemgroup_by_name(client, group_name)
            if group:
                return standardize_systemgroup_data(group)

        # If we get here, we couldn't find the system group
        return {
            "id": group_id,
            "name": group_name,
            "description": "",
            "org_id": None,
            "system_count": 0,
        }
    except Exception as e:
        # Return a minimal system group object on error
        return {
            "id": group_id,
            "name": group_name,
            "description": "",
            "org_id": None,
            "system_count": 0,
            "error": str(e),
        }


def create_systemgroup(module, client):
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
    description = module.params.get("description", "")

    # If check_mode is enabled, return now
    if module.check_mode:
        return (
            True,
            {"name": group_name, "description": description},
            "System group '{}' would be created".format(group_name),
        )

    # Create the system group
    try:
        create_data = {
            "name": group_name,
            "description": description,
        }

        create_path = "/systemgroup/create"
        result = client.post(create_path, data=create_data)
        check_api_response(result, "Create system group", module)

        return (
            True,
            result,
            "System group '{}' created successfully".format(group_name),
        )
    except Exception as e:
        module.fail_json(msg="Failed to create system group: {}".format(str(e)))


def update_systemgroup(module, client):
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
    description = module.params.get("description")

    # Find the system group
    group = get_systemgroup_by_name(client, group_name)
    if not group:
        return False, None, "System group '{}' does not exist".format(group_name)

    # Simple comparison: if user only provided name and state=present, no change needed
    if description is None:
        return False, group, "System group '{}' already exists".format(group_name)

    # Check if description needs to be updated
    current_description = group.get("description", "")
    if current_description == description:
        return False, group, "System group '{}' is already up to date".format(group_name)

    # If check_mode is enabled, return now
    if module.check_mode:
        return True, group, "System group '{}' would be updated".format(group_name)

    # Update the system group
    try:
        update_data = {
            "systemGroupName": group_name,
            "description": description,
        }

        update_path = "/systemgroup/update"
        result = client.post(update_path, data=update_data)
        check_api_response(result, "Update system group", module)

        return True, result, "System group '{}' updated successfully".format(group_name)
    except Exception as e:
        module.fail_json(msg="Failed to update system group: {}".format(str(e)))


def delete_systemgroup(module, client):
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

    # Find the system group
    group = get_systemgroup_by_name(client, group_name)
    if not group:
        return False, None, "System group '{}' does not exist".format(group_name)

    # If check_mode is enabled, return now
    if module.check_mode:
        return True, None, "System group '{}' would be deleted".format(group_name)

    # Delete the system group
    try:
        delete_path = "/systemgroup/delete"
        result = client.post(delete_path, data={"systemGroupName": group_name})
        check_api_response(result, "Delete system group", module)

        return True, None, "System group '{}' deleted successfully".format(group_name)
    except Exception as e:
        module.fail_json(msg="Failed to delete system group: {}".format(str(e)))


def manage_systemgroup_systems(module, client):
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
    system_state = module.params.get("system_state", "present")

    # Find the system group
    group = get_systemgroup_by_name(client, group_name)
    if not group:
        module.fail_json(msg="System group '{}' does not exist".format(group_name))

    # Get current systems in the group
    try:
        current_systems_result = client.get("/systemgroup/listSystems", params={"systemGroupName": group_name})
        if isinstance(current_systems_result, dict) and "result" in current_systems_result:
            current_systems_result = current_systems_result["result"]
        current_systems = [sys.get("id") for sys in current_systems_result if isinstance(sys, dict) and "id" in sys]
    except Exception:
        current_systems = []

    # Determine what changes are needed
    if system_state == "present":
        # Add systems that are not already present
        systems_to_add = [sys for sys in systems if sys not in current_systems]
        if not systems_to_add:
            return (
                False,
                group,
                "All specified systems already in system group '{}'".format(group_name),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                group,
                "Systems {} would be added to system group '{}'".format(
                    systems_to_add, group_name
                ),
            )

        # Add systems
        try:
            add_path = "/systemgroup/addOrRemoveSystems"
            result = client.post(add_path, data={
                "systemGroupName": group_name,
                "serverIds": systems_to_add,
                "add": True
            })
            check_api_response(result, "Add systems to system group", module)
            return (
                True,
                group,
                "Systems {} added to system group '{}'".format(
                    systems_to_add, group_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to add systems to system group: {}".format(str(e))
            )

    else:  # system_state == 'absent'
        # Remove systems that are currently present
        systems_to_remove = [sys for sys in systems if sys in current_systems]
        if not systems_to_remove:
            return (
                False,
                group,
                "None of the specified systems are in system group '{}'".format(
                    group_name
                ),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                group,
                "Systems {} would be removed from system group '{}'".format(
                    systems_to_remove, group_name
                ),
            )

        # Remove systems
        try:
            remove_path = "/systemgroup/addOrRemoveSystems"
            result = client.post(remove_path, data={
                "systemGroupName": group_name,
                "serverIds": systems_to_remove,
                "add": False
            })
            check_api_response(result, "Remove systems from system group", module)
            return (
                True,
                group,
                "Systems {} removed from system group '{}'".format(
                    systems_to_remove, group_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to remove systems from system group: {}".format(str(e))
            )


def manage_systemgroup_administrators(module, client):
    """
    Manage administrators for a system group.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    group_name = module.params["name"]
    administrators = module.params.get("administrators", [])
    admin_state = module.params.get("admin_state", "present")

    # Find the system group
    group = get_systemgroup_by_name(client, group_name)
    if not group:
        module.fail_json(msg="System group '{}' does not exist".format(group_name))

    # Get current administrators
    try:
        current_admins_result = client.get("/systemgroup/listAdministrators", params={"systemGroupName": group_name})
        if isinstance(current_admins_result, dict) and "result" in current_admins_result:
            current_admins_result = current_admins_result["result"]
        current_admins = [admin.get("login") for admin in current_admins_result if isinstance(admin, dict) and "login" in admin]
    except Exception:
        current_admins = []

    # Determine what changes are needed
    if admin_state == "present":
        # Add administrators that are not already present
        admins_to_add = [admin for admin in administrators if admin not in current_admins]
        if not admins_to_add:
            return (
                False,
                group,
                "All specified administrators already manage system group '{}'".format(group_name),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                group,
                "Administrators {} would be added to system group '{}'".format(
                    admins_to_add, group_name
                ),
            )

        # Add administrators
        try:
            add_path = "/systemgroup/addOrRemoveAdmins"
            result = client.post(add_path, data={
                "systemGroupName": group_name,
                "loginName": admins_to_add,
                "add": 1
            })
            check_api_response(result, "Add administrators to system group", module)
            return (
                True,
                group,
                "Administrators {} added to system group '{}'".format(
                    admins_to_add, group_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to add administrators to system group: {}".format(str(e))
            )

    else:  # admin_state == 'absent'
        # Remove administrators that are currently present
        admins_to_remove = [admin for admin in administrators if admin in current_admins]
        if not admins_to_remove:
            return (
                False,
                group,
                "None of the specified administrators manage system group '{}'".format(
                    group_name
                ),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                group,
                "Administrators {} would be removed from system group '{}'".format(
                    admins_to_remove, group_name
                ),
            )

        # Remove administrators
        try:
            remove_path = "/systemgroup/addOrRemoveAdmins"
            result = client.post(remove_path, data={
                "systemGroupName": group_name,
                "loginName": admins_to_remove,
                "add": 0
            })
            check_api_response(result, "Remove administrators from system group", module)
            return (
                True,
                group,
                "Administrators {} removed from system group '{}'".format(
                    admins_to_remove, group_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to remove administrators from system group: {}".format(str(e))
            )
