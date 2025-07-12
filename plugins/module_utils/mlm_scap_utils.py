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

"""
This module provides utility functions for working with OpenSCAP scans in SUSE Multi-Linux Manager.

It contains common functions used by the scap_scan and scap_info modules to avoid code duplication.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    check_api_response,
)


def standardize_scan_data(scan_data, include_results=False):
    """
    Standardize the scan data format.

    Args:
        scan_data (dict): The raw scan data from the API.
        include_results (bool): Whether to include detailed results.

    Returns:
        dict: The standardized scan data.
    """
    if not scan_data:
        return {}

    # Optimized field mapping using dictionary comprehension
    basic_field_map = {
        "id": "xid",
        "system_id": "sid",
        "action_id": "action_id",
        "profile": "profile",
        "path": "path",
        "command_line_arguments": "oscap_parameters",
        "oval_files": "ovalfiles",
        "started": "start_time",
        "completed": "end_time",
        "created": "start_time",
        "benchmark_identifier": "benchmark",
        "benchmark_version": "benchmark_version",
        "profile_identifier": "profile",
        "profile_title": "profile_title",
        "test_result": "test_result",
        "error_details": "errors",
        "deletable": "deletable"
    }

    # Efficiently map basic fields
    standardized_scan = {
        key: scan_data.get(source_key)
        for key, source_key in basic_field_map.items()
        if scan_data.get(source_key) is not None
    }

    # Add detailed results if requested
    if include_results:
        # Direct field mappings for result data
        result_field_map = {
            "results": "results",
            "result_files": "resultFiles",
            "test_results": "testResults",
            "rule_results": "ruleResults"
        }

        # Add result fields that exist
        standardized_scan.update({
            key: scan_data[source_key]
            for key, source_key in result_field_map.items()
            if source_key in scan_data
        })

        # Add scoring and detailed fields efficiently
        scoring_fields = {
            "score", "maxScore", "passedRules", "failedRules", "errorRules",
            "unknownRules", "notApplicableRules", "notCheckedRules", "notSelectedRules",
            "informationalRules", "fixedRules", "totalRules", "parameters",
            "returnCode", "stderr", "stdout"
        }

        standardized_scan.update({
            field: scan_data[field]
            for field in scoring_fields
            if field in scan_data
        })

    return standardized_scan


def list_xccdf_scans(client, system_id):
    """
    List all OpenSCAP XCCDF scans for a system.

    Args:
        client: The MLM client.
        system_id: The ID of the system to get scans for.

    Returns:
        list: A list of scan dictionaries.
    """
    try:
        # Make the API request
        path = f"/system/scap/listXccdfScans?sid={system_id}"
        response = client.get(path)

        # Handle case where response is None or not a list
        if not response:
            return []

        # Extract data from wrapper if needed
        if isinstance(response, dict) and "result" in response:
            response = response["result"]
        elif not isinstance(response, list):
            return []

        # Efficiently standardize scan data using list comprehension
        return [
            standardize_scan_data(scan)
            for scan in response
            if isinstance(scan, dict)
        ]
    except Exception:
        return []


def get_xccdf_scan_details(client, system_id, scan_id):
    """
    Get detailed information about a specific OpenSCAP XCCDF scan.

    Args:
        client: The MLM client.
        system_id: The ID of the system the scan was run on.
        scan_id: The ID of the scan to get details for.

    Returns:
        dict: The scan details.
    """
    try:
        # Make the API request - only xid parameter needed according to API docs
        path = f"/system/scap/getXccdfScanDetails?xid={scan_id}"
        response = client.get(path)

        # Check if response is None or empty
        if not response:
            return {
                "id": scan_id,
                "system_id": system_id,
                "error": "Scan not found or no details available"
            }

        # Extract scan data from wrapper efficiently
        scan_data = (
            response.get("result", response)
            if isinstance(response, dict) and "result" in response
            else response
        )

        # Standardize and return the scan data
        return standardize_scan_data(scan_data, include_results=True)
    except Exception as e:
        return {
            "id": scan_id,
            "system_id": system_id,
            "error": str(e)
        }


def schedule_xccdf_scan(client, system_id, profile, path, parameters=None, oval_files=None, date=None, module=None):
    """
    Schedule an OpenSCAP XCCDF scan.

    Args:
        client: The MLM client.
        system_id: The ID of the system to scan.
        profile: The XCCDF profile to use.
        path: The path to the XCCDF document.
        parameters: Optional parameters for the scan.
        oval_files: Optional list of additional OVAL files for the oscap tool.
        date: Optional date to schedule the action (ISO8601 format).
        module: The AnsibleModule instance for error handling (optional).

    Returns:
        dict: The scan result.
    """
    # Prepare the oscap parameters string
    oscap_params = "--profile {}".format(profile)

    # Add additional parameters if provided
    if parameters:
        for key, value in parameters.items():
            oscap_params += " --{} {}".format(key, value)

    # Add oval_files if provided
    if oval_files:
        for oval_file in oval_files:
            oscap_params += " --oval-definitions {}".format(oval_file)

    # Prepare the request data
    data = {
        "sid": system_id,
        "xccdfPath": path,
        "oscapParams": oscap_params
    }

    # Add date if provided
    if date:
        data["date"] = date

    # Make the API request
    api_path = "/system/scap/scheduleXccdfScan"
    result = client.post(api_path, data=data)
    if module:
        check_api_response(result, "Schedule XCCDF scan", module)

    # Extract the scan ID from the result
    scan_id = None
    if isinstance(result, dict):
        scan_id = result.get("id")
    elif isinstance(result, int):
        scan_id = result

    # Create the scan result
    scan_result = {
        "id": scan_id,
        "profile": profile,
        "path": path,
        "parameters": parameters or {},
        "oval_files": oval_files,
        "date": date
    }

    return scan_result


def delete_xccdf_scan(client, system_id, scan_id, module=None):
    """
    Delete an OpenSCAP XCCDF scan.

    Args:
        client: The MLM client.
        system_id: The ID of the system the scan was run on.
        scan_id: The ID of the scan to delete.
        module: The AnsibleModule instance for error handling (optional).

    Returns:
        bool: True if the scan was deleted successfully.
    """
    # Make the API request
    path = "/system/scap/deleteXccdfScan"
    result = client.post(path, data={"sid": system_id, "xid": scan_id})
    if module:
        check_api_response(result, "Delete XCCDF scan", module)

    # If no exception was raised, the scan was deleted successfully
    return True
