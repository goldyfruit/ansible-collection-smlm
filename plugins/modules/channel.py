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
module: channel
short_description: Manage software channels in SUSE Multi-Linux Manager
description:
  - Create, update, clone, or delete software channels in SUSE Multi-Linux Manager.
  - Manage software channel configurations and properties.
  - This module uses the SUSE Multi-Linux Manager API to manage software channels.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  label:
    description:
      - Label of the software channel.
      - Required for all operations.
      - Must be unique across all channels.
    type: str
    required: true
  state:
    description:
      - Whether the channel should exist or not.
      - When C(present), the channel will be created if it doesn't exist.
      - When C(absent), the channel will be deleted if it exists.
      - When C(cloned), the channel will be cloned from another channel.
    type: str
    choices: [ present, absent, cloned ]
    default: present
  name:
    description:
      - Display name of the software channel.
      - Required when state=present or state=cloned.
    type: str
    required: false
  summary:
    description:
      - Summary description of the software channel.
      - Optional when creating or cloning channels.
    type: str
    required: false
  arch_label:
    description:
      - Architecture label for the channel (e.g., x86_64, aarch64, noarch).
      - Required when state=present.
    type: str
    required: false
  parent_label:
    description:
      - Label of the parent channel for child channels.
      - Optional when creating channels.
    type: str
    required: false
  original_label:
    description:
      - Label of the original channel to clone from.
      - Required when state=cloned.
    type: str
    required: false
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to manage software channels.
  - When deleting a channel, all associated configurations will be removed.
  - Deleting a channel is a destructive operation and cannot be undone.
  - Channel labels must be unique across the entire system.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Using credentials configuration file (recommended)
- name: Create a new software channel using credentials file
  goldyfruit.mlm.channel:
    label: "my-custom-channel"
    name: "My Custom Channel"
    summary: "Custom packages for my organization"
    arch_label: "x86_64"
    state: present
  register: channel_result

- name: Create a child channel using credentials file
  goldyfruit.mlm.channel:
    label: "my-custom-updates"
    name: "My Custom Updates"
    summary: "Updates for my custom channel"
    arch_label: "x86_64"
    parent_label: "my-custom-channel"
    state: present

- name: Create channel using specific instance
  goldyfruit.mlm.channel:
    instance: staging  # Use staging instance from credentials file
    label: "staging-channel"
    name: "Staging Channel"
    summary: "Channel for staging environment"
    arch_label: "x86_64"
    state: present

# Using environment variables
- name: Create channel using environment variables
  goldyfruit.mlm.channel:
    label: "prod-custom-channel"
    name: "Production Custom Channel"
    summary: "Production custom packages"
    arch_label: "x86_64"
    state: present
  environment:
    MLM_URL: "https://mlm.example.com"
    MLM_USERNAME: "admin"
    MLM_PASSWORD: "{{ vault_mlm_password }}"

- name: Clone an existing channel
  goldyfruit.mlm.channel:
    label: "sles15-sp4-clone"
    name: "SLES 15 SP4 Clone"
    summary: "Cloned SLES 15 SP4 channel"
    original_label: "sles15-sp4-pool-x86_64"
    state: cloned
  register: clone_result

- name: Create multiple architecture channels
  goldyfruit.mlm.channel:
    label: "multi-arch-{{ item }}"
    name: "Multi-Arch Channel {{ item | upper }}"
    summary: "Multi-architecture channel for {{ item }}"
    arch_label: "{{ item }}"
    state: present
  loop:
    - x86_64
    - aarch64
  register: multi_arch_results

- name: Delete a software channel
  goldyfruit.mlm.channel:
    label: "old-channel"
    state: absent
"""

RETURN = r"""
channel:
  description: Information about the managed channel.
  returned: when state=present or state=cloned and the channel exists or was created/cloned
  type: dict
  contains:
    id:
      description: Channel ID.
      type: int
      sample: 42
    label:
      description: Channel label.
      type: str
      sample: "my-custom-channel"
    name:
      description: Channel name.
      type: str
      sample: "My Custom Channel"
    summary:
      description: Channel summary.
      type: str
      sample: "Custom packages for my organization"
    description:
      description: Channel description.
      type: str
      sample: "Custom packages for my organization"
    arch_name:
      description: Architecture name.
      type: str
      sample: "x86_64"
    last_modified:
      description: Last modification date.
      type: str
      sample: "2025-01-01T00:00:00Z"
    maintainer_name:
      description: Maintainer name.
      type: str
      sample: "Admin User"
    maintainer_email:
      description: Maintainer email.
      type: str
      sample: "admin@example.com"
    support_policy:
      description: Support policy.
      type: str
      sample: "Custom"
    parent_channel_label:
      description: Parent channel label (for child channels).
      type: str
      sample: "parent-channel"
    package_count:
      description: Number of packages in the channel.
      type: int
      sample: 1234
    globally_subscribable:
      description: Whether the channel is globally subscribable.
      type: bool
      sample: true
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "Channel 'my-custom-channel' created successfully"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_channel_utils import (
    create_channel,
    delete_channel,
    clone_channel,
    get_channel_by_label,
    standardize_channel_data,
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
        label=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent", "cloned"]),
        name=dict(type="str", required=False),
        summary=dict(type="str", required=False),
        arch_label=dict(type="str", required=False),
        parent_label=dict(type="str", required=False),
        original_label=dict(type="str", required=False),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ["name", "arch_label"]),
            ("state", "cloned", ["name", "original_label"]),
        ],
    )

    # Create the MLM client
    client = MLMClient(module)

    # Login to the API
    client.login()

    try:
        # Determine what to do based on the state
        state = module.params["state"]
        label = module.params["label"]

        if state == "present":
            # Create or update the channel
            changed, result, msg = create_channel(module, client)
            if changed or result:
                module.exit_json(changed=changed, msg=msg, channel=result)
            else:
                module.exit_json(changed=changed, msg=msg)

        elif state == "cloned":
            # Clone a channel
            changed, result, msg = clone_channel(module, client)
            if changed or result:
                module.exit_json(changed=changed, msg=msg, channel=result)
            else:
                module.exit_json(changed=changed, msg=msg)

        else:  # state == 'absent'
            # Delete the channel
            changed, result, msg = delete_channel(module, client)
            module.exit_json(changed=changed, msg=msg)

    except Exception as e:
        module.fail_json(msg="Failed to manage channel: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == "__main__":
    main()
