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

from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import check_api_response

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
        entities = client.get(path)
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
