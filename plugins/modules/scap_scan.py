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
module: scap_scan
short_description: Manage OpenSCAP scans in SUSE Multi-Linux Manager
description:
  - Schedule or delete OpenSCAP XCCDF scans in SUSE Multi-Linux Manager.
  - This module uses the SUSE Multi-Linux Manager API to manage OpenSCAP scans.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  system_id:
    description:
      - ID of the system to manage SCAP scans for.
      - Required for all operations.
    type: int
    required: true
  scan_id:
    description:
      - ID of the SCAP scan to delete.
      - Required when state=absent.
    type: int
    required: false
  state:
    description:
      - Whether the scan should exist or not.
      - When C(present), a new scan will be scheduled.
      - When C(absent), the specified scan will be deleted.
    type: str
    choices: [ present, absent ]
    default: present
  profile:
    description:
      - XCCDF profile to use for the scan.
      - Required when state=present.
    type: str
    required: false
  path:
    description:
      - Path to the XCCDF document to use for the scan.
      - Required when state=present.
    type: str
    required: false
  parameters:
    description:
      - Additional parameters for the scan.
      - Optional when state=present.
    type: dict
    required: false
  oval_files:
    description:
      - Additional OVAL files for the oscap tool.
      - Optional when state=present.
    type: list
    elements: str
    required: false
  date:
    description:
      - The date to schedule the action.
      - Format should be ISO8601 (e.g., "2025-06-15T14:30:00").
      - If not provided, the scan will be scheduled immediately.
      - Optional when state=present.
    type: str
    required: false
notes:
  - This module requires the SUSE Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to manage SCAP scans.
  - When scheduling a scan, the system must have the SCAP capability enabled.
  - When deleting a scan, all associated data will be deleted and cannot be recovered.
requirements:
  - python >= 3.6
'''

EXAMPLES = r'''
# Using credentials configuration file (recommended)
- name: Schedule a basic OpenSCAP XCCDF scan
  goldyfruit.mlm.scap_scan:
    system_id: 1000010000
    state: present
    profile: "xccdf_org.ssgproject.content_profile_common"
    path: "/usr/share/xml/scap/ssg/content/ssg-sle15-xccdf.xml"
  register: scan_result

- name: Display the new scan ID
  ansible.builtin.debug:
    msg: "Scan ID: {{ scan_result.scan.id }}"

- name: Schedule an OpenSCAP XCCDF scan with additional OVAL files and scheduled date
  goldyfruit.mlm.scap_scan:
    system_id: 1000010000
    state: present
    profile: "xccdf_org.ssgproject.content_profile_common"
    path: "/usr/share/xml/scap/ssg/content/ssg-sle15-xccdf.xml"
    oval_files:
      - "/usr/share/xml/scap/ssg/content/ssg-sle15-oval.xml"
      - "/usr/share/xml/scap/ssg/content/ssg-sle15-cpe-oval.xml"
    date: "2025-06-15T14:30:00"
  register: scheduled_scan_result

- name: Schedule an OpenSCAP XCCDF scan with additional parameters
  goldyfruit.mlm.scap_scan:
    system_id: 1000010000
    state: present
    profile: "xccdf_org.ssgproject.content_profile_common"
    path: "/usr/share/xml/scap/ssg/content/ssg-sle15-xccdf.xml"
    parameters:
      tailoring_path: "/etc/openscap/tailoring.xml"
      extra_args: "--fetch-remote-resources"
  register: param_scan_result

- name: Schedule scan using specific instance
  goldyfruit.mlm.scap_scan:
    instance: staging  # Use staging instance from credentials file
    system_id: 1000010000
    state: present
    profile: "xccdf_org.ssgproject.content_profile_common"
    path: "/usr/share/xml/scap/ssg/content/ssg-sle15-xccdf.xml"
  register: staging_scan_result

- name: Delete an OpenSCAP XCCDF scan
  goldyfruit.mlm.scap_scan:
    system_id: 1000010000
    scan_id: 42
    state: absent
  register: delete_result
'''

RETURN = r'''
scan:
  description: Information about the created or managed scan.
  returned: when state=present and the scan was scheduled
  type: dict
  contains:
    id:
      description: Scan ID.
      type: str
      sample: "42"
    profile:
      description: XCCDF profile used for the scan.
      type: str
      sample: "xccdf_org.ssgproject.content_profile_common"
    path:
      description: Path to the XCCDF document used for the scan.
      type: str
      sample: "/usr/share/xml/scap/ssg/content/ssg-sle15-xccdf.xml"
    parameters:
      description: Additional parameters used for the scan.
      type: dict
      sample: {"param1": "value1", "param2": "value2"}
    oval_files:
      description: Additional OVAL files used for the scan.
      type: list
      elements: str
      sample: ["/usr/share/xml/scap/ssg/content/ssg-sle15-oval.xml"]
    date:
      description: The date the scan was scheduled for.
      type: str
      sample: "2025-06-15T14:30:00"
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "OpenSCAP XCCDF scan scheduled successfully"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_scap_utils import (
    schedule_xccdf_scan as utils_schedule_xccdf_scan,
    delete_xccdf_scan as utils_delete_xccdf_scan,
)


def schedule_xccdf_scan(module, client):
    """
    Schedule an OpenSCAP XCCDF scan.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters efficiently
    params = module.params
    system_id = params['system_id']
    profile = params['profile']
    path = params['path']
    parameters = params.get('parameters', {})
    oval_files = params.get('oval_files')
    date = params.get('date')

    # Check if a scan with the same parameters already exists (optimization: avoid duplicate scans)
    from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_scap_utils import list_xccdf_scans
    existing_scans = list_xccdf_scans(client, system_id)

    # Efficient check for existing scans with matching parameters
    scan_match = next(
        (scan for scan in existing_scans
         if scan.get('profile') == profile
         and scan.get('path') == path
         and (not date or scan.get('created') == date)
         and (not parameters or scan.get('parameters') == parameters)
         and (not oval_files or scan.get('oval_files') == oval_files)),
        None
    )

    if scan_match:
        return False, scan_match, "OpenSCAP XCCDF scan with the same parameters already exists"

    # Handle check mode
    if module.check_mode:
        return True, {
            "profile": profile,
            "path": path,
            "parameters": parameters,
            "oval_files": oval_files,
            "date": date
        }, "OpenSCAP XCCDF scan would be scheduled"

    # Schedule the scan
    try:
        scan_result = utils_schedule_xccdf_scan(
            client, system_id, profile, path, parameters, oval_files, date, module
        )
        return True, scan_result, "OpenSCAP XCCDF scan scheduled successfully"
    except Exception as e:
        module.fail_json(msg=f"Failed to schedule OpenSCAP XCCDF scan: {e}")


def delete_xccdf_scan(module, client):
    """
    Delete an OpenSCAP XCCDF scan.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters efficiently
    params = module.params
    system_id = params['system_id']
    scan_id = params['scan_id']

    # Check if the scan exists
    from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_scap_utils import get_xccdf_scan_details
    scan = get_xccdf_scan_details(client, system_id, scan_id)

    # Early return for non-existent scans
    if not scan or 'error' in scan:
        return False, None, f"OpenSCAP XCCDF scan {scan_id} does not exist"

    # Handle check mode
    if module.check_mode:
        return True, None, f"OpenSCAP XCCDF scan {scan_id} would be deleted"

    # Delete the scan
    try:
        utils_delete_xccdf_scan(client, system_id, scan_id, module)
        return True, None, f"OpenSCAP XCCDF scan {scan_id} deleted successfully"
    except Exception as e:
        module.fail_json(msg=f"Failed to delete OpenSCAP XCCDF scan: {e}")


def main():
    """Main module execution."""
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        system_id=dict(type='int', required=True),
        scan_id=dict(type='int', required=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        profile=dict(type='str', required=False),
        path=dict(type='str', required=False),
        parameters=dict(type='dict', required=False),
        oval_files=dict(type='list', elements='str', required=False),
        date=dict(type='str', required=False),
    )

    # Define required arguments based on state
    required_if = [
        ['state', 'present', ['profile', 'path']],
        ['state', 'absent', ['scan_id']],
    ]

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
    )

    # Create the MLM client
    client = MLMClient(module)

    # Login to the API
    client.login()

    try:
        # Determine what to do based on the state
        state = module.params['state']
        if state == 'present':
            changed, result, msg = schedule_xccdf_scan(module, client)
        else:  # state == 'absent'
            changed, result, msg = delete_xccdf_scan(module, client)

        # Return the result
        if result:
            module.exit_json(
                changed=changed,
                msg=msg,
                scan=result
            )
        else:
            module.exit_json(
                changed=changed,
                msg=msg
            )
    except Exception as e:
        module.fail_json(msg="Failed to manage OpenSCAP XCCDF scan: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == '__main__':
    main()
