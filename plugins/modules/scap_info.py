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
module: scap_info
short_description: Get information about OpenSCAP scans in SUSE Multi-Linux Manager
description:
  - Get information about OpenSCAP XCCDF scans in SUSE Multi-Linux Manager.
  - This module can list all OpenSCAP XCCDF scans for a system or get details of a specific scan.
  - This module uses the SUSE Multi-Linux Manager API to retrieve scan information.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  system_id:
    description:
      - ID of the system to get SCAP scan information for.
      - Required when listing scans (scan_id not provided).
      - Optional when getting details of a specific scan (scan_id provided).
    type: int
    required: false
  scan_id:
    description:
      - ID of the SCAP scan to get details for.
      - If provided, returns detailed information about this specific scan.
      - If not provided, lists all scans for the specified system.
    type: int
    required: false
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to view SCAP scan information.
  - If scan_id is not provided, the module will list all SCAP scans for the specified system.
  - If scan_id is provided, the module will return detailed information about that specific scan.
requirements:
  - python >= 3.6
'''

EXAMPLES = r'''
# Using credentials configuration file (recommended)
- name: List all OpenSCAP XCCDF scans for a system
  goldyfruit.mlm.scap_info:
    system_id: 1000010000
  register: scap_list

- name: Display scan IDs
  ansible.builtin.debug:
    msg: "{{ scap_list.scans | map(attribute='id') | list }}"

- name: Get details of a specific OpenSCAP XCCDF scan
  goldyfruit.mlm.scap_info:
    system_id: 1000010000
    scan_id: 42
  register: scap_details

- name: Get scans using specific instance
  goldyfruit.mlm.scap_info:
    instance: staging  # Use staging instance from credentials file
    system_id: 1000010000
  register: staging_scap_list

- name: Display scan details
  ansible.builtin.debug:
    msg: "{{ scap_details.scan }}"
'''

RETURN = r'''
scans:
  description: List of all OpenSCAP XCCDF scans for the specified system.
  returned: when scan_id is not provided
  type: list
  elements: dict
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
    completed:
      description: Whether the scan has completed.
      type: bool
      sample: true
    evaluation_completed:
      description: Whether the evaluation has completed.
      type: bool
      sample: true
    created:
      description: Timestamp when the scan was created.
      type: str
      sample: "2025-01-01T12:00:00Z"
scan:
  description: Detailed information about the specified OpenSCAP XCCDF scan.
  returned: when scan_id is provided
  type: dict
  contains:
    # Core identification
    id:
      description: Scan ID.
      type: str
      sample: "2"
    system_id:
      description: System ID where the scan was performed.
      type: str
      sample: "1000010008"

    # Scan configuration
    profile:
      description: XCCDF profile used for the scan.
      type: str
      sample: "xccdf_org.ssgproject.content_profile_standard"
    path:
      description: Path to the XCCDF document used for the scan.
      type: str
      sample: "/usr/share/xml/scap/ssg/content/ssg-debian11-xccdf.xml"
    command_line_arguments:
      description: Command line arguments passed to oscap tool.
      type: str
      sample: "--profile xccdf_org.ssgproject.content_profile_standard"
    oval_files:
      description: List of OVAL files used in the scan.
      type: list
      elements: str
      sample: ["/usr/share/xml/scap/ssg/content/ssg-debian11-oval.xml"]

    # Timing information
    started:
      description: Timestamp when the scan started.
      type: str
      sample: "2025-07-12T04:46:05Z"
    completed:
      description: Timestamp when the scan completed.
      type: str
      sample: "2025-07-12T04:46:05Z"
    created:
      description: Timestamp when the scan was created/scheduled.
      type: str
      sample: "2025-07-12T04:46:05Z"
    evaluation_completed:
      description: Whether the evaluation has completed.
      type: bool
      sample: true

    # Benchmark and profile details
    benchmark_identifier:
      description: XCCDF benchmark identifier.
      type: str
      sample: "xccdf_org.ssgproject.content_benchmark_DEBIAN-11"
    benchmark_version:
      description: Version of the benchmark used.
      type: str
      sample: "0.1.65"
    profile_identifier:
      description: XCCDF profile identifier.
      type: str
      sample: "xccdf_org.ssgproject.content_profile_standard"
    profile_title:
      description: Human-readable profile title.
      type: str
      sample: "Standard System Security Profile for Debian 11"
    scan_title:
      description: Title of the scan.
      type: str
      sample: "Standard System Security Profile for Debian 11"

    # Execution details
    scheduled_by:
      description: User who scheduled the scan.
      type: str
      sample: "admin"
    command:
      description: Full command executed for the scan.
      type: str
      sample: "/usr/bin/oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_standard"
    error_details:
      description: Error details if the scan failed.
      type: str
      sample: "No errors"
    status:
      description: Current status of the scan.
      type: str
      sample: "completed"

    # Detailed results and scoring (when available)
    results:
      description: List of rule results from the scan.
      type: list
      elements: dict
      contains:
        idref:
          description: Rule ID.
          type: str
          sample: "xccdf_org.ssgproject.content_rule_ensure_gpgcheck_globally_activated"
        result:
          description: Result of the rule evaluation.
          type: str
          sample: "pass"
        ident:
          description: List of identifiers associated with the rule.
          type: list
          elements: dict
          contains:
            system:
              description: Identifier system.
              type: str
              sample: "https://nvd.nist.gov/cce/index.cfm"
            text:
              description: Identifier text.
              type: str
              sample: "CCE-27343-3"

    result_files:
      description: Available result files (HTML reports, XML results, etc.).
      type: list
      elements: str
      sample: ["ssg-debian11-oval.xml.result.xml", "report.html", "results.xml"]

    test_results:
      description: Summary of test results.
      type: dict
      sample: {"passed": 45, "failed": 12, "error": 0}

    rule_results:
      description: Detailed rule-by-rule results.
      type: list
      elements: dict

    # Scoring information (when available)
    score:
      description: Achieved score for the scan.
      type: float
      sample: 85.5
    maxScore:
      description: Maximum possible score.
      type: float
      sample: 100.0
    passedRules:
      description: Number of rules that passed.
      type: int
      sample: 45
    failedRules:
      description: Number of rules that failed.
      type: int
      sample: 12
    errorRules:
      description: Number of rules that had errors.
      type: int
      sample: 0
    unknownRules:
      description: Number of rules with unknown results.
      type: int
      sample: 2
    notApplicableRules:
      description: Number of rules that are not applicable.
      type: int
      sample: 8
    notCheckedRules:
      description: Number of rules that were not checked.
      type: int
      sample: 3
    notSelectedRules:
      description: Number of rules that were not selected.
      type: int
      sample: 5
    informationalRules:
      description: Number of informational rules.
      type: int
      sample: 10
    fixedRules:
      description: Number of rules that were fixed.
      type: int
      sample: 2
    totalRules:
      description: Total number of rules evaluated.
      type: int
      sample: 87

    # Additional execution information
    parameters:
      description: Additional parameters used for the scan.
      type: dict
      sample: {"tailoring_path": "/etc/openscap/tailoring.xml"}
    returnCode:
      description: Return code from the oscap command.
      type: int
      sample: 0
    stderr:
      description: Standard error output from the scan.
      type: str
      sample: ""
    stdout:
      description: Standard output from the scan.
      type: str
      sample: "OpenSCAP scan completed successfully"
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "OpenSCAP XCCDF scan information retrieved successfully"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_scap_utils import (
    list_xccdf_scans,
    get_xccdf_scan_details,
)


def main():
    """Main module execution."""
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update({
        'system_id': {'type': 'int', 'required': False},
        'scan_id': {'type': 'int', 'required': False},
    })

    # Create the module with optimized parameter validation
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['system_id', 'scan_id']],  # Optimize validation with built-in check
    )

    # Extract parameters once for efficiency
    system_id = module.params['system_id']
    scan_id = module.params['scan_id']

    # Create and initialize client
    client = MLMClient(module)
    client.login()

    try:
        if scan_id:
            # Get details of a specific scan
            scan = get_xccdf_scan_details(client, system_id, scan_id)

            # Optimize error checking with early return pattern
            if 'error' in scan:
                module.fail_json(msg="Failed to get scan details: {}".format(scan['error']))

            module.exit_json(
                changed=False,
                msg="OpenSCAP XCCDF scan details retrieved successfully",
                scan=scan
            )
        else:
            # List all scans for the system
            # Additional validation for listing operation
            if not system_id:
                module.fail_json(msg="'system_id' is required when listing scans")

            scans = list_xccdf_scans(client, system_id)
            module.exit_json(
                changed=False,
                msg="OpenSCAP XCCDF scan list retrieved successfully",
                scans=scans
            )
    except Exception as e:
        module.fail_json(msg="Failed to get OpenSCAP XCCDF scan information: {}".format(e))
    finally:
        # Ensure cleanup always happens
        client.logout()


if __name__ == '__main__':
    main()
