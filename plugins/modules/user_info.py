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
module: user_info
short_description: Retrieve information about users in SUSE Multi-Linux Manager
description:
  - Retrieve information about users in SUSE Multi-Linux Manager.
  - This module uses the SUSE Multi-Linux Manager API to fetch user information.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  login:
    description:
      - User login name to retrieve information for.
      - If not specified, information for all users will be retrieved.
    type: str
    required: false
  details:
    description:
      - Whether to retrieve detailed information about the user.
      - Only applicable when login is specified.
    type: bool
    default: false
  roles:
    description:
      - Whether to include role information in the output.
      - Only applicable when login is specified.
    type: bool
    default: false
  system_groups:
    description:
      - Whether to include system group information in the output.
      - Only applicable when login is specified.
    type: bool
    default: false
  assignable_roles:
    description:
      - Whether to retrieve the list of assignable roles.
      - This is a global setting and not user-specific.
    type: bool
    default: false
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to view user information.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Get information about all users
- name: List all users
  goldyfruit.mlm.user_info:
  register: all_users

- name: Display user count
  ansible.builtin.debug:
    msg: "Total users: {{ all_users.users | length }}"

# Get basic information about a specific user
- name: Get basic user information
  goldyfruit.mlm.user_info:
    login: "jdoe"
  register: user_info

- name: Display user details
  ansible.builtin.debug:
    msg: "User {{ user_info.users[0].login }} is {{ 'enabled' if user_info.users[0].enabled else 'disabled' }}"

# Get detailed information about a specific user
- name: Get detailed user information
  goldyfruit.mlm.user_info:
    login: "jdoe"
    details: true
  register: detailed_user_info

# Get user information with roles
- name: Get user information including roles
  goldyfruit.mlm.user_info:
    login: "jdoe"
    roles: true
  register: user_with_roles

- name: Display user roles
  ansible.builtin.debug:
    msg: "User {{ user_with_roles.users[0].login }} has roles: {{ user_with_roles.user_roles }}"

# Get user information with system groups
- name: Get user information including system groups
  goldyfruit.mlm.user_info:
    login: "jdoe"
    system_groups: true
  register: user_with_groups

- name: Display user system groups
  ansible.builtin.debug:
    msg: "User assigned system groups: {{ user_with_groups.assigned_system_groups | length }}"

# Get comprehensive user information
- name: Get comprehensive user information
  goldyfruit.mlm.user_info:
    login: "jdoe"
    details: true
    roles: true
    system_groups: true
  register: comprehensive_user_info

# Get list of assignable roles
- name: Get assignable roles
  goldyfruit.mlm.user_info:
    assignable_roles: true
  register: assignable_roles_info

- name: Display assignable roles
  ansible.builtin.debug:
    msg: "Assignable roles: {{ assignable_roles_info.assignable_roles }}"
"""

RETURN = r"""
users:
  description: List of users.
  returned: always
  type: list
  elements: dict
  contains:
    id:
      description: User ID.
      type: int
      sample: 123
    login:
      description: User login name.
      type: str
      sample: "jdoe"
    login_uc:
      description: User login name in uppercase.
      type: str
      sample: "JDOE"
    enabled:
      description: Whether the user is enabled.
      type: bool
      sample: true
    first_name:
      description: User's first name.
      type: str
      sample: "John"
    last_name:
      description: User's last name.
      type: str
      sample: "Doe"
    email:
      description: User's email address.
      type: str
      sample: "john.doe@example.com"
    prefix:
      description: User's prefix.
      type: str
      sample: "Mr."
    last_login_date:
      description: Last login date.
      type: str
      sample: "2025-01-01T00:00:00Z"
    created_date:
      description: User creation date.
      type: str
      sample: "2025-01-01T00:00:00Z"
    role_labels:
      description: List of role labels assigned to the user.
      type: list
      sample: ["organization_admin", "channel_admin"]
    use_pam_authentication:
      description: Whether the user uses PAM authentication.
      type: bool
      sample: false
    read_only:
      description: Whether the user is read-only.
      type: bool
      sample: false
    errata_notifications:
      description: Whether errata notifications are enabled.
      type: bool
      sample: false
user_roles:
  description: List of roles assigned to the user.
  returned: when login is specified and roles=true
  type: list
  elements: str
  sample: ["organization_admin", "channel_admin"]
assigned_system_groups:
  description: List of system groups assigned to the user.
  returned: when login is specified and system_groups=true
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
      sample: "Web Servers"
    description:
      description: System group description.
      type: str
      sample: "All web server systems"
    system_count:
      description: Number of systems in the group.
      type: int
      sample: 10
    org_id:
      description: Organization ID for this system group.
      type: int
      sample: 1
default_system_groups:
  description: List of default system groups for the user.
  returned: when login is specified and system_groups=true
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
      sample: "Web Servers"
    description:
      description: System group description.
      type: str
      sample: "All web server systems"
    system_count:
      description: Number of systems in the group.
      type: int
      sample: 10
    org_id:
      description: Organization ID for this system group.
      type: int
      sample: 1
assignable_roles:
  description: List of roles that can be assigned to users.
  returned: when assignable_roles=true
  type: list
  elements: str
  sample: ["organization_admin", "channel_admin", "system_group_admin"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_user_utils import (
    list_users,
    get_user_by_login,
    get_user_details,
    list_user_roles,
    list_assignable_roles,
    list_user_assigned_system_groups,
    list_user_default_system_groups,
    standardize_user_data,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Creates the MLM client and logs in to the API
    3. Retrieves user information based on the specified parameters
    4. Returns the result to Ansible
    5. Ensures proper logout from the API
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        login=dict(type="str", required=False),
        details=dict(type="bool", default=False),
        roles=dict(type="bool", default=False),
        system_groups=dict(type="bool", default=False),
        assignable_roles=dict(type="bool", default=False),
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
        result = {}

        # Get user information
        login = module.params.get("login")

        if login:
            # Get specific user information
            if module.params["details"]:
                # Get detailed user information
                user_details = get_user_details(client, login)
                if user_details:
                    result["users"] = [user_details]
                else:
                    result["users"] = []
            else:
                # Get basic user information
                user = get_user_by_login(client, login)
                if user:
                    result["users"] = [standardize_user_data(user)]
                else:
                    result["users"] = []

            # Get user roles if requested
            if module.params["roles"] and login:
                try:
                    user_roles = list_user_roles(client, login)
                    result["user_roles"] = user_roles
                except Exception as e:
                    module.warn("Failed to get user roles: {}".format(str(e)))
                    result["user_roles"] = []

            # Get user system groups if requested
            if module.params["system_groups"] and login:
                try:
                    assigned_groups = list_user_assigned_system_groups(client, login)
                    result["assigned_system_groups"] = assigned_groups
                except Exception as e:
                    module.warn("Failed to get assigned system groups: {}".format(str(e)))
                    result["assigned_system_groups"] = []

                try:
                    default_groups = list_user_default_system_groups(client, login)
                    result["default_system_groups"] = default_groups
                except Exception as e:
                    module.warn("Failed to get default system groups: {}".format(str(e)))
                    result["default_system_groups"] = []
        else:
            # Get all users
            try:
                users = list_users(client)
                result["users"] = users
            except Exception as e:
                module.fail_json(msg="Failed to list users: {}".format(str(e)))

        # Get assignable roles if requested
        if module.params["assignable_roles"]:
            try:
                assignable_roles = list_assignable_roles(client)
                result["assignable_roles"] = assignable_roles
            except Exception as e:
                module.warn("Failed to get assignable roles: {}".format(str(e)))
                result["assignable_roles"] = []

        # Return the result
        module.exit_json(changed=False, **result)

    except Exception as e:
        module.fail_json(msg="Failed to retrieve user information: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == "__main__":
    main()
