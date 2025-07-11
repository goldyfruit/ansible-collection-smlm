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
module: channel_info
short_description: Gather information about software channels in SUSE Multi-Linux Manager
description:
  - Retrieve information about software channels in SUSE Multi-Linux Manager.
  - List all channels or get detailed information about specific channels.
  - This module uses the SUSE Multi-Linux Manager API to gather channel information.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  channel_label:
    description:
      - Label of the software channel to get information about.
      - If not provided, information about all channels will be returned.
    type: str
    required: false
  channel_id:
    description:
      - ID of the software channel to get information about.
      - If not provided, information about all channels will be returned.
    type: int
    required: false
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to view channel information.
  - This module is read-only and does not make any changes to the system.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
- name: List all channels
  goldyfruit.mlm.channel_info:
  register: channel_list

- name: Display channel labels
  ansible.builtin.debug:
    msg: "{{ channel_list.channels | map(attribute='label') | list }}"

- name: Count channels
  ansible.builtin.debug:
    msg: "Total channels: {{ channel_list.channels | length }}"

- name: Get channel details by ID
  goldyfruit.mlm.channel_info:
    channel_id: 42
  register: channel_details

- name: Get channel details by label
  goldyfruit.mlm.channel_info:
    channel_label: "sles15-sp4-pool-x86_64"
  register: channel_details

- name: Display channel details
  ansible.builtin.debug:
    msg: "{{ channel_details.channel }}"
"""

RETURN = r"""
channels:
  description: List of channel information.
  returned: when multiple channels are found or no specific channel is requested
  type: list
  elements: dict
  contains:
    id:
      description: Channel ID.
      type: int
      sample: 42
    label:
      description: Channel label.
      type: str
      sample: "sles15-sp4-pool-x86_64"
    name:
      description: Channel name.
      type: str
      sample: "SLES 15 SP4 Pool x86_64"
    summary:
      description: Channel summary.
      type: str
      sample: "SLES 15 SP4 base packages"
    description:
      description: Channel description.
      type: str
      sample: "SLES 15 SP4 base packages for x86_64 architecture"
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
      sample: "SUSE"
    maintainer_email:
      description: Maintainer email.
      type: str
      sample: "support@suse.com"
    support_policy:
      description: Support policy.
      type: str
      sample: "Supported"
    gpg_key_url:
      description: GPG key URL.
      type: str
      sample: "https://download.suse.com/keys/rpm-gpg-key"
    gpg_key_id:
      description: GPG key ID.
      type: str
      sample: "0x12345678"
    gpg_key_fp:
      description: GPG key fingerprint.
      type: str
      sample: "1234 5678 9ABC DEF0 1234 5678 9ABC DEF0 1234 5678"
    parent_channel_label:
      description: Parent channel label (for child channels).
      type: str
      sample: ""
    package_count:
      description: Number of packages in the channel.
      type: int
      sample: 1234
    globally_subscribable:
      description: Whether the channel is globally subscribable.
      type: bool
      sample: true
channel:
  description: Information about a specific channel.
  returned: when a specific channel is requested and found
  type: dict
  contains:
    id:
      description: Channel ID.
      type: int
      sample: 42
    label:
      description: Channel label.
      type: str
      sample: "sles15-sp4-pool-x86_64"
    name:
      description: Channel name.
      type: str
      sample: "SLES 15 SP4 Pool x86_64"
    summary:
      description: Channel summary.
      type: str
      sample: "SLES 15 SP4 base packages"
    description:
      description: Channel description.
      type: str
      sample: "SLES 15 SP4 base packages for x86_64 architecture"
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
      sample: "SUSE"
    maintainer_email:
      description: Maintainer email.
      type: str
      sample: "support@suse.com"
    support_policy:
      description: Support policy.
      type: str
      sample: "Supported"
    gpg_key_url:
      description: GPG key URL.
      type: str
      sample: "https://download.suse.com/keys/rpm-gpg-key"
    gpg_key_id:
      description: GPG key ID.
      type: str
      sample: "0x12345678"
    gpg_key_fp:
      description: GPG key fingerprint.
      type: str
      sample: "1234 5678 9ABC DEF0 1234 5678 9ABC DEF0 1234 5678"
    parent_channel_label:
      description: Parent channel label (for child channels).
      type: str
      sample: ""
    package_count:
      description: Number of packages in the channel.
      type: int
      sample: 1234
    globally_subscribable:
      description: Whether the channel is globally subscribable.
      type: bool
      sample: true
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_channel_utils import (
    list_channels,
    get_channel_details,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Extracts and validates the required parameters
    3. Creates the MLM client and logs in to the API
    4. Determines whether to retrieve a specific channel's details or list all channels
    5. Returns the result to Ansible
    6. Ensures proper logout from the API

    The module supports check mode, though it doesn't make any changes to the system
    as it's an information-gathering module.

    If neither channel_id nor channel_label is provided, the module will list all channels.
    If either channel_id or channel_label is provided, the module will return detailed information
    about that specific channel. If both are provided, channel_id takes precedence.
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        channel_id=dict(type="int", required=False),
        channel_label=dict(type="str", required=False),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Extract module parameters
    channel_id = module.params.get("channel_id")
    channel_label = module.params.get("channel_label")

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
            if channel_id is not None or channel_label is not None:
                # Get details for a specific channel
                channel_details = get_channel_details(client, channel_id, channel_label)
                if channel_details:
                    module.exit_json(changed=False, channel=channel_details)
                else:
                    # Channel not found
                    identifier = channel_label or channel_id
                    module.fail_json(msg="Channel '{}' not found".format(identifier))
            else:
                # List all channels
                channels = list_channels(client)
                module.exit_json(changed=False, channels=channels)
        except Exception as e:
            module.fail_json(
                msg="Failed to retrieve channel information: {}".format(str(e))
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
