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
module: contentsource
short_description: Manage content sources in SUSE Multi-Linux Manager content projects
description:
  - Attach or detach software channel sources to/from content projects in SUSE Multi-Linux Manager.
  - Only software channels are supported as sources for content projects.
  - Manage source positioning within content projects for proper priority ordering.
version_added: '1.0.0'
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  project_label:
    description: Label of the content project where the source will be managed.
    type: str
    required: true
  source_type:
    description:
      - Type of the content source to manage.
      - Currently only C(software) for software channel sources is supported.
      - Configuration channels cannot be attached to content projects.
    type: str
    choices: [ software ]
    required: true
  source_label:
    description: Label of the content source to attach or detach.
    type: str
    required: true
  source_position:
    description: Position/priority of the source within the content project.
    type: int
    default: 0
  state:
    description: Desired state of the content source in the project.
    type: str
    choices: [ present, absent ]
    default: present
requirements:
  - python >= 3.6
  - SUSE Multi-Linux Manager server with API access
'''

EXAMPLES = r'''
- name: Attach a software source to a content project
  goldyfruit.mlm.contentsource:
    project_label: "dev-project"
    source_type: "software"
    source_label: "sles15-sp4-pool-x86_64"
    source_position: 0
    state: present

- name: Detach a source from a content project
  goldyfruit.mlm.contentsource:
    project_label: "dev-project"
    source_type: "software"
    source_label: "sles15-sp4-pool-x86_64"
    state: absent
'''

RETURN = r'''
source:
  description: Information about the content source operation.
  returned: always
  type: dict
  contains:
    project_label:
      description: Label of the content project.
      type: str
      sample: "dev-project"
    source_type:
      description: Type of the source.
      type: str
      sample: "software"
    source_label:
      description: Label of the source.
      type: str
      sample: "sles15-sp4-pool-x86_64"
    source_position:
      description: Position of the source in the project.
      type: int
      sample: 0
    state:
      description: State of the source.
      type: str
      sample: "attached"
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "Source attached successfully"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_contentmanagement_utils import (
    attach_source_to_project,
    detach_source_from_project,
    list_project_sources,
    standardize_content_source_data,
)


def is_source_attached(client, project_label, source_type, source_label):
    """Check if a source is attached to a content project."""
    try:
        sources = list_project_sources(client, project_label, source_type)
        for source in sources:
            standardized = standardize_content_source_data(source)
            if standardized.get('label') == source_label:
                return True
        return False
    except Exception:
        return False


def attach_source_handler(module, client):
    """Attach a source to a content project."""
    project_label = module.params['project_label']
    source_type = module.params['source_type']
    source_label = module.params['source_label']
    source_position = module.params['source_position']

    source_attached = is_source_attached(client, project_label, source_type, source_label)

    if module.check_mode:
        if source_attached:
            return False, {
                "project_label": project_label,
                "source_type": source_type,
                "source_label": source_label,
                "source_position": source_position,
                "state": "attached"
            }, "Source already attached"
        return True, {
            "project_label": project_label,
            "source_type": source_type,
            "source_label": source_label,
            "source_position": source_position,
            "state": "attached"
        }, "Source would be attached"

    try:
        if source_attached:
            return False, {
                "project_label": project_label,
                "source_type": source_type,
                "source_label": source_label,
                "source_position": source_position,
                "state": "attached"
            }, "Source already attached"

        attach_source_to_project(client, project_label, source_type, source_label, source_position)
        return True, {
            "project_label": project_label,
            "source_type": source_type,
            "source_label": source_label,
            "source_position": source_position,
            "state": "attached"
        }, "Source attached successfully"
    except Exception as e:
        module.fail_json(msg="Failed to attach source: {}".format(str(e)))


def detach_source_handler(module, client):
    """Detach a source from a content project."""
    project_label = module.params['project_label']
    source_type = module.params['source_type']
    source_label = module.params['source_label']

    source_attached = is_source_attached(client, project_label, source_type, source_label)

    if module.check_mode:
        if source_attached:
            return True, {
                "project_label": project_label,
                "source_type": source_type,
                "source_label": source_label,
                "state": "detached"
            }, "Source would be detached"
        return False, {
            "project_label": project_label,
            "source_type": source_type,
            "source_label": source_label,
            "state": "detached"
        }, "Source already detached"

    try:
        if source_attached:
            detach_source_from_project(client, project_label, source_type, source_label)
            return True, {
                "project_label": project_label,
                "source_type": source_type,
                "source_label": source_label,
                "state": "detached"
            }, "Source detached successfully"
        return False, {
            "project_label": project_label,
            "source_type": source_type,
            "source_label": source_label,
            "state": "detached"
        }, "Source already detached"
    except Exception as e:
        module.fail_json(msg="Failed to detach source: {}".format(str(e)))


def main():
    """Main module execution."""
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        project_label=dict(type='str', required=True),
        source_type=dict(type='str', required=True, choices=['software']),
        source_label=dict(type='str', required=True),
        source_position=dict(type='int', default=0),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    client = MLMClient(module)
    client.login()

    try:
        state = module.params['state']
        if state == 'present':
            changed, result, msg = attach_source_handler(module, client)
        else:  # state == 'absent'
            changed, result, msg = detach_source_handler(module, client)

        module.exit_json(
            changed=changed,
            msg=msg,
            source=result
        )
    except Exception as e:
        module.fail_json(msg="Failed to manage content source: {}".format(str(e)))
    finally:
        client.logout()


if __name__ == '__main__':
    main()
