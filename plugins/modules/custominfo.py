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

from typing import Any, Tuple, Dict, Optional

DOCUMENTATION = r"""
---
module: custominfo
short_description: Manage custom system information in SUSE Multi-Linux Manager
description:
  - Create, update, or delete custom information keys in SUSE Multi-Linux Manager.
  - Set custom information values for systems.
  - This module uses the SUSE Multi-Linux Manager API to manage custom system information.
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
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
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
- name: Create a new custom information key using credentials file
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

- name: Create custom information key using specific instance
  goldyfruit.mlm.custominfo:
    instance: staging  # Use staging instance from credentials file
    key_label: "STAGING_TAG"
    description: "Asset tag for staging environment"
    state: present

# Using environment variables
- name: Create custom information key using environment variables
  goldyfruit.mlm.custominfo:
    key_label: "PRODUCTION_TAG"
    description: "Asset tag for production environment"
    state: present
  environment:
    MLM_URL: "https://mlm.example.com"
    MLM_USERNAME: "admin"
    MLM_PASSWORD: "{{ vault_mlm_password }}"

- name: Set a custom value for a system
  goldyfruit.mlm.custominfo:
    key_label: "INVENTORY_TAG"
    system_id: 1000010000
    value: "A12345"
    state: value
  register: value_result

- name: Set custom values for multiple systems
  goldyfruit.mlm.custominfo:
    key_label: "INVENTORY_TAG"
    system_id: "{{ item.id }}"
    value: "{{ item.tag }}"
    state: value
  loop:
    - { id: 1000010000, tag: "A12345" }
    - { id: 1000010001, tag: "B67890" }
    - { id: 1000010002, tag: "C24680" }
  register: batch_value_results

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
    create_or_update_custom_key,
    delete_custom_key_module,
    set_custom_value_module,
)


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
            changed, result, msg = create_or_update_custom_key(module, client)
        elif state == "absent":
            changed, result, msg = delete_custom_key_module(module, client)
        else:  # state == 'value'
            changed, result, msg = set_custom_value_module(module, client)

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
