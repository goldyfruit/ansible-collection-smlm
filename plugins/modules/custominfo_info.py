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

DOCUMENTATION = r'''
---
module: custominfo_info
short_description: Get information about custom system information in SUSE Manager
description:
  - List all custom information keys in SUSE Manager.
  - Get all custom values for a specific system.
  - This module uses the SUSE Manager API to retrieve custom system information.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  system_id:
    description:
      - ID of the system to get custom values for.
      - If provided, returns all custom values for the specified system.
      - If not provided, lists all custom information keys.
    type: int
    required: false
notes:
  - This module requires the SUSE Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to view custom system information.
  - If system_id is not provided, the module will list all custom information keys.
  - If system_id is provided, the module will return all custom values for the specified system.
  - When getting custom values for a system, the system must exist.
  - The module will check if the system exists before trying to get custom values for it.
requirements:
  - python >= 3.6
'''

EXAMPLES = r'''
# Using credentials configuration file (recommended)
- name: List all custom information keys
  goldyfruit.mlm.custominfo_info:
  register: keys_result

- name: Display all custom information keys
  ansible.builtin.debug:
    msg: "{{ keys_result.custom_keys | map(attribute='label') | list }}"

- name: Get all custom values for a system
  goldyfruit.mlm.custominfo_info:
    system_id: 1000010000
  register: values_result

- name: Get custom values using specific instance
  goldyfruit.mlm.custominfo_info:
    instance: staging  # Use staging instance from credentials file
    system_id: 1000010000
  register: staging_values_result

- name: Display all custom values for the system
  ansible.builtin.debug:
    msg: "{{ values_result.values }}"
'''

RETURN = r'''
custom_keys:
  description: List of all custom information keys.
  returned: when system_id is not provided
  type: list
  elements: dict
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
values:
  description: List of all custom values for the specified system.
  returned: when system_id is provided
  type: list
  elements: dict
  contains:
    key_label:
      description: Label of the custom information key.
      type: str
      sample: "ASSET_TAG"
    value:
      description: Value set for the key.
      type: str
      sample: "A12345"
    created:
      description: Timestamp when the value was created.
      type: str
      sample: "2025-01-01T12:00:00Z"
    modified:
      description: Timestamp when the value was last modified.
      type: str
      sample: "2025-01-01T12:00:00Z"
    creator:
      description: User who created the value.
      type: str
      sample: "admin"
    modifier:
      description: User who last modified the value.
      type: str
      sample: "admin"
'''

import os
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_custominfo_utils import (
    list_all_keys,
    get_custom_values,
    standardize_custom_key,
    standardize_custom_value,
)


def main():
    """Main module execution."""
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        system_id=dict(type='int', required=False),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Extract module parameters
    system_id = module.params.get('system_id')

    # Create the MLM client
    client = MLMClient(module)

    # Login to the API
    client.login()

    try:
        # Determine what information to retrieve
        if system_id is not None:
            # Check if the system exists using get_systems method
            try:
                # Get all systems
                systems = client.get_systems()

                # Check if the system exists
                system_exists = False
                for system in systems:
                    if system.get('id') == system_id:
                        system_exists = True
                        break

                if not system_exists:
                    module.fail_json(msg="System with ID {} does not exist".format(system_id))
            except Exception as e:
                module.fail_json(msg="Failed to check if system exists: {}".format(str(e)))

            # Get all custom values for the specified system
            values_data = get_custom_values(client, system_id)
            standardized_values = []
            for value in values_data:
                standardized_values.append(standardize_custom_value(value))
            module.exit_json(changed=False, values=standardized_values)
        else:
            # List all custom information keys
            keys_data = list_all_keys(client)
            standardized_keys = []

            # Handle the case where the API returns a dictionary with a "result" key
            if isinstance(keys_data, dict) and "result" in keys_data:
                keys_to_process = keys_data["result"]
            else:
                keys_to_process = keys_data

            for key in keys_to_process:
                # Handle both string and dictionary keys
                if isinstance(key, str):
                    standardized_keys.append(standardize_custom_key({"label": key}))
                else:
                    standardized_keys.append(standardize_custom_key(key))
            # Return the standardized keys as a list
            module.exit_json(changed=False, custom_keys=standardized_keys)
    except Exception as e:
        module.fail_json(msg="Failed to retrieve custom information: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == '__main__':
    main()
