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
module: contentsource_info
short_description: Retrieve information about content sources in SUSE Multi-Linux Manager content projects
description:
  - List all sources attached to a content project in SUSE Multi-Linux Manager.
  - Support for filtering by source type (software channels or configuration channels).
  - Retrieve detailed information including source labels, names, types, and states.
  - This module uses the SUSE Multi-Linux Manager API to efficiently query content source information.
version_added: '1.0.0'
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  project_label:
    description:
      - Label of the content project to query for sources.
      - Must be an existing content project in SUSE Multi-Linux Manager.
      - This identifies the target project for source information retrieval.
    type: str
    required: true
  source_type:
    description:
      - Type of sources to filter the results by.
      - C(software) to list only software channel sources (package repositories).
      - C(config) to list only configuration channel sources.
      - If not specified, all sources (both software and config) will be returned.
      - Useful for focused queries when only specific source types are needed.
    type: str
    choices: [ software, config ]
    required: false
seealso:
  - module: goldyfruit.mlm.contentsource
    description: Manage content sources in projects.
  - module: goldyfruit.mlm.contentproject_info
    description: Get information about content projects.
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have appropriate permissions to view content sources.
  - If source_type is not provided, all sources in the project will be listed.
  - Source information includes labels, names, types, and attachment states.
  - This module is read-only and does not modify any content sources.
  - Results can be used for inventory, validation, or automation decisions.
requirements:
  - python >= 3.6
  - SUSE Multi-Linux Manager server with API access
"""

EXAMPLES = r"""
# Using credentials configuration file (recommended)
- name: List all sources in a content project using credentials file
  goldyfruit.mlm.contentsource_info:
    project_label: "dev-project"
  register: all_sources_result

- name: List only software sources in a content project
  goldyfruit.mlm.contentsource_info:
    project_label: "dev-project"
    source_type: "software"
  register: software_sources_result

- name: List only configuration sources in a content project
  goldyfruit.mlm.contentsource_info:
    project_label: "dev-project"
    source_type: "config"
  register: config_sources_result

# Using specific instance from credentials file
- name: List sources using specific instance
  goldyfruit.mlm.contentsource_info:
    instance: staging
    project_label: "staging-project"
    source_type: "software"
  register: staging_sources_result

# Using environment variables with Ansible Vault
- name: List sources using environment variables
  goldyfruit.mlm.contentsource_info:
    project_label: "production-project"
    source_type: "software"
  environment:
    MLM_URL: "https://mlm.example.com"
    MLM_USERNAME: "admin"
    MLM_PASSWORD: "{{ vault_mlm_password }}"
  register: prod_sources_result

# Batch operations across multiple projects
- name: Get sources from multiple projects
  goldyfruit.mlm.contentsource_info:
    project_label: "{{ item }}"
  loop:
    - "dev-project"
    - "test-project"
    - "staging-project"
    - "production-project"
  register: multi_project_sources

# Integration with other modules
- name: Get current project sources before modifications
  goldyfruit.mlm.contentsource_info:
    project_label: "automation-project"
  register: pre_change_sources

- name: Add source if not present
  goldyfruit.mlm.contentsource:
    project_label: "automation-project"
    source_type: "software"
    source_label: "new-software-channel"
    state: present
  when: "'new-software-channel' not in (pre_change_sources.sources | map(attribute='label') | list)"
"""

RETURN = r"""
sources:
  description: List of sources in the content project.
  returned: always
  type: list
  elements: dict
  contains:
    label:
      description: Label of the source.
      type: str
      sample: "sles15-sp4-pool-x86_64"
    name:
      description: Name of the source.
      type: str
      sample: "SUSE Linux Enterprise Server 15 SP4"
    type:
      description: Type of the source.
      type: str
      sample: "software"
    state:
      description: State of the source.
      type: str
      sample: "attached"
    channelLabel:
      description: Channel label of the source.
      type: str
      sample: "sles15-sp4-pool-x86_64"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_contentmanagement_utils import (
    list_project_sources,
)


def main():
    """Main module execution."""
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        project_label=dict(type="str", required=True),
        source_type=dict(type="str", required=False, choices=["software", "config"]),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    project_label = module.params["project_label"]
    source_type = module.params.get("source_type")

    client = MLMClient(module)
    client.login()

    try:
        sources = list_project_sources(client, project_label, source_type)
        module.exit_json(changed=False, sources=sources)
    except Exception as e:
        module.fail_json(
            msg="Failed to retrieve content source information: {}".format(str(e))
        )
    finally:
        client.logout()


if __name__ == "__main__":
    main()
