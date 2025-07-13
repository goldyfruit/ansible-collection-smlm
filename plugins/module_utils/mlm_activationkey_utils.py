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
This module provides utility functions for working with activation keys in SUSE Multi-Linux Manager.

It contains common functions used by the activationkey and activationkey_info modules to avoid code duplication.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    check_api_response,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_api_utils import (
    get_entity_by_field,
)


def get_activation_key(client, key_id=None, key_name=None):
    """
    Get an activation key by ID or name.

    Args:
        client: The MLM client.
        key_id: The ID of the activation key to find.
        key_name: The name of the activation key to find.

    Returns:
        dict: The activation key if found, None otherwise.
    """
    if key_id is None and key_name is None:
        return None

    from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_api_utils import (
        get_entity_by_field,
    )

    keys_path = "/activationkey/listActivationKeys"
    if key_id is not None:
        return get_entity_by_field(client, keys_path, "id", key_id)
    if key_name is not None:
        key = get_entity_by_field(client, keys_path, "key", key_name)
        if key:
            return key
        # Check if the key matches with organization prefix (e.g., '1-ubuntu-24-04' vs 'ubuntu-24-04')
        entities = client.get(keys_path)
        if isinstance(entities, dict) and "result" in entities:
            entities = entities["result"]
        if isinstance(entities, list):
            for entity in entities:
                actual_key = entity.get("key", "")
                if "-" in actual_key and actual_key.split("-", 1)[1] == key_name:
                    return entity
        return None
    return None


def get_activation_key_by_name(client, key_name):
    """
    Get an activation key by name.

    Args:
        client: The MLM client.
        key_name: The name of the activation key to find.

    Returns:
        dict: The activation key if found, None otherwise.
    """
    return get_activation_key(client, key_name=key_name)


def get_activation_key_by_id(client, key_id):
    """
    Get an activation key by ID.

    Args:
        client: The MLM client.
        key_id: The ID of the activation key to find.

    Returns:
        dict: The activation key if found, None otherwise.
    """
    return get_activation_key(client, key_id=key_id)


def standardize_activation_key_data(key_data, client=None):
    """
    Standardize the activation key data format.

    Args:
        key_data: The raw activation key data from the API.
        client: The MLM client (optional, needed for server group name conversion).

    Returns:
        dict: The standardized activation key data.
    """
    if not key_data:
        return {}

    standardized_key = {
        "id": key_data.get("id"),
        "key": key_data.get("key"),
        "description": key_data.get("description", ""),
        "base_channel_label": key_data.get("base_channel_label", ""),
        "usage_limit": key_data.get("usage_limit", 0),
        "system_count": key_data.get("system_count", 0),
        "disabled": key_data.get("disabled", False),
        "universal_default": key_data.get("universal_default", False),
    }

    # Add optional fields if they exist
    if "child_channel_labels" in key_data:
        standardized_key["child_channel_labels"] = key_data["child_channel_labels"]

    # Convert server group IDs to names for better user experience
    if "server_group_ids" in key_data:
        standardized_key["server_group_ids"] = key_data["server_group_ids"]
        # Also provide server group names
        server_group_names = []
        for group_id in key_data["server_group_ids"]:
            group_name = get_server_group_name_by_id(client, group_id)
            if group_name:
                server_group_names.append(group_name)
        standardized_key["server_group_names"] = server_group_names
    elif "server_group_names" in key_data:
        standardized_key["server_group_names"] = key_data["server_group_names"]

    if "packages" in key_data:
        standardized_key["packages"] = key_data["packages"]
    if "config_channels" in key_data:
        standardized_key["config_channels"] = key_data["config_channels"]

    return standardized_key


def list_activation_keys(client, org_id=None):
    """
    List all activation keys.

    Args:
        client: The MLM client.
        org_id: Optional organization ID to filter keys.

    Returns:
        list: A list of standardized activation key data.
    """
    # Determine the API path
    if org_id:
        path = "/activationkey/listActivationKeys?orgId={}".format(org_id)
    else:
        path = "/activationkey/listActivationKeys"

    keys = client.get(path)
    if not keys:
        return []

    if isinstance(keys, dict) and "result" in keys:
        keys = keys["result"]

    if not isinstance(keys, list):
        return []

    return [
        standardize_activation_key_data(key, client) for key in keys if isinstance(key, dict)
    ]


def get_activation_key_details(client, key_id=None, key_name=None):
    """
    Get detailed information about a specific activation key.

    Args:
        client: The MLM client.
        key_id: The ID of the activation key to get details for.
        key_name: The name of the activation key to get details for.

    Returns:
        dict: The standardized activation key details.
    """
    try:
        # If key_id is provided, try to get the activation key by ID
        if key_id is not None:
            key = get_activation_key_by_id(client, key_id)
            if key:
                return standardize_activation_key_data(key, client)

        # If key_name is provided, try to get the activation key by name
        if key_name:
            key = get_activation_key_by_name(client, key_name)
            if key:
                return standardize_activation_key_data(key, client)

        # If we get here, we couldn't find the activation key
        return {
            "id": key_id,
            "key": key_name,
            "description": "",
            "base_channel_label": "",
            "usage_limit": 0,
            "system_count": 0,
            "disabled": False,
            "universal_default": False,
        }
    except Exception as e:
        # Return a minimal activation key object on error
        return {
            "id": key_id,
            "key": key_name,
            "description": "",
            "base_channel_label": "",
            "usage_limit": 0,
            "system_count": 0,
            "disabled": False,
            "universal_default": False,
            "error": str(e),
        }


def create_activation_key(module, client):
    """
    Create a new activation key.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """

    # Extract module parameters
    key_name = module.params.get("key_name")
    description = module.params.get("description", "")
    base_channel_label = module.params.get("base_channel_label", "")
    usage_limit = module.params.get("usage_limit")
    unlimited_usage_limit = module.params.get("unlimited_usage_limit")
    universal_default = module.params.get("universal_default")
    disabled = module.params.get("disabled")
    contact_method = module.params.get("contact_method")
    entitlements = module.params.get("entitlements", [])

    # Set defaults for parameters not provided
    if usage_limit is None:
        usage_limit = 0
    if unlimited_usage_limit is None:
        unlimited_usage_limit = False
    if universal_default is None:
        universal_default = False
    if disabled is None:
        disabled = False
    if contact_method is None:
        contact_method = "default"

    # Handle empty or None key_name (for autogenerated keys)
    if not key_name:
        key_name = ""

    # If check_mode is enabled, return now
    if module.check_mode:
        return (
            True,
            {"key": key_name},
            "Activation key '{}' would be created".format(key_name or "autogenerated"),
        )

    # Create the activation key using SUSE Multi-Linux Manager API
    # Step 1: Create basic activation key using /activationkey/create
    # This endpoint supports: key, description, baseChannelLabel, usageLimit, entitlements, universalDefault, contactMethod
    create_data = {
        "key": key_name,
        "description": description,
        "baseChannelLabel": base_channel_label,
        "usageLimit": usage_limit,
        "entitlements": entitlements,
        "universalDefault": universal_default,
    }

    # Note: contactMethod is not supported in create endpoint, only in setDetails
    create_path = "/activationkey/create"
    result = client.post(create_path, data=create_data)
    check_api_response(result, "Create activation key", module)

    # Step 2: Apply additional settings via /activationkey/setDetails if needed
    # The setDetails endpoint is required for: unlimited_usage_limit, disabled, contact_method
    additional_params_provided = (
        unlimited_usage_limit
        or disabled
        or (contact_method and contact_method != "default")
    )

    if additional_params_provided:
        # Get the actual key name from the API result (includes org prefix like "1-ubuntu-24-04")
        created_key_name = key_name
        if isinstance(result, dict) and "key" in result:
            # Always use the key name returned by the API as it includes the org prefix
            created_key_name = result["key"]
        elif not created_key_name:
            # If no key name was provided and not in result, try to find the newly created key
            keys = client.get("/activationkey/listActivationKeys")
            if isinstance(keys, dict) and "result" in keys:
                keys = keys["result"]
            if isinstance(keys, list) and keys:
                # Get the most recently created key (assuming it's the last one)
                created_key_name = keys[-1].get("key", "")
        else:
            # If we have a key_name but no result key, find the actual key name with org prefix
            actual_key = get_activation_key_by_name(client, key_name)
            if actual_key and actual_key.get("key"):
                created_key_name = actual_key["key"]

        # Prepare setDetails data with proper API structure
        # The setDetails endpoint expects parameters nested in a 'details' struct
        details_struct = {}
        if unlimited_usage_limit:
            details_struct["unlimited_usage_limit"] = unlimited_usage_limit
        if disabled:
            details_struct["disabled"] = disabled
        if contact_method and contact_method != "default":
            details_struct["contact_method"] = contact_method

        # Structure data according to setDetails API specification
        setdetails_data = {"key": created_key_name, "details": details_struct}
        setdetails_path = "/activationkey/setDetails"
        setdetails_result = client.post(setdetails_path, data=setdetails_data)
        check_api_response(setdetails_result, "Set activation key details", module)

    return (
        True,
        result,
        "Activation key '{}' created successfully".format(key_name or "autogenerated"),
    )


def update_activation_key(module, client):
    """
    Update an existing activation key.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """

    # Extract module parameters
    key_name = module.params["key_name"]
    description = module.params.get("description")
    base_channel_label = module.params.get("base_channel_label")
    usage_limit = module.params.get("usage_limit")
    unlimited_usage_limit = module.params.get("unlimited_usage_limit")
    universal_default = module.params.get("universal_default")
    disabled = module.params.get("disabled")
    contact_method = module.params.get("contact_method")
    entitlements = module.params.get("entitlements")

    # Find the activation key
    key = get_activation_key_by_name(client, key_name)
    if not key:
        return False, None, "Activation key '{}' does not exist".format(key_name)

    # Simple comparison: if user only provided key_name and state=present, no change needed
    if (
        description is None
        and base_channel_label is None
        and usage_limit is None
        and unlimited_usage_limit is None
        and universal_default is None
        and disabled is None
        and contact_method is None
        and entitlements is None
    ):
        return False, key, "Activation key '{}' already exists".format(key_name)

    # Compare current vs desired values to detect changes
    # Build the details struct with only parameters that have changed
    changes_needed = False
    details_struct = {}

    # Check each parameter that was provided and compare with current values
    if description is not None:
        current_desc = key.get("description", "")
        if current_desc != description:
            details_struct["description"] = description
            changes_needed = True

    if base_channel_label is not None:
        current_channel = key.get("base_channel_label", "")
        if current_channel != base_channel_label:
            details_struct["base_channel_label"] = base_channel_label
            changes_needed = True

    if usage_limit is not None:
        current_limit = key.get("usage_limit", 0)
        if current_limit != usage_limit:
            details_struct["usage_limit"] = usage_limit
            changes_needed = True

    if unlimited_usage_limit is not None:
        current_unlimited = key.get("unlimited_usage_limit", False)
        if current_unlimited != unlimited_usage_limit:
            details_struct["unlimited_usage_limit"] = unlimited_usage_limit
            changes_needed = True

    if universal_default is not None:
        current_default = key.get("universal_default", False)
        if current_default != universal_default:
            details_struct["universal_default"] = universal_default
            changes_needed = True

    if disabled is not None:
        current_disabled = key.get("disabled", False)
        if current_disabled != disabled:
            details_struct["disabled"] = disabled
            changes_needed = True

    if contact_method is not None:
        # API returns contact_method field name
        current_contact_method = key.get("contact_method", "default")
        if current_contact_method != contact_method:
            details_struct["contact_method"] = contact_method
            changes_needed = True

    # Note: entitlements are managed separately through dedicated endpoints
    # They should not be passed to setDetails endpoint

    # If no changes needed, return unchanged
    if not changes_needed:
        return False, key, "Activation key '{}' is already up to date".format(key_name)

    # If check_mode is enabled, return now
    if module.check_mode:
        return True, key, "Activation key '{}' would be updated".format(key_name)

    # Update the activation key using /activationkey/setDetails endpoint
    # All updates must use setDetails with proper API structure (nested details)
    try:
        # Use the actual key name from the API (includes org prefix like "1-ubuntu-24-04")
        actual_key_name = key.get("key", key_name)

        # Structure data according to setDetails API specification
        update_data = {"key": actual_key_name, "details": details_struct}

        # Make the API request to update the activation key
        update_path = "/activationkey/setDetails"
        result = client.post(update_path, data=update_data)
        check_api_response(result, "Update activation key", module)

        return True, result, "Activation key '{}' updated successfully".format(key_name)
    except Exception as e:
        module.fail_json(msg="Failed to update activation key: {}".format(str(e)))


def delete_activation_key(module, client):
    """
    Delete an activation key.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """

    # Extract module parameters
    key_name = module.params["key_name"]

    # Find the activation key
    key = get_activation_key_by_name(client, key_name)
    if not key:
        return False, None, "Activation key '{}' does not exist".format(key_name)

    # If check_mode is enabled, return now
    if module.check_mode:
        return True, None, "Activation key '{}' would be deleted".format(key_name)

    # Delete the activation key
    try:
        # Use the actual key name from the API (includes org prefix like "1-ubuntu-24-04")
        actual_key_name = key.get("key", key_name)

        # Make the API request
        delete_path = "/activationkey/delete"
        result = client.post(delete_path, data={"key": actual_key_name})
        check_api_response(result, "Delete activation key", module)

        return True, None, "Activation key '{}' deleted successfully".format(key_name)
    except Exception as e:
        module.fail_json(msg="Failed to delete activation key: {}".format(str(e)))


def manage_activation_key_channels(module, client):
    """
    Manage software channels for an activation key.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """

    # Extract module parameters
    key_name = module.params["key_name"]
    child_channels = module.params.get("child_channels", [])
    channel_state = module.params.get("channel_state", "present")

    # Find the activation key
    key = get_activation_key_by_name(client, key_name)
    if not key:
        module.fail_json(msg="Activation key '{}' does not exist".format(key_name))

    # Get current child channels
    current_channels = key.get("child_channel_labels", [])

    # Determine what changes are needed
    if channel_state == "present":
        # Add channels that are not already present
        channels_to_add = [ch for ch in child_channels if ch not in current_channels]
        if not channels_to_add:
            return (
                False,
                key,
                "All specified channels already added to activation key '{}'".format(
                    key_name
                ),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                key,
                "Channels {} would be added to activation key '{}'".format(
                    channels_to_add, key_name
                ),
            )

        # Add channels
        try:
            # Use the actual key name from the API (includes org prefix like "1-ubuntu-24-04")
            actual_key_name = key.get("key", key_name)

            add_path = "/activationkey/addChildChannels"
            result = client.post(
                add_path,
                data={"key": actual_key_name, "childChannelLabels": channels_to_add},
            )
            check_api_response(result, "Add channels to activation key", module)
            return (
                True,
                key,
                "Channels {} added to activation key '{}'".format(
                    channels_to_add, key_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to add channels to activation key: {}".format(str(e))
            )

    else:  # channel_state == 'absent'
        # Remove channels that are currently present
        channels_to_remove = [ch for ch in child_channels if ch in current_channels]
        if not channels_to_remove:
            return (
                False,
                key,
                "None of the specified channels are present in activation key '{}'".format(
                    key_name
                ),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                key,
                "Channels {} would be removed from activation key '{}'".format(
                    channels_to_remove, key_name
                ),
            )

        # Remove channels
        try:
            # Use the actual key name from the API (includes org prefix like "1-ubuntu-24-04")
            actual_key_name = key.get("key", key_name)

            remove_path = "/activationkey/removeChildChannels"
            result = client.post(
                remove_path,
                data={"key": actual_key_name, "childChannelLabels": channels_to_remove},
            )
            check_api_response(result, "Remove channels from activation key", module)
            return (
                True,
                key,
                "Channels {} removed from activation key '{}'".format(
                    channels_to_remove, key_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to remove channels from activation key: {}".format(str(e))
            )


def manage_activation_key_packages(module, client):
    """
    Manage packages for an activation key.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """

    # Extract module parameters
    key_name = module.params["key_name"]
    packages = module.params.get("packages", [])
    package_state = module.params.get("package_state", "present")

    # Find the activation key
    key = get_activation_key_by_name(client, key_name)
    if not key:
        module.fail_json(msg="Activation key '{}' does not exist".format(key_name))

    # Get current packages - extract package names from the packages list
    current_packages_objs = key.get("packages", [])
    current_packages = []
    if current_packages_objs:
        # Extract package names from package objects
        current_packages = [
            pkg.get("name")
            for pkg in current_packages_objs
            if isinstance(pkg, dict) and "name" in pkg
        ]

    # If packages field is not available or empty, try package_names field
    if not current_packages:
        current_packages = key.get("package_names", [])

    # Determine what changes are needed
    if package_state == "present":
        # Add packages that are not already present
        packages_to_add = [pkg for pkg in packages if pkg not in current_packages]
        if not packages_to_add:
            return (
                False,
                key,
                "All specified packages already added to activation key '{}'".format(
                    key_name
                ),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                key,
                "Packages {} would be added to activation key '{}'".format(
                    packages_to_add, key_name
                ),
            )

        # Add packages
        try:
            # Use the actual key name from the API (includes org prefix like "1-ubuntu-24-04")
            actual_key_name = key.get("key", key_name)

            add_path = "/activationkey/addPackages"
            # Convert package names to package objects with name and optional arch
            package_objects = [{"name": pkg} for pkg in packages_to_add]
            result = client.post(
                add_path, data={"key": actual_key_name, "packages": package_objects}
            )
            check_api_response(result, "Add packages to activation key", module)
            return (
                True,
                key,
                "Packages {} added to activation key '{}'".format(
                    packages_to_add, key_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to add packages to activation key: {}".format(str(e))
            )

    else:  # package_state == 'absent'
        # Remove packages that are currently present
        packages_to_remove = [pkg for pkg in packages if pkg in current_packages]
        if not packages_to_remove:
            return (
                False,
                key,
                "None of the specified packages are present in activation key '{}'".format(
                    key_name
                ),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                key,
                "Packages {} would be removed from activation key '{}'".format(
                    packages_to_remove, key_name
                ),
            )

        # Remove packages
        try:
            # Use the actual key name from the API (includes org prefix like "1-ubuntu-24-04")
            actual_key_name = key.get("key", key_name)

            remove_path = "/activationkey/removePackages"
            # Convert package names to package objects with name and optional arch
            package_objects = [{"name": pkg} for pkg in packages_to_remove]
            result = client.post(
                remove_path, data={"key": actual_key_name, "packages": package_objects}
            )
            check_api_response(result, "Remove packages from activation key", module)
            return (
                True,
                key,
                "Packages {} removed from activation key '{}'".format(
                    packages_to_remove, key_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to remove packages from activation key: {}".format(str(e))
            )


def get_server_group_id_by_name(client, group_name):
    """
    Get server group ID by name.

    Args:
        client: The MLM client.
        group_name: The name of the server group.

    Returns:
        int: The server group ID if found, None otherwise.
    """
    from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_systemgroup_utils import get_systemgroup_by_name

    try:
        group = get_systemgroup_by_name(client, group_name)
        return group.get("id") if group else None
    except Exception:
        return None


def get_server_group_name_by_id(client, group_id):
    """
    Get server group name by ID.

    Args:
        client: The MLM client.
        group_id: The ID of the server group.

    Returns:
        str: The server group name if found, None otherwise.
    """
    from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_systemgroup_utils import get_systemgroup_by_id

    try:
        group = get_systemgroup_by_id(client, group_id)
        return group.get("name") if group else None
    except Exception:
        return None


def manage_activation_key_server_groups(module, client):
    """
    Manage server groups for an activation key.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """

    # Extract module parameters
    key_name = module.params["key_name"]
    server_groups = module.params.get("server_groups", [])
    server_group_state = module.params.get("server_group_state", "present")

    # Find the activation key
    key = get_activation_key_by_name(client, key_name)
    if not key:
        module.fail_json(msg="Activation key '{}' does not exist".format(key_name))

    # Get current server group IDs from the key
    current_server_group_ids = key.get("server_group_ids", [])

    # Convert current server group IDs to names for comparison
    current_server_group_names = []
    for group_id in current_server_group_ids:
        group_name = get_server_group_name_by_id(client, group_id)
        if group_name:
            current_server_group_names.append(group_name)

    # Determine what changes are needed
    if server_group_state == "present":
        # Add server groups that are not already present
        groups_to_add = [
            grp for grp in server_groups if grp not in current_server_group_names
        ]
        if not groups_to_add:
            return (
                False,
                key,
                "All specified server groups already added to activation key '{}'".format(
                    key_name
                ),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                key,
                "Server groups {} would be added to activation key '{}'".format(
                    groups_to_add, key_name
                ),
            )

        # Convert server group names to IDs
        group_ids_to_add = []
        for group_name in groups_to_add:
            group_id = get_server_group_id_by_name(client, group_name)
            if group_id is None:
                module.fail_json(msg="Server group '{}' not found".format(group_name))
            group_ids_to_add.append(group_id)

        # Add server groups
        try:
            # Use the actual key name from the API (includes org prefix like "1-ubuntu-24-04")
            actual_key_name = key.get("key", key_name)

            add_path = "/activationkey/addServerGroups"
            result = client.post(
                add_path,
                data={"key": actual_key_name, "serverGroupIds": group_ids_to_add},
            )
            check_api_response(result, "Add server groups to activation key", module)
            return (
                True,
                key,
                "Server groups {} added to activation key '{}'".format(
                    groups_to_add, key_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to add server groups to activation key: {}".format(str(e))
            )

    else:  # server_group_state == 'absent'
        # Remove server groups that are currently present
        groups_to_remove = [
            grp for grp in server_groups if grp in current_server_group_names
        ]
        if not groups_to_remove:
            return (
                False,
                key,
                "None of the specified server groups are present in activation key '{}'".format(
                    key_name
                ),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                key,
                "Server groups {} would be removed from activation key '{}'".format(
                    groups_to_remove, key_name
                ),
            )

        # Convert server group names to IDs
        group_ids_to_remove = []
        for group_name in groups_to_remove:
            group_id = get_server_group_id_by_name(client, group_name)
            if group_id is None:
                module.fail_json(msg="Server group '{}' not found".format(group_name))
            group_ids_to_remove.append(group_id)

        # Remove server groups
        try:
            # Use the actual key name from the API (includes org prefix like "1-ubuntu-24-04")
            actual_key_name = key.get("key", key_name)

            remove_path = "/activationkey/removeServerGroups"
            result = client.post(
                remove_path,
                data={"key": actual_key_name, "serverGroupIds": group_ids_to_remove},
            )
            check_api_response(
                result, "Remove server groups from activation key", module
            )
            return (
                True,
                key,
                "Server groups {} removed from activation key '{}'".format(
                    groups_to_remove, key_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to remove server groups from activation key: {}".format(
                    str(e)
                )
            )


def manage_activation_key_entitlements(module, client):
    """
    Manage entitlements for an activation key.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """

    # Extract module parameters
    key_name = module.params["key_name"]
    entitlements = module.params.get("entitlements", [])
    entitlement_state = module.params.get("entitlement_state", "present")

    # Find the activation key
    key = get_activation_key_by_name(client, key_name)
    if not key:
        module.fail_json(msg="Activation key '{}' does not exist".format(key_name))

    # Get current entitlements from the key
    current_entitlements = key.get("entitlements", [])

    # Determine what changes are needed
    if entitlement_state == "present":
        # Add entitlements that are not already present
        entitlements_to_add = [ent for ent in entitlements if ent not in current_entitlements]
        if not entitlements_to_add:
            return (
                False,
                key,
                "All specified entitlements already added to activation key '{}'".format(
                    key_name
                ),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                key,
                "Entitlements {} would be added to activation key '{}'".format(
                    entitlements_to_add, key_name
                ),
            )

        # Add entitlements
        try:
            # Use the actual key name from the API (includes org prefix like "1-ubuntu-24-04")
            actual_key_name = key.get("key", key_name)

            add_path = "/activationkey/addEntitlements"
            result = client.post(
                add_path,
                data={"key": actual_key_name, "entitlements": entitlements_to_add},
            )
            check_api_response(result, "Add entitlements to activation key", module)
            return (
                True,
                key,
                "Entitlements {} added to activation key '{}'".format(
                    entitlements_to_add, key_name
                ),
            )
        except Exception as e:
            module.fail_json(
                msg="Failed to add entitlements to activation key: {}".format(str(e))
            )

    else:  # entitlement_state == 'absent'
        # Remove entitlements that are currently present
        entitlements_to_remove = [ent for ent in entitlements if ent in current_entitlements]
        if not entitlements_to_remove:
            return (
                False,
                key,
                "None of the specified entitlements are present in activation key '{}'".format(
                    key_name
                ),
            )

        # If check_mode is enabled, return now
        if module.check_mode:
            return (
                True,
                key,
                "Entitlements {} would be removed from activation key '{}'".format(
                    entitlements_to_remove, key_name
                ),
            )

        # Remove entitlements
        try:
            # Use the actual key name from the API (includes org prefix like "1-ubuntu-24-04")
            actual_key_name = key.get("key", key_name)

            remove_path = "/activationkey/removeEntitlements"
            result = client.post(
                remove_path,
                data={"key": actual_key_name, "entitlements": entitlements_to_remove},
            )
            check_api_response(result, "Remove entitlements from activation key", module)
            return (
                True,
                key,
                "Entitlements {} removed from activation key '{}'".format(
                    entitlements_to_remove, key_name
                ),
t             )
        except Exception as e:
            module.fail_json(
                msg="Failed to remove entitlements from activation key: {}".format(str(e))
            )
