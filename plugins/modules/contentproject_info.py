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

DOCUMENTATION = r'''
---
module: contentproject_info
short_description: Get information about content projects in SUSE Multi-Linux Manager
description:
  - List all content projects in SUSE Multi-Linux Manager.
  - Get details of a specific content project.
  - This module uses the SUSE Multi-Linux Manager API to retrieve content project information.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  label:
    description:
      - Label of the content project to get details for.
      - If provided, returns details of the specified content project.
      - If not provided, lists all content projects.
    type: str
    required: false
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to view content projects.
  - If label is not provided, the module will list all content projects.
  - If label is provided, the module will return details of the specified content project.
requirements:
  - python >= 3.6
'''

EXAMPLES = r'''
# Using credentials configuration file (recommended)
- name: List all content projects using credentials file
  goldyfruit.mlm.contentproject_info:
  register: projects_result

- name: Display all content project labels
  ansible.builtin.debug:
    msg: "{{ projects_result.projects | map(attribute='label') | list }}"

- name: Get details of a specific content project using credentials file
  goldyfruit.mlm.contentproject_info:
    label: "dev-project"
  register: project_result

- name: Display content project details
  ansible.builtin.debug:
    msg: "{{ project_result.project }}"

# Using environment variables
- name: List content projects using environment variables
  goldyfruit.mlm.contentproject_info:
  environment:
    MLM_URL: "https://mlm.example.com"
    MLM_USERNAME: "admin"
    MLM_PASSWORD: "{{ vault_mlm_password }}"

# Using specific instance from credentials file
- name: Get project details using specific instance
  goldyfruit.mlm.contentproject_info:
    instance: staging
    label: "staging-project"
  register: staging_project
'''

RETURN = r'''
projects:
  description: List of all content projects.
  returned: when label is not provided
  type: list
  elements: dict
  contains:
    label:
      description: Label of the content project.
      type: str
      sample: "dev-project"
    name:
      description: Name of the content project.
      type: str
      sample: "Development Project"
    description:
      description: Description of the content project.
      type: str
      sample: "Content project for development"
    first_environment:
      description: Label of the first environment in the project.
      type: str
      sample: "dev"
    created:
      description: Timestamp when the project was created.
      type: str
      sample: "2025-01-01T12:00:00Z"
    modified:
      description: Timestamp when the project was last modified.
      type: str
      sample: "2025-01-01T12:00:00Z"
project:
  description: Details of the specified content project.
  returned: when label is provided
  type: dict
  contains:
    label:
      description: Label of the content project.
      type: str
      sample: "dev-project"
    name:
      description: Name of the content project.
      type: str
      sample: "Development Project"
    description:
      description: Description of the content project.
      type: str
      sample: "Content project for development"
    first_environment:
      description: Label of the first environment in the project.
      type: str
      sample: "dev"
    created:
      description: Timestamp when the project was created.
      type: str
      sample: "2025-01-01T12:00:00Z"
    modified:
      description: Timestamp when the project was last modified.
      type: str
      sample: "2025-01-01T12:00:00Z"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_contentmanagement_utils import (
    list_content_projects,
    get_content_project_details,
    standardize_content_project_data,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Extracts and validates the required parameters
    3. Creates the MLM client and logs in to the API
    4. Determines whether to retrieve a specific content project's details or list all content projects
    5. Returns the result to Ansible
    6. Ensures proper logout from the API

    The module supports check mode, though it doesn't make any changes to the system
    as it's an information-gathering module.

    If label is not provided, the module will list all content projects.
    If label is provided, the module will return detailed information about that specific content project.
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        label=dict(type='str', required=False),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Extract module parameters
    label = module.params.get('label')

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
            if label is not None:
                # Get details of the specified content project
                project_data = get_content_project_details(client, label)
                if not project_data or project_data.get('error'):
                    module.fail_json(msg="Content project '{}' not found".format(label))
                module.exit_json(changed=False, project=project_data)
            else:
                # List all content projects
                projects_data = list_content_projects(client)
                module.exit_json(changed=False, projects=projects_data)
        except Exception as e:
            module.fail_json(msg="Failed to retrieve content project information: {}".format(str(e)))
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


if __name__ == '__main__':
    main()
