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
This module provides utility functions for working with SCAP scanning in SUSE Multi-Linux Manager.

It contains common functions used by the scap_info and scap_scan modules to avoid code duplication.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Dict, List, Optional, Any
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    check_api_response,
)


def standardize_scan_data(scan_data: Dict[str, Any], include_results: bool = False) -> Dict[str, Any]:
    """
    Standardize the SCAP scan data format.

    Args:
        scan_data: The raw scan data from the API.
        include_results: Whether to include detailed scan results.

    Returns:
        dict: The standardized scan data.
    """
    if not scan_data:
        return {}

    standardized_scan = {
        "id": scan_data.get("id"),
        "name": scan_data.get("name", ""),
        "path": scan_data.get("path", ""),
        "profile": scan_data.get("profile", ""),
        "test_result": scan_data.get("testResult", ""),
        "created": scan_data.get("created", ""),
        "modified": scan_data.get("modified", ""),
        "benchmark": scan_data.get("benchmark", ""),
        "benchmark_version": scan_data.get("benchmarkVersion", ""),
        "profile_title": scan_data.get("profileTitle", ""),
        "oval_files": scan_data.get("ovalFiles", []),
        "parameters": scan_data.get("parameters", {}),
    }

    # Add results if requested
    if include_results and "results" in scan_data:
        standardized_scan["results"] = scan_data["results"]

    return standardized_scan


def list_xccdf_scans(client: Any, system_id: int) -> List[Dict[str, Any]]:
    """
    List XCCDF scans for a system.

    Args:
        client: The MLM client.
        system_id: The ID of the system.

    Returns:
        list: A list of standardized scan data.
    """
    path = "/system/scap/listXccdfScans"
    params = {"sid": system_id}
    scans = client.get(path, params=params)

    if not scans:
        return []

    if isinstance(scans, dict) and "result" in scans:
        scans = scans["result"]

    if not isinstance(scans, list):
        return []

    return [standardize_scan_data(scan) for scan in scans if isinstance(scan, dict)]


def get_xccdf_scan_details(client: Any, system_id: int, scan_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific XCCDF scan.

    Args:
        client: The MLM client.
        system_id: The ID of the system.
        scan_id: The ID of the scan.

    Returns:
        dict: The standardized scan details, or None if not found.
    """
    try:
        path = "/system/scap/getXccdfScanDetails"
        params = {"sid": system_id, "xid": scan_id}
        scan_details = client.get(path, params=params)

        if scan_details:
            return standardize_scan_data(scan_details, include_results=True)

        return None
    except Exception:
        return None


def schedule_xccdf_scan(
    client: Any,
    system_id: int,
    profile: str,
    path: str,
    parameters: Optional[Dict[str, str]] = None,
    oval_files: Optional[List[str]] = None,
    date: Optional[str] = None,
    module: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Schedule an XCCDF scan.

    Args:
        client: The MLM client.
        system_id: The ID of the system.
        profile: The SCAP profile to use.
        path: The path to the SCAP content.
        parameters: Optional parameters for the scan.
        oval_files: Optional list of OVAL files.
        date: Optional date to schedule the scan (ISO format).
        module: The AnsibleModule instance for error handling.

    Returns:
        dict: The result of the schedule operation.
    """
    api_path = "/system/scap/scheduleXccdfScan"

    # Prepare the data for the API call
    data = {
        "sid": system_id,
        "path": path,
        "profile": profile,
    }

    # Add optional parameters
    if parameters:
        data["parameters"] = parameters
    if oval_files:
        data["ovalFiles"] = oval_files
    if date:
        data["date"] = date

    # Make the API request
    result = client.post(api_path, data=data)

    # Check the API response if module is provided
    if module:
        check_api_response(result, "Schedule XCCDF scan", module)

    return result


def delete_xccdf_scan(client: Any, system_id: int, scan_id: int, module: Optional[Any] = None) -> Dict[str, Any]:
    """
    Delete an XCCDF scan.

    Args:
        client: The MLM client.
        system_id: The ID of the system.
        scan_id: The ID of the scan to delete.
        module: The AnsibleModule instance for error handling.

    Returns:
        dict: The result of the delete operation.
    """
    api_path = "/system/scap/deleteXccdfScan"

    # Prepare the data for the API call
    data = {
        "sid": system_id,
        "xid": scan_id,
    }

    # Make the API request
    result = client.post(api_path, data=data)

    # Check the API response if module is provided
    if module:
        check_api_response(result, "Delete XCCDF scan", module)

    return result
