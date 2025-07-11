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
module: org_update
short_description: Update the name of an organization in SUSE Manager
description:
  - Update the name of an organization in SUSE Manager.
  - This module uses the SUSE Manager API to update organization names.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  org_id:
    description:
      - ID of the organization to update.
    type: int
    required: true
  name:
    description:
      - New name for the organization.
      - Must meet same criteria as in the web UI.
    type: str
    required: true
notes:
  - This module requires the SUSE Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to update organizations.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Using credentials configuration file (recommended)
- name: Update organization name
  goldyfruit.mlm.org_update:
    org_id: 42
    name: "New Engineering Department"
  register: update_result

- name: Update organization using specific instance
  goldyfruit.mlm.org_update:
    instance: staging  # Use staging instance from credentials file
    org_id: 42
    name: "New Staging Engineering Department"
  register: update_result

- name: Display updated organization
  ansible.builtin.debug:
    msg: "{{ update_result.organization }}"
"""

RETURN = r"""
organization:
  description: Updated organization information.
  returned: success
  type: dict
  contains:
    id:
      description: Organization ID.
      type: int
      sample: 42
    name:
      description: Updated organization name.
      type: str
      sample: "New Engineering Department"
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

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_org_utils import (
    get_organization_details,
    standardize_org_data,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Creates the MLM client and logs in to the API
    3. Checks if the organization exists and retrieves its current name
    4. Determines if a name change is needed (skips if the name is already set to the requested value)
    5. Updates the organization name if needed
    6. Returns the result to Ansible
    7. Ensures proper logout from the API

    The module supports check mode, which allows for dry runs without making
    actual changes to the system.
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        org_id=dict(type="int", required=True),
        name=dict(type="str", required=True),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Create the MLM client
    client = MLMClient(module)

    # Extract module parameters
    org_id = module.params["org_id"]
    new_name = module.params["name"]

    # Check if the organization exists and get current name
    try:
        # Login to the API
        client.login()

        # Get the organization details using the utility function
        try:
            org_details = get_organization_details(client, org_id=org_id)
            if not org_details or "id" not in org_details:
                module.fail_json(
                    msg="Organization with ID {} does not exist".format(org_id)
                )
            current_name = org_details.get("name")
        except Exception:
            module.fail_json(
                msg="Organization with ID {} does not exist".format(org_id)
            )

        # Check if the name is already set to the requested value
        if current_name == new_name:
            module.exit_json(
                changed=False,
                msg="Organization name is already set to '{}'".format(new_name),
                organization=org_details,
            )
    except Exception as e:
        module.fail_json(msg="Failed to check organization details: {}".format(str(e)))

    # If check_mode is enabled, return now
    if module.check_mode:
        # Update the organization details with the new name for the result
        org_details["name"] = new_name
        module.exit_json(
            changed=True,
            msg="Organization name would be updated from '{}' to '{}'".format(
                current_name, new_name
            ),
            organization=org_details,
        )

    # Update the organization name
    try:
        # Prepare the request data
        update_data = {"orgId": org_id, "name": new_name}

        # Make the API request
        update_path = "/org/updateName"
        result = client.post(update_path, data=update_data)

        # Standardize the result data for consistent output
        standardized_result = standardize_org_data(result)

        # Return the result
        module.exit_json(
            changed=True,
            msg="Organization name updated from '{}' to '{}'".format(
                current_name, new_name
            ),
            organization=standardized_result,
        )
    except Exception as e:
        module.fail_json(msg="Failed to update organization name: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == "__main__":
    main()
