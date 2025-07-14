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

from typing import Dict, List, Optional, Any
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_api_utils import (
    get_entity_by_field,
)


def standardize_channel_data(channel_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Standardize the channel data format.

    Args:
        channel_data: The raw channel data from the API.

    Returns:
        dict: The standardized channel data.
    """
    if not channel_data:
        return {}

    # Handle different possible field names for parent channel
    # Try multiple possible field names from the API response
    parent_channel_label = ""

    # List of possible field names for parent channel information
    parent_field_names = [
        "parent_channel_label",
        "parent_channel",
        "parent_label",
        "parentChannelLabel",
        "parentChannel",
        "parent",
        "parent_id",
        "parentId",
        "parent_name",
        "parentName",
        "base_channel",
        "baseChannel",
        "base_channel_label",
        "baseChannelLabel"
    ]

    # Try each possible field name
    for field_name in parent_field_names:
        if field_name in channel_data and channel_data[field_name]:
            parent_channel_label = str(channel_data[field_name])
            break

    # If we still don't have a parent channel label, check if this is a child channel
    # by looking for patterns in the label or name that might indicate a parent
    if not parent_channel_label and channel_data.get("label"):
        label = channel_data.get("label", "")
        # For child channels, the parent is often the base part of the label
        # e.g., "ubuntu-2404-amd64-main-updates-amd64" -> "ubuntu-2404-amd64-main-amd64"
        if "-updates" in label:
            parent_channel_label = label.replace("-updates", "")
        elif "-installer" in label:
            parent_channel_label = label.replace("-installer", "")
        elif "-extras" in label:
            parent_channel_label = label.replace("-extras", "")
        elif "-optional" in label:
            parent_channel_label = label.replace("-optional", "")

    return {
        "id": channel_data.get("id"),
        "label": channel_data.get("label"),
        "name": channel_data.get("name", ""),
        "summary": channel_data.get("summary", ""),
        "description": channel_data.get("description", ""),
        "arch_name": channel_data.get("arch_name", ""),
        "last_modified": channel_data.get("last_modified", ""),
        "maintainer_name": channel_data.get("maintainer_name", ""),
        "maintainer_email": channel_data.get("maintainer_email", ""),
        "support_policy": channel_data.get("support_policy", ""),
        "gpg_key_url": channel_data.get("gpg_key_url", ""),
        "gpg_key_id": channel_data.get("gpg_key_id", ""),
        "gpg_key_fp": channel_data.get("gpg_key_fp", ""),
        "parent_channel_label": parent_channel_label,
        "clone_original": channel_data.get("clone_original", ""),
        "provider_name": channel_data.get("provider_name", ""),
        "package_count": channel_data.get("package_count", 0),
        "globally_subscribable": channel_data.get("globally_subscribable", False),
    }


def list_channels(client: Any) -> List[Dict[str, Any]]:
    """
    List all channels.

    Args:
        client: The MLM client.

    Returns:
        list: A list of standardized channel data.

    Raises:
        Exception: If there's an error retrieving channels from the API.
    """
    try:
        channels = client.get("/channel/listAllChannels")
        if not channels:
            return []

        if isinstance(channels, dict) and "result" in channels:
            channels = channels["result"]

        if not isinstance(channels, list):
            return []

        return [
            standardize_channel_data(channel) for channel in channels if isinstance(channel, dict)
        ]
    except Exception as e:
        raise Exception("Failed to list channels: {}".format(str(e)))


def get_channel_details(
    client: Any,
    channel_id: Optional[int] = None,
    channel_label: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific channel using getDetails method.

    Args:
        client: The MLM client.
        channel_id: The ID of the channel to get details for.
        channel_label: The label of the channel to get details for.

    Returns:
        dict: The standardized channel details, or None if not found.

    Raises:
        Exception: If there's an error retrieving channel details from the API.
    """
    if channel_id is None and channel_label is None:
        raise Exception("Either channel_id or channel_label must be provided")

    try:
        # First, get basic channel info and ensure we have both ID and label
        target_channel_id = channel_id
        target_channel_label = channel_label

        # If we only have label, get the ID first
        if channel_label is not None and channel_id is None:
            channel = get_entity_by_field(client, "/channel/listAllChannels", "label", channel_label)
            if channel:
                target_channel_id = channel.get("id")
            else:
                return None

        # If we only have ID, get the label first
        if channel_id is not None and channel_label is None:
            channel = get_entity_by_field(client, "/channel/listAllChannels", "id", channel_id)
            if channel:
                target_channel_label = channel.get("label")
            else:
                return None

        # Start with basic channel data from listAllChannels
        base_channel_data = get_entity_by_field(client, "/channel/listAllChannels", "label", target_channel_label)
        if not base_channel_data:
            return None

        # Use getDetails method to get full channel information
        final_data = base_channel_data.copy()

        try:
            # Method: getDetails
            # HTTP GET
            # Parameters: string sessionKey, int id
            # Returns: struct channel with all detailed fields
            detailed_info = client.get("/channel/software/getDetails", params={"id": target_channel_id})

            if detailed_info and isinstance(detailed_info, dict):
                # Check if we got meaningful data from getDetails
                if detailed_info.get("id") or detailed_info.get("label") or detailed_info.get("name"):
                    # Merge detailed info with base data
                    final_data.update(detailed_info)
                elif "result" in detailed_info:
                    # Handle case where result is wrapped in a result field
                    result_data = detailed_info["result"]
                    if isinstance(result_data, dict) and (result_data.get("id") or result_data.get("label") or result_data.get("name")):
                        final_data.update(result_data)

        except Exception:
            # If getDetails fails, continue with base data
            pass

        # Add package count if we have the channel label
        if target_channel_label:
            package_count = 0
            try:
                params = {"channelLabel": target_channel_label}
                packages = client.get("/channel/software/listAllPackages", params=params)
                if packages and isinstance(packages, list):
                    package_count = len(packages)
                elif packages and isinstance(packages, dict):
                    if "result" in packages and isinstance(packages["result"], list):
                        package_count = len(packages["result"])
                    elif "data" in packages and isinstance(packages["data"], list):
                        package_count = len(packages["data"])
            except Exception:
                pass

            final_data["package_count"] = package_count

        return standardize_channel_data(final_data)

    except Exception as e:
        raise Exception("Failed to get channel details: {}".format(str(e)))


def get_channel_by_label(client: Any, channel_label: str) -> Optional[Dict[str, Any]]:
    """
    Get a channel by its label.

    Args:
        client: The MLM client.
        channel_label: The label of the channel to retrieve.

    Returns:
        dict: The channel data, or None if not found.

    Raises:
        Exception: If there's an error retrieving the channel from the API.
    """
    return get_entity_by_field(client, "/channel/listAllChannels", "label", channel_label)
