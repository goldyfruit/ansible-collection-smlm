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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: custominfo
short_description: Manage custom system information in SUSE Manager
description:
  - Create, update, or delete custom information keys in SUSE Manager.
  - Set custom information values for systems.
  - This module uses the SUSE Manager API to manage custom system information.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  key_label:
    description:
      - Label of the custom information key.
      - Required for all operations except when listing all keys.
    type: str
    required: false
  new_key_label:
    description:
      - New label for the custom information key when updating.
      - Only used when state=present and key_label is provided.
    type: str
    required: false
  description:
    description:
      - Description of the custom information key.
      - Required when creating a new key.
      - Optional when updating an existing key.
    type: str
    required: false
  system_id:
    description:
      - ID of the system to set custom information for.
      - Required when setting a custom value.
    type: int
    required: false
  value:
    description:
      - Value to set for the custom information key.
      - Required when setting a custom value.
    type: str
    required: false
  state:
    description:
      - Whether the custom information key should exist or not.
      - When C(present), the key will be created if it doesn't exist, or updated if it does.
      - When C(absent), the key will be deleted.
      - When C(value), a custom value will be set for a system.
      - When changing a key's label (using new_key_label), the module will preserve all custom values
        associated with the old key and apply them to the new key.
    type: str
    choices: [ present, absent, value ]
    default: present
notes:
  - This module requires the SUSE Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to manage custom system information.
  - Custom information keys must have unique labels.
  - When setting a custom value, the key must already exist.
  - When setting a custom value, the system must exist.
  - The module will check if the system exists before trying to set a custom value for it.
  - When changing a key's label, the module will preserve all custom values associated with the old key
    and apply them to the new key.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Using credentials configuration file (recommended)
- name: Create a new custom information key
  goldyfruit.mlm.custominfo:
    key_label: "ASSET_TAG"
    description: "Asset tag for inventory tracking"
    state: present
  register: key_result

- name: Update an existing custom information key
  goldyfruit.mlm.custominfo:
    key_label: "ASSET_TAG"
    new_key_label: "INVENTORY_TAG"
    description: "Updated asset tag for inventory tracking"
    state: present
  register: update_result

- name: Set a custom value for a system
  goldyfruit.mlm.custominfo:
    key_label: "INVENTORY_TAG"
    system_id: 1000010000
    value: "A12345"
    state: value
  register: value_result

- name: Set custom value using specific instance
  goldyfruit.mlm.custominfo:
    instance: staging  # Use staging instance from credentials file
    key_label: "INVENTORY_TAG"
    system_id: 1000010000
    value: "B67890"
    state: value
  register: staging_value_result

- name: Delete a custom information key
  goldyfruit.mlm.custominfo:
    key_label: "INVENTORY_TAG"
    state: absent
  register: delete_result
"""

RETURN = r"""
key:
  description: Information about the custom information key.
  returned: when state=present
  type: dict
  contains:
    label:
      description: Label of the custom information key.
      type: str
      sample: "ASSET_TAG"
    description:
      description: Description of the custom information key.
      type: str
      sample: "Asset tag for inventory tracking"
    created:
      description: Timestamp when the key was created.
      type: str
      sample: "2025-01-01T12:00:00Z"
    modified:
      description: Timestamp when the key was last modified.
      type: str
      sample: "2025-01-01T12:00:00Z"
    creator:
      description: User who created the key.
      type: str
      sample: "admin"
    modifier:
      description: User who last modified the key.
      type: str
      sample: "admin"
value:
  description: Information about the custom value set for a system.
  returned: when state=value
  type: dict
  contains:
    key_label:
      description: Label of the custom information key.
      type: str
      sample: "ASSET_TAG"
    value:
      description: Value set for the key.
      type: str
      sample: "A12345"
    system_id:
      description: ID of the system the value was set for.
      type: int
      sample: 1000010000
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "Custom information key created successfully"
"""

import os
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_custominfo_utils import (
    create_custom_key,
    update_custom_key,
    delete_custom_key,
    list_all_keys,
    set_custom_value,
    standardize_custom_key,
)


def create_or_update_key(module, client):
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
    existing_keys = list_all_keys(client)
    key_exists = False
    existing_key = None

    # Handle the case where the API returns a dictionary with a "result" key
    if isinstance(existing_keys, dict) and "result" in existing_keys:
        keys_to_check = existing_keys["result"]
    else:
        keys_to_check = existing_keys

    for key in keys_to_check:
        # Handle both string and dictionary keys
        if isinstance(key, str) and key == key_label:
            key_exists = True
            existing_key = {"label": key}
            break
        elif isinstance(key, dict) and key.get("label") == key_label:
            key_exists = True
            existing_key = key
            break

    # If check_mode is enabled, return now
    if module.check_mode:
        if key_exists:
            if new_key_label or (
                description and description != existing_key.get("description")
            ):
                return (
                    True,
                    standardize_custom_key(existing_key),
                    "Custom information key would be updated",
                )
            return (
                False,
                standardize_custom_key(existing_key),
                "Custom information key already exists",
            )
        return (
            True,
            {"label": key_label, "description": description},
            "Custom information key would be created",
        )

    # Create or update the key
    try:
        if key_exists:
            # Update the key if new_key_label or description is provided
            if new_key_label or (
                description and description != existing_key.get("description")
            ):
                # No warning needed as custom values are preserved

                result = update_custom_key(
                    client,
                    key_label,
                    new_key_label or key_label,
                    description or existing_key.get("description", ""),
                )
                # Get the updated key
                updated_keys = list_all_keys(client)
                updated_key = None

                # Handle the case where the API returns a dictionary with a "result" key
                if isinstance(updated_keys, dict) and "result" in updated_keys:
                    keys_to_check = updated_keys["result"]
                else:
                    keys_to_check = updated_keys

                for key in keys_to_check:
                    # Handle both string and dictionary keys
                    if isinstance(key, str):
                        if key == (new_key_label or key_label):
                            updated_key = {"label": key}
                            break
                    elif isinstance(key, dict) and key.get("label") == (
                        new_key_label or key_label
                    ):
                        updated_key = key
                        break
                return (
                    True,
                    standardize_custom_key(updated_key),
                    "Custom information key updated successfully",
                )
            return (
                False,
                standardize_custom_key(existing_key),
                "Custom information key already exists",
            )
        else:
            # Create the key
            if not description:
                module.fail_json(
                    msg="Description is required when creating a new custom information key"
                )
            result = create_custom_key(client, key_label, description)
            # Get the created key
            created_keys = list_all_keys(client)
            created_key = None

            # Handle the case where the API returns a dictionary with a "result" key
            if isinstance(created_keys, dict) and "result" in created_keys:
                keys_to_check = created_keys["result"]
            else:
                keys_to_check = created_keys

            for key in keys_to_check:
                # Handle both string and dictionary keys
                if isinstance(key, str):
                    if key == key_label:
                        created_key = {"label": key}
                        break
                elif isinstance(key, dict) and key.get("label") == key_label:
                    created_key = key
                    break
            return (
                True,
                standardize_custom_key(created_key),
                "Custom information key created successfully",
            )
    except Exception as e:
        module.fail_json(
            msg="Failed to create or update custom information key: {}".format(str(e))
        )


def delete_key(module, client):
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
    existing_keys = list_all_keys(client)
    key_exists = False
    existing_key = None

    # Handle the case where the API returns a dictionary with a "result" key
    if isinstance(existing_keys, dict) and "result" in existing_keys:
        keys_to_check = existing_keys["result"]
    else:
        keys_to_check = existing_keys

    for key in keys_to_check:
        # Handle both string and dictionary keys
        if isinstance(key, str) and key == key_label:
            key_exists = True
            existing_key = {"label": key}
            break
        elif isinstance(key, dict) and key.get("label") == key_label:
            key_exists = True
            existing_key = key
            break

    # If check_mode is enabled, return now
    if module.check_mode:
        if key_exists:
            return True, None, "Custom information key '{}' would be deleted".format(key_label)
        return False, None, "Custom information key '{}' does not exist".format(key_label)

    # Delete the key
    try:
        if key_exists:
            delete_custom_key(client, key_label)
            return (
                True,
                None,
                "Custom information key '{}' deleted successfully".format(key_label),
            )
        return False, None, "Custom information key '{}' does not exist".format(key_label)
    except Exception as e:
        module.fail_json(msg="Failed to delete custom information key: {}".format(str(e)))


def set_value(module, client):
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
    existing_keys = list_all_keys(client)

    key_exists = False

    # Handle the case where the API returns a dictionary with a "result" key
    if isinstance(existing_keys, dict) and "result" in existing_keys:
        keys_to_check = existing_keys["result"]
    else:
        keys_to_check = existing_keys

    for key in keys_to_check:
        # Handle both string and dictionary keys
        if isinstance(key, str) and key == key_label:
            key_exists = True
            break
        elif isinstance(key, dict) and key.get("label") == key_label:
            key_exists = True
            break

    if not key_exists:
        module.fail_json(msg="Custom information key '{}' does not exist".format(key_label))

    # Check if the system exists using get_systems method
    try:
        # Get all systems
        systems = client.get_systems()

        # Check if the system exists
        system_exists = False
        for system in systems:
            if system.get("id") == system_id:
                system_exists = True
                break

        if not system_exists:
            module.fail_json(msg="System with ID {} does not exist".format(system_id))
    except Exception as e:
        module.fail_json(msg="Failed to check if system exists: {}".format(str(e)))

    # Check if the value is already set to the desired value
    try:
        # Get the current value
        current_value = None

        # Make the API request to get the current value using client method
        path = "/system/getCustomValues?sid={}".format(system_id)
        response = client.get(path)

        # Handle case where response is None or not a list/dict
        if response:
            if isinstance(response, list):
                for item in response:
                    if isinstance(item, dict) and item.get("key") == key_label:
                        current_value = item.get("value")
                        break
            elif isinstance(response, dict):
                # Some APIs return a dict with a "result" key
                if "result" in response:
                    result = response["result"]
                    if isinstance(result, list):
                        for item in result:
                            if isinstance(item, dict) and item.get("key") == key_label:
                                current_value = item.get("value")
                                break
                    elif isinstance(result, dict):
                        # Some APIs return a dict with key-value pairs
                        for key, val in result.items():
                            if key == key_label:
                                current_value = val
                                break
                else:
                    # Some APIs return a dict with key-value pairs directly
                    for key, val in response.items():
                        if key == key_label:
                            current_value = val
                            break

        # If the value is already set to the desired value, return unchanged
        if current_value == value:
            return (
                False,
                {"key_label": key_label, "value": value, "system_id": system_id},
                "Custom value for key '{}' is already set to '{}' for system {}".format(key_label, value, system_id),
            )
    except Exception:
        # If we can't get the current value, proceed with setting the value
        pass

    # If check_mode is enabled, return now
    if module.check_mode:
        return (
            True,
            {"key_label": key_label, "value": value, "system_id": system_id},
            "Custom value for key '{}' would be set for system {}".format(key_label, system_id),
        )

    # Set the value
    try:
        set_custom_value(client, system_id, key_label, value)
        return (
            True,
            {"key_label": key_label, "value": value, "system_id": system_id},
            "Custom value for key '{}' set successfully for system {}".format(key_label, system_id),
        )
    except Exception as e:
        module.fail_json(msg="Failed to set custom value: {}".format(str(e)))


def main():
    """Main module execution."""
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        key_label=dict(type="str", required=False),
        new_key_label=dict(type="str", required=False),
        description=dict(type="str", required=False),
        system_id=dict(type="int", required=False),
        value=dict(type="str", required=False),
        state=dict(
            type="str", default="present", choices=["present", "absent", "value"]
        ),
    )

    # Define required arguments based on state
    required_if = [
        ["state", "present", ["key_label"]],
        ["state", "absent", ["key_label"]],
        ["state", "value", ["key_label", "system_id", "value"]],
    ]

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
    )

    # Create the MLM client
    client = MLMClient(module)

    # Login to the API
    client.login()

    try:
        # Determine what to do based on the state
        state = module.params["state"]
        if state == "present":
            changed, result, msg = create_or_update_key(module, client)
        elif state == "absent":
            changed, result, msg = delete_key(module, client)
        else:  # state == 'value'
            changed, result, msg = set_value(module, client)

        # Return the result
        if result:
            if state == "present":
                module.exit_json(changed=changed, msg=msg, key=result)
            elif state == "value":
                module.exit_json(changed=changed, msg=msg, value=result)
        else:
            module.exit_json(changed=changed, msg=msg)
    except Exception as e:
        module.fail_json(msg="Failed to manage custom information: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == '__main__':
    main()
