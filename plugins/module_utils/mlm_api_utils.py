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
This module provides shared utility functions for API interactions in SUSE Multi-Linux Manager.

It centralizes common patterns for making API requests, handling responses, and standardizing data,
reducing code duplication across other utility modules.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.suse.mlm.plugins.module_utils.mlm_client import check_api_response

def make_api_request(client, method, path, data=None, headers=None, module=None):
    """
    Make an API request with the specified method and handle the response.

    Args:
        client: The MLM client instance.
        method: The HTTP method (GET, POST, PUT, DELETE).
        path: The API endpoint path.
        data: Optional data to send with the request.
        headers: Optional headers to include with the request.
        module: The AnsibleModule instance for error handling (optional).

    Returns:
        dict or list: The parsed response from the API.

    Raises:
        AnsibleFailJson: If the request fails or returns an error, and a module is provided.
    """
    try:
        if method == "GET":
            response = client.get(path, headers=headers)
        elif method == "POST":
            response = client.post(path, data=data, headers=headers)
        elif method == "PUT":
            response = client.put(path, data=data, headers=headers)
        elif method == "DELETE":
            response = client.delete(path, headers=headers)
        else:
            if module:
                module.fail_json(msg=f"Unsupported HTTP method: {method}")
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Handle case where response is None or not a dict/list
        if response is None:
            if module:
                module.fail_json(msg=f"API request to {path} returned no response")
            raise ValueError(f"API request to {path} returned no response")

        return response
    except Exception as e:
        if module:
            module.fail_json(msg=f"API request to {path} failed: {str(e)}")
        raise


def standardize_data(data, mapping):
    """
    Standardize data format using a provided mapping.

    Args:
        data: The raw data from the API (dict, list, or str).
        mapping: A dictionary mapping standardized keys to API keys or tuples for nested keys.

    Returns:
        dict or list: The standardized data.
    """
    if not data:
        return {}

    # Handle list input
    if isinstance(data, list):
        return [standardize_data(item, mapping) for item in data]

    # Handle string or non-dict input
    if not isinstance(data, dict):
        standardized = {key: "" for key in mapping.keys()}
        if isinstance(data, str) and next(iter(mapping.keys())) == "label":
            standardized["label"] = data
        return standardized

    standardized = {}
    for std_key, api_key in mapping.items():
        if isinstance(api_key, tuple):
            # Handle nested dictionaries
            parent, child = api_key
            value = data.get(parent, {}).get(child, "") if isinstance(data.get(parent), dict) else ""
        else:
            value = data.get(api_key, "")
            if std_key == "id" and value == "":
                value = 0
        standardized[std_key] = value

    return standardized


def get_entity_by_field(client, path, field, value, module=None):
    """
    Get an entity by a specific field value from a list endpoint.

    Args:
        client: The MLM client instance.
        path: The API endpoint path to list entities.
        field: The field to match (e.g., 'id', 'name').
        value: The value to find.
        module: The AnsibleModule instance for error handling (optional).

    Returns:
        dict: The matching entity if found, None otherwise.
    """
    try:
        entities = make_api_request(client, "GET", path, module=module)
        if not entities:
            return None

        if isinstance(entities, dict) and "result" in entities:
            entities = entities["result"]

        if not isinstance(entities, list):
            return None

        for entity in entities:
            if entity.get(field) == value:
                return entity
        return None
    except Exception:
        return None
