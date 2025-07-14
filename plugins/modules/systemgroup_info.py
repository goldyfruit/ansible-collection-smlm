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

from typing import Any

DOCUMENTATION = r"""
---
module: systemgroup_info
short_description: Get information about system groups in SUSE Multi-Linux Manager
description:
  - Get information about system groups in SUSE Multi-Linux Manager.
  - If no system group identifier is provided, lists all system groups.
  - If a system group ID or name is provided, returns detailed information about that specific system group.
  - This module uses the SUSE Multi-Linux Manager API to retrieve system group information.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  group_id:
    description:
      - ID of the system group to get details for.
      - If provided, returns detailed information about this specific system group.
      - If both group_id and group_name are provided, group_id takes precedence.
    type: int
    required: false
  group_name:
    description:
      - Name of the system group to get details for.
      - If provided, returns detailed information about this specific system group.
    type: str
    required: false
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to view system group information.
  - If neither group_id nor group_name is provided, the module will list all system groups.
  - If either group_id or group_name is provided, the module will return detailed information about that specific system group.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
- name: List all system groups
  goldyfruit.mlm.systemgroup_info:
  register: group_list

- name: Display system group names
  ansible.builtin.debug:
    msg: "{{ group_list.system_groups | map(attribute='name') | list }}"

- name: Count system groups
  ansible.builtin.debug:
    msg: "Total system groups: {{ group_list.system_groups | length }}"

- name: Get system group details by ID
  goldyfruit.mlm.systemgroup_info:
    group_id: 42
  register: group_details

- name: Get system group details by name
  goldyfruit.mlm.systemgroup_info:
    group_name: "Production Servers"
  register: group_details

- name: Display system group details
  ansible.builtin.debug:
    msg: "{{ group_details.system_group }}"

- name: List system groups using specific instance
  goldyfruit.mlm.systemgroup_info:
    instance: staging
  register: staging_groups
"""

RETURN = r"""
system_groups:
  description: List of all system groups.
  returned: when neither group_id nor group_name is provided
  type: list
  elements: dict
  contains:
    id:
      description: System group ID.
      type: int
      sample: 42
    name:
      description: System group name.
      type: str
      sample: "Production Servers"
    description:
      description: System group description.
      type: str
      sample: "Production web servers"
    org_id:
      description: Organization ID that owns the system group.
      type: int
      sample: 1
    system_count:
      description: Number of systems in the group.
      type: int
      sample: 5
system_group:
  description: Detailed information about the specified system group.
  returned: when either group_id or group_name is provided
  type: dict
  contains:
    id:
      description: System group ID.
      type: int
      sample: 42
    name:
      description: System group name.
      type: str
      sample: "Production Servers"
    description:
      description: System group description.
      type: str
      sample: "Production web servers"
    org_id:
      description: Organization ID that owns the system group.
      type: int
      sample: 1
    system_count:
      description: Number of systems in the group.
      type: int
      sample: 5
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_systemgroup_utils import (
    list_systemgroups,
    get_systemgroup_details,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Extracts and validates the required parameters
    3. Creates the MLM client and logs in to the API
    4. Determines whether to retrieve a specific system group's details or list all system groups
    5. Returns the result to Ansible
    6. Ensures proper logout from the API

    The module supports check mode, though it doesn't make any changes to the system
    as it's an information-gathering module.

    If neither group_id nor group_name is provided, the module will list all system groups.
    If either group_id or group_name is provided, the module will return detailed information
    about that specific system group. If both are provided, group_id takes precedence.
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        group_id=dict(type="int", required=False),
        group_name=dict(type="str", required=False),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Extract module parameters
    group_id = module.params.get("group_id")
    group_name = module.params.get("group_name")

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
            if group_id is not None or group_name is not None:
                # Get details for a specific system group
                group_details = get_systemgroup_details(client, group_id, group_name)
                module.exit_json(changed=False, system_group=group_details)
            else:
                # List all system groups
                system_groups = list_systemgroups(client)
                module.exit_json(changed=False, system_groups=system_groups)
        except Exception as e:
            module.fail_json(
                msg="Failed to retrieve system group information: {}".format(str(e))
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
