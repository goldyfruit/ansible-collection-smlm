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
module: activationkey_info
short_description: Get information about activation keys in SUSE Multi-Linux Manager
description:
  - Get information about activation keys in SUSE Multi-Linux Manager.
  - If no activation key identifier is provided, lists all activation keys.
  - If an activation key ID or name is provided, returns detailed information about that specific activation key.
  - This module uses the SUSE Multi-Linux Manager API to retrieve activation key information.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  key_id:
    description:
      - ID of the activation key to get details for.
      - If provided, returns detailed information about this specific activation key.
      - If both key_id and key_name are provided, key_id takes precedence.
    type: int
    required: false
  key_name:
    description:
      - Name of the activation key to get details for.
      - If provided, returns detailed information about this specific activation key.
    type: str
    required: false
  org_id:
    description:
      - Organization ID to filter activation keys.
      - If provided, only activation keys from this organization will be returned.
    type: int
    required: false
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to view activation key information.
  - If neither key_id nor key_name is provided, the module will list all activation keys.
  - If either key_id or key_name is provided, the module will return detailed information about that specific activation key.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
- name: List all activation keys
  goldyfruit.mlm.activationkey_info:
    url: https://suma.example.com
    username: admin
    password: admin
  register: key_list

- name: Display activation key names
  ansible.builtin.debug:
    msg: "{{ key_list.activation_keys | map(attribute='key') | list }}"

- name: Count activation keys
  ansible.builtin.debug:
    msg: "Total activation keys: {{ key_list.activation_keys | length }}"

- name: Get activation key details by ID
  goldyfruit.mlm.activationkey_info:
    url: https://suma.example.com
    username: admin
    password: admin
    key_id: 42
  register: key_details

- name: Get activation key details by name
  goldyfruit.mlm.activationkey_info:
    url: https://suma.example.com
    username: admin
    password: admin
    key_name: "sles-15-key"
  register: key_details

- name: Display activation key details
  ansible.builtin.debug:
    msg: "{{ key_details.activation_key }}"

- name: List activation keys for specific organization
  goldyfruit.mlm.activationkey_info:
    url: https://suma.example.com
    username: admin
    password: admin
    org_id: 1
  register: org_keys
"""

RETURN = r"""
activation_keys:
  description: List of all activation keys.
  returned: when neither key_id nor key_name is provided
  type: list
  elements: dict
  contains:
    id:
      description: Activation key ID.
      type: int
      sample: 42
    key:
      description: Activation key name.
      type: str
      sample: "sles-15-key"
    description:
      description: Activation key description.
      type: str
      sample: "Key for SLES 15 systems"
    base_channel_label:
      description: Base channel label for the activation key.
      type: str
      sample: "sles15-sp4-pool-x86_64"
    usage_limit:
      description: Usage limit for the activation key (0 = unlimited).
      type: int
      sample: 100
    system_count:
      description: Number of systems currently using this activation key.
      type: int
      sample: 5
    disabled:
      description: Whether the activation key is disabled.
      type: bool
      sample: false
    contact_method:
      description: Contact method for systems using this key.
      type: str
      sample: "default"
    universal_default:
      description: Whether this is a universal default activation key.
      type: bool
      sample: false
    child_channel_labels:
      description: List of child channel labels associated with the activation key.
      type: list
      elements: str
      sample: ["sles15-sp4-updates-x86_64", "sles15-sp4-installer-updates-x86_64"]
    server_group_names:
      description: List of server group names associated with the activation key.
      type: list
      elements: str
      sample: ["Production Servers", "Web Servers"]
    packages:
      description: List of packages associated with the activation key.
      type: list
      elements: str
      sample: ["vim", "htop", "curl"]
    config_channels:
      description: List of configuration channels associated with the activation key.
      type: list
      elements: str
      sample: ["config-channel-1", "config-channel-2"]
activation_key:
  description: Detailed information about the specified activation key.
  returned: when either key_id or key_name is provided
  type: dict
  contains:
    id:
      description: Activation key ID.
      type: int
      sample: 42
    key:
      description: Activation key name.
      type: str
      sample: "sles-15-key"
    description:
      description: Activation key description.
      type: str
      sample: "Key for SLES 15 systems"
    base_channel_label:
      description: Base channel label for the activation key.
      type: str
      sample: "sles15-sp4-pool-x86_64"
    usage_limit:
      description: Usage limit for the activation key (0 = unlimited).
      type: int
      sample: 100
    system_count:
      description: Number of systems currently using this activation key.
      type: int
      sample: 5
    disabled:
      description: Whether the activation key is disabled.
      type: bool
      sample: false
    contact_method:
      description: Contact method for systems using this key.
      type: str
      sample: "default"
    universal_default:
      description: Whether this is a universal default activation key.
      type: bool
      sample: false
    child_channel_labels:
      description: List of child channel labels associated with the activation key.
      type: list
      elements: str
      sample: ["sles15-sp4-updates-x86_64", "sles15-sp4-installer-updates-x86_64"]
    server_group_names:
      description: List of server group names associated with the activation key.
      type: list
      elements: str
      sample: ["Production Servers", "Web Servers"]
    packages:
      description: List of packages associated with the activation key.
      type: list
      elements: str
      sample: ["vim", "htop", "curl"]
    config_channels:
      description: List of configuration channels associated with the activation key.
      type: list
      elements: str
      sample: ["config-channel-1", "config-channel-2"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_activationkey_utils import (
    list_activation_keys,
    get_activation_key_details,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Extracts and validates the required parameters
    3. Creates the MLM client and logs in to the API
    4. Determines whether to retrieve a specific activation key's details or list all activation keys
    5. Returns the result to Ansible
    6. Ensures proper logout from the API

    The module supports check mode, though it doesn't make any changes to the system
    as it's an information-gathering module.

    If neither key_id nor key_name is provided, the module will list all activation keys.
    If either key_id or key_name is provided, the module will return detailed information
    about that specific activation key. If both are provided, key_id takes precedence.
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        key_id=dict(type="int", required=False),
        key_name=dict(type="str", required=False),
        org_id=dict(type="int", required=False),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Extract module parameters
    key_id = module.params.get("key_id")
    key_name = module.params.get("key_name")
    org_id = module.params.get("org_id")

    # Create the MLM client (it will handle parameter validation and credentials loading)
    try:
        client = MLMClient(module)
    except Exception as e:
        module.fail_json(msg="Failed to initialize MLM client: {}".format(str(e)))

    login_success = False
    try:
        # Login to the API
        try:
            client.login()
            login_success = True
        except Exception as e:
            module.fail_json(msg="Failed to login to MLM API: {}".format(str(e)))

        # Determine what information to retrieve
        try:
            if key_id is not None or key_name is not None:
                # Get details for a specific activation key
                key_details = get_activation_key_details(client, key_id, key_name)
                module.exit_json(changed=False, activation_key=key_details)
            else:
                # List all activation keys
                activation_keys = list_activation_keys(client, org_id)
                module.exit_json(changed=False, activation_keys=activation_keys)
        except Exception as e:
            module.fail_json(
                msg="Failed to retrieve activation key information: {}".format(str(e))
            )
    except Exception as e:
        module.fail_json(msg="Unexpected error: {}".format(str(e)))
    finally:
        # Logout from the API only if login was successful
        if login_success:
            try:
                client.logout()
            except Exception:
                # Ignore logout errors
                pass


if __name__ == "__main__":
    main()
