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
module: org_transfer
short_description: Transfer systems between organizations in SUSE Manager
description:
  - Transfer systems from one organization to another in SUSE Manager.
  - This module uses the SUSE Manager API to transfer systems between organizations.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  to_org_id:
    description:
      - ID of the organization where the system(s) will be transferred to.
    type: int
    required: true
  system_ids:
    description:
      - List of system IDs to transfer.
    type: list
    elements: int
    required: true
notes:
  - This module requires the SUSE Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to transfer systems.
  - If executed by a SUSE Manager administrator, the systems will be transferred from their current organization to the organization specified by to_org_id.
  - If executed by an organization administrator, the systems must exist in the same organization as that administrator and the systems will be transferred to the organization specified by to_org_id.
  - In any scenario, the origination and destination organizations must be defined in a trust.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Using credentials configuration file (recommended)
- name: Transfer systems to another organization
  goldyfruit.mlm.org_transfer:
    to_org_id: 42
    system_ids:
      - 1001
      - 1002
      - 1003
  register: transfer_result

- name: Transfer systems using specific instance
  goldyfruit.mlm.org_transfer:
    instance: staging  # Use staging instance from credentials file
    to_org_id: 42
    system_ids:
      - 1001
      - 1002
      - 1003
  register: transfer_result

- name: Display transferred system IDs
  ansible.builtin.debug:
    msg: "Transferred systems: {{ transfer_result.transferred_system_ids }}"
"""

RETURN = r"""
transferred_system_ids:
  description: List of system IDs that were successfully transferred.
  returned: success
  type: list
  elements: int
  sample: [1001, 1002, 1003]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_org_utils import (
    get_organization_by_id,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Creates the MLM client and logs in to the API
    3. Validates the parameters and checks if the target organization exists
    4. Transfers the specified systems to the target organization
    5. Returns the result to Ansible
    6. Ensures proper logout from the API

    The module supports check mode, which allows for dry runs without making
    actual changes to the system.

    The transfer operation requires that:
    - The target organization exists
    - The user has appropriate permissions to transfer systems
    - The origination and destination organizations have a trust relationship
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        to_org_id=dict(type="int", required=True),
        system_ids=dict(type="list", elements="int", required=True),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Create the MLM client
    client = MLMClient(module)

    # Extract module parameters
    to_org_id = module.params["to_org_id"]
    system_ids = module.params["system_ids"]

    # Validate parameters
    if not system_ids:
        module.exit_json(
            changed=False,
            msg="No system IDs provided for transfer",
            transferred_system_ids=[],
        )

    # Check if the target organization exists using the utility function
    try:
        # Login to the API
        client.login()

        # Check if the target organization exists
        target_org = get_organization_by_id(client, to_org_id)
        if not target_org:
            module.fail_json(
                msg="Target organization with ID {} does not exist".format(to_org_id)
            )
    except Exception as e:
        module.fail_json(
            msg="Failed to check if target organization exists: {}".format(str(e))
        )

    # If check_mode is enabled, return now
    if module.check_mode:
        module.exit_json(
            changed=True,
            msg="Systems {} would be transferred to organization with ID {}".format(
                system_ids, to_org_id
            ),
            transferred_system_ids=system_ids,
        )

    # Transfer the systems
    try:
        # Prepare the request data
        transfer_data = {"toOrgId": to_org_id, "sids": system_ids}

        # Make the API request
        transfer_path = "/org/transferSystems"
        result = client.post(transfer_path, data=transfer_data)

        # The API returns a list of server IDs that were transferred
        transferred_ids = result

        # Return the result
        module.exit_json(
            changed=True,
            msg="Systems {} transferred to organization with ID {}".format(
                transferred_ids, to_org_id
            ),
            transferred_system_ids=transferred_ids,
        )
    except Exception as e:
        module.fail_json(msg="Failed to transfer systems: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == "__main__":
    main()
