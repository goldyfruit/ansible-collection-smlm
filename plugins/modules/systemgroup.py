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
module: systemgroup
short_description: Manage system groups in SUSE Multi-Linux Manager
description:
  - Create, update, or delete system groups in SUSE Multi-Linux Manager.
  - Manage systems and administrators associated with system groups.
  - This module uses the SUSE Multi-Linux Manager API to manage system groups.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  name:
    description:
      - Name of the system group.
      - Required for all operations.
    type: str
    required: true
  state:
    description:
      - Whether the system group should exist or not.
      - When C(present), the system group will be created if it doesn't exist or updated if it does.
      - When C(absent), the system group will be deleted if it exists.
    type: str
    choices: [ present, absent ]
    default: present
  description:
    description:
      - Description of the system group.
      - Only used when state=present.
    type: str
    required: false
  systems:
    description:
      - List of system IDs to associate with the system group.
      - Only used when state=present and system_state is specified.
    type: list
    elements: int
    required: false
  system_state:
    description:
      - Whether systems should be present or absent in the group.
      - Only applies when systems is specified.
    type: str
    choices: [ present, absent ]
    default: present
  administrators:
    description:
      - List of user login names to manage the system group.
      - Only used when state=present and admin_state is specified.
    type: list
    elements: str
    required: false
  admin_state:
    description:
      - Whether administrators should be present or absent.
      - Only applies when administrators is specified.
    type: str
    choices: [ present, absent ]
    default: present
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to manage system groups.
  - When deleting a system group, all associated configurations will be removed.
  - Deleting a system group is a destructive operation and cannot be undone.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Using credentials configuration file (recommended)
- name: Create a new system group using credentials file
  goldyfruit.mlm.systemgroup:
    name: "Production Servers"
    description: "Production web servers"
    state: present
  register: group_result

- name: Create system group using specific instance
  goldyfruit.mlm.systemgroup:
    instance: staging  # Use staging instance from credentials file
    name: "Staging Servers"
    description: "Staging environment servers"
    state: present

- name: Update system group description
  goldyfruit.mlm.systemgroup:
    name: "Production Servers"
    description: "Updated production web servers"
    state: present

- name: Add systems to system group
  goldyfruit.mlm.systemgroup:
    name: "Production Servers"
    systems:
      - 1001
      - 1002
      - 1003
    system_state: present
    state: present

- name: Remove systems from system group
  goldyfruit.mlm.systemgroup:
    name: "Production Servers"
    systems:
      - 1003
    system_state: absent
    state: present

- name: Add administrators to system group
  goldyfruit.mlm.systemgroup:
    name: "Production Servers"
    administrators:
      - "admin1"
      - "admin2"
    admin_state: present
    state: present

- name: Remove administrators from system group
  goldyfruit.mlm.systemgroup:
    name: "Production Servers"
    administrators:
      - "admin2"
    admin_state: absent
    state: present

- name: Create system group with systems and administrators
  goldyfruit.mlm.systemgroup:
    name: "Web Servers"
    description: "Web server group"
    systems:
      - 2001
      - 2002
    system_state: present
    administrators:
      - "webadmin"
    admin_state: present
    state: present

- name: Delete a system group
  goldyfruit.mlm.systemgroup:
    name: "Old Servers"
    state: absent
"""

RETURN = r"""
system_group:
  description: Information about the managed system group.
  returned: when state=present and the system group exists or was created
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
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "System group 'Production Servers' created successfully"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_systemgroup_utils import (
    create_systemgroup,
    update_systemgroup,
    delete_systemgroup,
    manage_systemgroup_systems,
    manage_systemgroup_administrators,
    get_systemgroup_by_name,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Creates the MLM client and logs in to the API
    3. Determines the action to take based on the 'state' parameter
    4. Calls the appropriate function to perform the action
    5. Returns the result to Ansible
    6. Ensures proper logout from the API

    The module supports check mode, which allows for dry runs without making
    actual changes to the system.
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        description=dict(type="str", required=False),
        systems=dict(type="list", elements="int", required=False),
        system_state=dict(type="str", default="present", choices=["present", "absent"]),
        administrators=dict(type="list", elements="str", required=False),
        admin_state=dict(type="str", default="present", choices=["present", "absent"]),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Create the MLM client
    client = MLMClient(module)

    # Login to the API
    client.login()

    try:
        # Determine what to do based on the state
        state = module.params["state"]
        group_name = module.params["name"]

        if state == "present":
            # Step 1: Ensure the system group exists
            existing_group = get_systemgroup_by_name(client, group_name)

            if existing_group:
                # Group exists - check if update is needed
                changed, result, msg = update_systemgroup(module, client)
            else:
                # Group doesn't exist - create it
                changed, result, msg = create_systemgroup(module, client)

            # Step 2: Manage systems if specified
            if module.params.get("systems"):
                sys_changed, sys_result, sys_msg = manage_systemgroup_systems(
                    module, client
                )
                if sys_changed:
                    changed = True
                    msg += " {}".format(sys_msg)

            # Step 3: Manage administrators if specified
            if module.params.get("administrators"):
                admin_changed, admin_result, admin_msg = (
                    manage_systemgroup_administrators(module, client)
                )
                if admin_changed:
                    changed = True
                    msg += " {}".format(admin_msg)

            # Step 4: Get the final state of the system group
            final_result = get_systemgroup_by_name(client, group_name)
            if not final_result:
                # Fallback to the result from create/update if we can't fetch the group
                final_result = result

            module.exit_json(changed=changed, msg=msg, system_group=final_result)

        else:  # state == 'absent'
            changed, result, msg = delete_systemgroup(module, client)
            module.exit_json(changed=changed, msg=msg)

    except Exception as e:
        module.fail_json(msg="Failed to manage system group: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == "__main__":
    main()
