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
module: user
short_description: Manage users in SUSE Multi-Linux Manager
description:
  - Create, delete, enable, disable, and update users in SUSE Multi-Linux Manager.
  - This module uses the SUSE Multi-Linux Manager API to manage users.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  login:
    description:
      - User login name.
      - Required for all operations.
    type: str
    required: true
  password:
    description:
      - User password.
      - Required when state=present or when updating password.
    type: str
    required: false
    no_log: true
  first_name:
    description:
      - User's first name.
      - Required when state=present.
    type: str
    required: false
  last_name:
    description:
      - User's last name.
      - Required when state=present.
    type: str
    required: false
  email:
    description:
      - User's email address.
      - Required when state=present.
    type: str
    required: false
  prefix:
    description:
      - User's prefix (e.g., Dr., Mr., Mrs., Ms., Sr.).
      - Must match one of the values available in the web UI.
      - Note: This parameter is not supported during user creation and will be ignored. Use update operations to set the prefix after creation.
    type: str
    required: false
  use_pam_auth:
    description:
      - Whether to use PAM authentication for the user.
    type: bool
    default: false
  state:
    description:
      - Whether the user should exist or not.
      - When C(present), the user will be created if it doesn't exist or updated if it does.
      - When C(absent), the user will be deleted if it exists.
      - When C(enabled), the user will be enabled if it exists.
      - When C(disabled), the user will be disabled if it exists.
    type: str
    choices: [ present, absent, enabled, disabled ]
    default: present
  role:
    description:
      - Role to add or remove from the user.
      - Used when role_state is specified.
      - Valid roles include C(satellite_admin), C(org_admin), C(channel_admin), C(config_admin), C(system_group_admin), C(activation_key_admin), C(image_admin).
      - The available roles may vary depending on your SUSE Multi-Linux Manager configuration and user permissions.
    type: str
    required: false
  role_state:
    description:
      - Whether the role should be present or absent for the user.
      - When C(present), the role will be added to the user.
      - When C(absent), the role will be removed from the user.
      - Requires the 'role' parameter to be specified.
    type: str
    choices: [ present, absent ]
    required: false
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to manage users.
  - When deleting a user, all associated data will be removed.
  - Role management can be done in the same task as user management.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Create a new user
- name: Create a new user
  goldyfruit.mlm.user:
    login: "jdoe"
    password: "{{ vault_user_password }}"
    first_name: "John"
    last_name: "Doe"
    email: "john.doe@example.com"
    prefix: "Mr."
    state: present

# Create a user with PAM authentication
- name: Create a PAM user
  goldyfruit.mlm.user:
    login: "pamuser"
    password: "{{ vault_pam_password }}"
    first_name: "PAM"
    last_name: "User"
    email: "pam.user@example.com"
    use_pam_auth: true
    state: present

# Update user details
- name: Update user information
  goldyfruit.mlm.user:
    login: "jdoe"
    first_name: "Jane"
    last_name: "Smith"
    email: "jane.smith@example.com"
    prefix: "Ms."
    state: present

# Enable a user
- name: Enable user
  goldyfruit.mlm.user:
    login: "jdoe"
    state: enabled

# Disable a user
- name: Disable user
  goldyfruit.mlm.user:
    login: "jdoe"
    state: disabled

# Delete a user
- name: Delete user
  goldyfruit.mlm.user:
    login: "jdoe"
    state: absent

# Create user and add role
- name: Create user with role
  goldyfruit.mlm.user:
    login: "admin_user"
    password: "{{ vault_admin_password }}"
    first_name: "Admin"
    last_name: "User"
    email: "admin@example.com"
    state: present
    role: "org_admin"
    role_state: present

# Remove role from user
- name: Remove role from user
  goldyfruit.mlm.user:
    login: "admin_user"
    role: "org_admin"
    role_state: absent
"""

RETURN = r"""
user:
  description: Information about the user.
  returned: when state=present, enabled, or disabled and user exists
  type: dict
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
      sample: ["org_admin", "channel_admin"]
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
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "User 'jdoe' created successfully"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_user_utils import (
    get_user_by_login,
    create_user,
    delete_user,
    enable_user,
    disable_user,
    update_user_details,
    add_user_role,
    remove_user_role,
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
        login=dict(type="str", required=True),
        password=dict(type="str", required=False, no_log=True),
        first_name=dict(type="str", required=False),
        last_name=dict(type="str", required=False),
        email=dict(type="str", required=False),
        prefix=dict(type="str", required=False),
        use_pam_auth=dict(type="bool", default=False),
        state=dict(type="str", default="present", choices=["present", "absent", "enabled", "disabled"]),
        role=dict(type="str", required=False),
        role_state=dict(type="str", choices=["present", "absent"], required=False),
    )

    # Define required arguments based on state
    required_if = [
        ["role_state", "present", ["role"]],
        ["role_state", "absent", ["role"]],
    ]

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
    )

    # Validate role_state parameter
    if module.params.get("role_state") and not module.params.get("role"):
        module.fail_json(msg="role parameter is required when role_state is specified")

    # Create the MLM client
    client = MLMClient(module)

    # Login to the API
    client.login()

    try:
        # Determine what to do based on the state
        state = module.params["state"]
        role_state = module.params.get("role_state")

        # Handle user state first
        if state == "present":
            # Check if user exists for update vs create
            existing_user = get_user_by_login(client, module.params["login"])
            if existing_user:
                # User exists, update if needed
                if any([
                    module.params.get("first_name"),
                    module.params.get("last_name"),
                    module.params.get("email"),
                    module.params.get("prefix"),
                    module.params.get("password"),
                ]):
                    changed, result, msg = update_user_details(module, client)
                else:
                    # No updates needed
                    changed, result, msg = False, existing_user, "User '{}' already exists".format(module.params['login'])
            else:
                # User doesn't exist, validate required fields for creation
                missing_fields = []
                if not module.params.get("first_name"):
                    missing_fields.append("first_name")
                if not module.params.get("last_name"):
                    missing_fields.append("last_name")
                if not module.params.get("email"):
                    missing_fields.append("email")
                if not module.params.get("password"):
                    missing_fields.append("password")

                if missing_fields:
                    module.fail_json(msg="Creating a new user requires the following parameters: {}".format(", ".join(missing_fields)))

                # User doesn't exist, create it
                changed, result, msg = create_user(module, client)
        elif state == "absent":
            changed, result, msg = delete_user(module, client)
        elif state == "enabled":
            changed, result, msg = enable_user(module, client)
        elif state == "disabled":
            changed, result, msg = disable_user(module, client)
        else:
            module.fail_json(msg="Invalid state: {}".format(state))

        # Handle role management if specified
        if role_state == "present":
            role_changed, role_result, role_msg = add_user_role(module, client)
            if role_changed:
                changed = True
                msg += "; {}".format(role_msg)
        elif role_state == "absent":
            role_changed, role_result, role_msg = remove_user_role(module, client)
            if role_changed:
                changed = True
                msg += "; {}".format(role_msg)

        # Return the result
        if result:
            module.exit_json(changed=changed, msg=msg, user=result)
        else:
            module.exit_json(changed=changed, msg=msg)
    except Exception as e:
        module.fail_json(msg="Failed to manage user: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == "__main__":
    main()
