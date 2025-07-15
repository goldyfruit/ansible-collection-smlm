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
module: channel_arch_info
short_description: Retrieve information about software channel architectures in SUSE Multi-Linux Manager
description:
  - Retrieve information about available software channel architectures in SUSE Multi-Linux Manager.
  - This module provides details about the potential software channel architectures that can be created.
  - This module uses the SUSE Multi-Linux Manager API to retrieve channel architecture information.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  arch_label:
    description:
      - Label of a specific architecture to get information for.
      - If not provided, information for all architectures will be returned.
      - Can also be specified using the 'arch_name' alias.
    type: str
    required: false
    aliases: [ arch_name ]
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to access architecture information.
  - This module is read-only and does not modify any system state.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Using credentials configuration file (recommended)
- name: Get all channel architectures using credentials file
  goldyfruit.mlm.channel_arch_info:
  register: all_architectures

- name: Get specific architecture information using credentials file
  goldyfruit.mlm.channel_arch_info:
    arch_label: "channel-x86_64"
  register: x86_64_architecture

- name: Get architectures using specific instance
  goldyfruit.mlm.channel_arch_info:
    instance: staging  # Use staging instance from credentials file
  register: staging_architectures

# Using environment variables
- name: Get all architectures using environment variables
  goldyfruit.mlm.channel_arch_info:
  environment:
    MLM_URL: "https://mlm.example.com"
    MLM_USERNAME: "admin"
    MLM_PASSWORD: "{{ vault_mlm_password }}"
  register: arch_result

- name: Display architecture information
  ansible.builtin.debug:
    msg: "Found {{ arch_result.architectures | length }} architectures"

- name: Display specific architecture details
  ansible.builtin.debug:
    msg: "Architecture: {{ item.name }} ({{ item.label }})"
  loop: "{{ arch_result.architectures }}"
  when: arch_result.architectures is defined

- name: Check if x86_64 architecture is available
  goldyfruit.mlm.channel_arch_info:
    arch_label: "channel-x86_64"
  register: x86_64_check
  failed_when: x86_64_check.architecture is not defined

- name: Get architecture information for multiple labels
  goldyfruit.mlm.channel_arch_info:
    arch_label: "{{ item }}"
  loop:
    - "channel-x86_64"
    - "channel-aarch64"
  register: multi_arch_results
  ignore_errors: true

- name: Display available architectures in a formatted way
  ansible.builtin.debug:
    msg: |
      Available Channel Architectures:
      {% for arch in all_architectures.architectures %}
      - {{ arch.name }} ({{ arch.label }})
      {% endfor %}
  when: all_architectures.architectures is defined
"""

RETURN = r"""
architectures:
  description: List of all available channel architectures.
  returned: when arch_label is not specified
  type: list
  elements: dict
  contains:
    name:
      description: Human-readable name of the architecture.
      type: str
      sample: "channel-x86_64"
    label:
      description: Label of the architecture used in API calls.
      type: str
      sample: "channel-x86_64"
  sample:
    - name: "channel-x86_64"
      label: "channel-x86_64"
    - name: "channel-aarch64"
      label: "channel-aarch64"
architecture:
  description: Information about the requested architecture.
  returned: when arch_label is specified and found
  type: dict
  contains:
    name:
      description: Human-readable name of the architecture.
      type: str
      sample: "channel-x86_64"
    label:
      description: Label of the architecture used in API calls.
      type: str
      sample: "channel-x86_64"
  sample:
    name: "channel-x86_64"
    label: "channel-x86_64"
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "Retrieved information for 2 architectures"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_channel_utils import (
    list_channel_architectures,
    get_channel_architecture_by_label,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Creates the MLM client and logs in to the API
    3. Determines the action to take based on the parameters
    4. Calls the appropriate function to retrieve the information
    5. Returns the result to Ansible
    6. Ensures proper logout from the API

    The module is read-only and does not modify any system state.
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        arch_label=dict(type="str", required=False, aliases=["arch_name"]),
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
        # Determine what to do based on the parameters
        arch_label = module.params.get("arch_label")

        if arch_label:
            # Get specific architecture information
            architecture = get_channel_architecture_by_label(client, arch_label)

            if architecture:
                module.exit_json(
                    changed=False,
                    msg="Retrieved information for architecture '{}'".format(arch_label),
                    architecture=architecture,
                )
            else:
                module.fail_json(msg="Architecture '{}' not found".format(arch_label))
        else:
            # Get all architectures
            architectures = list_channel_architectures(client)

            module.exit_json(
                changed=False,
                msg="Retrieved information for {} architectures".format(len(architectures)),
                architectures=architectures,
            )

    except Exception as e:
        module.fail_json(msg="Failed to retrieve architecture information: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == "__main__":
    main()
