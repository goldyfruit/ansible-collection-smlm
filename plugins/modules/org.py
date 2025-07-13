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
module: org
short_description: Manage organizations in SUSE Manager
description:
  - Create or delete organizations in SUSE Manager.
  - This module uses the SUSE Manager API to manage organizations.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  org_name:
    description:
      - Organization name. Must meet same criteria as in the web UI.
      - Required when state=present or when org_id is not specified.
    type: str
    required: false
  org_id:
    description:
      - ID of the organization to manage.
      - Required when state=absent and org_name is not specified.
    type: int
    required: false
  state:
    description:
      - Whether the organization should exist or not.
      - When C(present), the organization will be created if it doesn't exist.
      - When C(absent), the organization will be deleted if it exists.
    type: str
    choices: [ present, absent ]
    default: present
  admin_login:
    description:
      - New administrator login name.
      - Required when state=present.
    type: str
    required: false
  admin_password:
    description:
      - New administrator password.
      - Required when state=present.
    type: str
    required: false
    no_log: true
  first_name:
    description:
      - New administrator's first name.
      - Required when state=present.
    type: str
    required: false
  last_name:
    description:
      - New administrator's last name.
      - Required when state=present.
    type: str
    required: false
  email:
    description:
      - New administrator's e-mail.
      - Required when state=present.
    type: str
    required: false
  prefix:
    description:
      - New administrator's prefix. Must match one of the values available in the web UI (i.e. Dr., Mr., Mrs., Ms., Sr.).
    type: str
    required: false
  use_pam_auth:
    description:
      - True if PAM authentication should be used for the new administrator account.
    type: bool
    default: false
notes:
  - This module requires the SUSE Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to create or delete organizations.
  - When deleting an organization, all systems, users, and other resources associated with the organization will be deleted.
  - Deleting an organization is a destructive operation and cannot be undone.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Using credentials configuration file (recommended)
- name: Create a new organization using credentials file
  goldyfruit.mlm.org:
    org_name: "Engineering"
    state: present
    admin_login: "eng_admin"
    admin_password: "{{ vault_admin_password }}"
    first_name: "John"
    last_name: "Doe"
    email: "john.doe@example.com"
    prefix: "Mr."
  register: org_result

- name: Display the new organization ID
  ansible.builtin.debug:
    msg: "Organization ID: {{ org_result.organization.id }}"

- name: Create organization using specific instance
  goldyfruit.mlm.org:
    instance: staging  # Use staging instance from credentials file
    org_name: "Staging Engineering"
    state: present
    admin_login: "staging_admin"
    admin_password: "{{ vault_staging_admin_password }}"
    first_name: "Jane"
    last_name: "Smith"
    email: "jane.smith@example.com"
    prefix: "Ms."
  register: staging_org_result

# Using environment variables
- name: Create organization using environment variables
  goldyfruit.mlm.org:
    org_name: "Production Engineering"
    state: present
    admin_login: "prod_admin"
    admin_password: "{{ vault_prod_admin_password }}"
    first_name: "Admin"
    last_name: "User"
    email: "admin@example.com"
    prefix: "Mr."
  environment:
    MLM_URL: "https://mlm.example.com"
    MLM_USERNAME: "admin"
    MLM_PASSWORD: "{{ vault_mlm_password }}"

- name: Create organization with PAM authentication
  goldyfruit.mlm.org:
    org_name: "PAM Organization"
    state: present
    admin_login: "pam_admin"
    admin_password: "{{ vault_pam_password }}"
    first_name: "PAM"
    last_name: "Administrator"
    email: "pam.admin@example.com"
    use_pam_auth: true

- name: Delete an organization by ID
  goldyfruit.mlm.org:
    org_id: 42
    state: absent
  register: delete_result

- name: Delete an organization by name
  goldyfruit.mlm.org:
    org_name: "Engineering"
    state: absent
  register: delete_result
"""

RETURN = r"""
organization:
  description: Information about the created or managed organization.
  returned: when state=present and the organization exists or was created
  type: dict
  contains:
    id:
      description: Organization ID.
      type: int
      sample: 42
    name:
      description: Organization name.
      type: str
      sample: "Engineering"
    active_users:
      description: Number of active users in the organization.
      type: int
      sample: 1
    systems:
      description: Number of systems in the organization.
      type: int
      sample: 0
    trusts:
      description: Number of trusted organizations.
      type: int
      sample: 0
    system_groups:
      description: Number of system groups in the organization.
      type: int
      sample: 0
    activation_keys:
      description: Number of activation keys in the organization.
      type: int
      sample: 0
    kickstart_profiles:
      description: Number of kickstart profiles in the organization.
      type: int
      sample: 0
    configuration_channels:
      description: Number of configuration channels in the organization.
      type: int
      sample: 0
    staging_content_enabled:
      description: Whether staging content is enabled in the organization.
      type: bool
      sample: false
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "Organization 'Engineering' created successfully"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_org_utils import (
    get_organization_by_name,
    get_organization_by_id,
    create_organization,
    delete_organization,
)


# The create_organization function is now imported from mlm_org_utils.py


# The delete_organization function is now imported from mlm_org_utils.py


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
        org_name=dict(type="str", required=False),
        org_id=dict(type="int", required=False),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        admin_login=dict(type="str", required=False),
        admin_password=dict(type="str", required=False, no_log=True),
        first_name=dict(type="str", required=False),
        last_name=dict(type="str", required=False),
        email=dict(type="str", required=False),
        prefix=dict(type="str", required=False),
        use_pam_auth=dict(type="bool", default=False),
    )

    # Define required arguments based on state
    required_if = [
        [
            "state",
            "present",
            [
                "org_name",
                "admin_login",
                "admin_password",
                "first_name",
                "last_name",
                "email",
            ],
        ],
    ]

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
        required_one_of=[["org_name", "org_id"]],
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
            changed, result, msg = create_organization(module, client)
        else:  # state == 'absent'
            changed, result, msg = delete_organization(module, client)

        # Return the result
        if result:
            module.exit_json(changed=changed, msg=msg, organization=result)
        else:
            module.exit_json(changed=changed, msg=msg)
    except Exception as e:
        module.fail_json(msg="Failed to manage organization: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == "__main__":
    main()
