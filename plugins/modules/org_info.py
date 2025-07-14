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
module: org_info
short_description: Get information about organizations in SUSE Multi-Linux Manager
description:
  - Get information about organizations in SUSE Multi-Linux Manager.
  - If no organization identifier is provided, lists all organizations.
  - If an organization ID or name is provided, returns detailed information about that specific organization.
  - This module uses the SUSE Multi-Linux Manager API to retrieve organization information.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  org_id:
    description:
      - ID of the organization to get details for.
      - If provided, returns detailed information about this specific organization.
      - If both org_id and org_name are provided, org_id takes precedence.
    type: int
    required: false
  org_name:
    description:
      - Name of the organization to get details for.
      - If provided, returns detailed information about this specific organization.
    type: str
    required: false
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to view organization information.
  - If neither org_id nor org_name is provided, the module will list all organizations.
  - If either org_id or org_name is provided, the module will return detailed information about that specific organization.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Using credentials configuration file (recommended)
- name: List all organizations
  goldyfruit.mlm.org_info:
  register: org_list

- name: Display organization names
  ansible.builtin.debug:
    msg: "{{ org_list.organizations | map(attribute='name') | list }}"

- name: Count organizations
  ansible.builtin.debug:
    msg: "Total organizations: {{ org_list.organizations | length }}"

- name: Get organization details by ID
  goldyfruit.mlm.org_info:
    org_id: 42
  register: org_details

- name: Get organization details by name
  goldyfruit.mlm.org_info:
    org_name: "Engineering"
  register: org_details

- name: Get organization details using specific instance
  goldyfruit.mlm.org_info:
    instance: staging  # Use staging instance from credentials file
    org_name: "Engineering"
  register: org_details

- name: Display organization details
  ansible.builtin.debug:
    msg: "{{ org_details.organization }}"
"""

RETURN = r"""
organizations:
  description: List of all organizations.
  returned: when neither org_id nor org_name is provided
  type: list
  elements: dict
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
      sample: 5
    systems:
      description: Number of systems in the organization.
      type: int
      sample: 10
    trusts:
      description: Number of trusted organizations.
      type: int
      sample: 2
    system_groups:
      description: Number of system groups in the organization.
      type: int
      sample: 3
    activation_keys:
      description: Number of activation keys in the organization.
      type: int
      sample: 5
    kickstart_profiles:
      description: Number of kickstart profiles in the organization.
      type: int
      sample: 2
    configuration_channels:
      description: Number of configuration channels in the organization.
      type: int
      sample: 4
    staging_content_enabled:
      description: Whether staging content is enabled in the organization.
      type: bool
      sample: false
organization:
  description: Detailed information about the specified organization.
  returned: when either org_id or org_name is provided
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
      sample: 5
    systems:
      description: Number of systems in the organization.
      type: int
      sample: 10
    trusts:
      description: Number of trusted organizations.
      type: int
      sample: 2
    system_groups:
      description: Number of system groups in the organization.
      type: int
      sample: 3
    activation_keys:
      description: Number of activation keys in the organization.
      type: int
      sample: 5
    kickstart_profiles:
      description: Number of kickstart profiles in the organization.
      type: int
      sample: 2
    configuration_channels:
      description: Number of configuration channels in the organization.
      type: int
      sample: 4
    staging_content_enabled:
      description: Whether staging content is enabled in the organization.
      type: bool
      sample: false
"""

import os
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_org_utils import (
    standardize_org_data,
    list_organizations,
    get_organization_details,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Extracts and validates the required parameters
    3. Creates the MLM client and logs in to the API
    4. Determines whether to retrieve a specific organization's details or list all organizations
    5. Returns the result to Ansible
    6. Ensures proper logout from the API

    The module supports check mode, though it doesn't make any changes to the system
    as it's an information-gathering module.

    If neither org_id nor org_name is provided, the module will list all organizations.
    If either org_id or org_name is provided, the module will return detailed information
    about that specific organization. If both are provided, org_id takes precedence.
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        org_id=dict(type="int", required=False),
        org_name=dict(type="str", required=False),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Extract module parameters
    org_id = module.params.get("org_id")
    org_name = module.params.get("org_name")

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
            if org_id is not None or org_name is not None:
                # Get details for a specific organization
                org_details = get_organization_details(client, org_id, org_name)
                module.exit_json(changed=False, organization=org_details)
            else:
                # List all organizations
                organizations = list_organizations(client)
                module.exit_json(changed=False, organizations=organizations)
        except Exception as e:
            module.fail_json(
                msg="Failed to retrieve organization information: {}".format(str(e))
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
