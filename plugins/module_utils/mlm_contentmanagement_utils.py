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
This module provides utility functions for working with content management in SUSE Multi-Linux Manager.

It contains common functions used by the contentproject and contentproject_info modules to avoid code duplication.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Dict, List, Optional, Any
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    check_api_response,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_api_utils import (
    get_entity_by_field,
)


def get_content_project(client, project_label=None):
    """
    Get a content project by label.

    This function retrieves a content project from SUSE Multi-Linux Manager
    by its label and returns the project data.

    Args:
        client: The MLM client instance for making API calls.
        project_label (str): The label of the content project to find.

    Returns:
        dict: The content project if found, None otherwise.

    Examples:
        >>> project = get_content_project(client, "my-project")
        >>> if project:
        ...     print("Found project: {}".format(project["name"]))
    """
    if project_label is None:
        return None

    projects_path = "/contentmanagement/listProjects"
    return get_entity_by_field(client, projects_path, "label", project_label)


def get_content_project_by_label(client, project_label):
    """
    Get a content project by label.

    Args:
        client: The MLM client instance for making API calls.
        project_label (str): The label of the content project to find.

    Returns:
        dict: The content project if found, None otherwise.
    """
    return get_content_project(client, project_label=project_label)


def standardize_content_project_data(project_data, client=None):
    """
    Standardize the content project data format.

    This function converts content project data from the API into a consistent
    format with standardized field names and proper handling of various data types.

    Args:
        project_data: The raw content project data from the API.
        client: The MLM client (optional, for future use).

    Returns:
        dict: The standardized content project data.

    Examples:
        >>> project = {"label": "test", "name": "Test Project"}
        >>> standardized = standardize_content_project_data(project)
        >>> print(standardized["label"])
        test
    """
    if not project_data:
        return {}

    standardized_project = {
        "label": project_data.get("label", ""),
        "name": project_data.get("name", ""),
        "description": project_data.get("description", ""),
        "first_environment": "",
        "created": project_data.get("created", ""),
        "modified": project_data.get("lastModified", project_data.get("modified", "")),
    }

    # Handle special case for firstEnvironment
    if "firstEnvironment" in project_data:
        first_env = project_data["firstEnvironment"]
        if isinstance(first_env, dict) and "label" in first_env:
            standardized_project["first_environment"] = first_env["label"]
        else:
            standardized_project["first_environment"] = (
                str(first_env) if first_env else ""
            )

    return standardized_project


def list_content_projects(client):
    """
    List all content projects.

    This function retrieves all content projects from SUSE Multi-Linux Manager
    and returns a list of standardized project data.

    Args:
        client: The MLM client instance for making API calls.

    Returns:
        list: A list of standardized content project data.

    Examples:
        >>> projects = list_content_projects(client)
        >>> for project in projects:
        ...     print("Project: {}".format(project["label"]))
    """
    path = "/contentmanagement/listProjects"

    projects = client.get(path)
    if not projects:
        return []

    if isinstance(projects, dict) and "result" in projects:
        projects = projects["result"]

    if not isinstance(projects, list):
        return []

    return [
        standardize_content_project_data(project, client)
        for project in projects
        if isinstance(project, dict)
    ]


def get_content_project_details(client, project_label):
    """
    Get detailed information about a specific content project.

    This function retrieves detailed information about a content project
    identified by its label and returns standardized project data.

    Args:
        client: The MLM client instance for making API calls.
        project_label (str): The label of the content project to get details for.

    Returns:
        dict: The standardized content project details.

    Examples:
        >>> details = get_content_project_details(client, "my-project")
        >>> print("Project name: {}".format(details["name"]))
    """
    try:
        # Try to get the content project by label
        project = get_content_project_by_label(client, project_label)
        if project:
            return standardize_content_project_data(project, client)

        # If we get here, we couldn't find the content project
        return {
            "label": project_label,
            "name": "",
            "description": "",
            "first_environment": "",
            "created": "",
            "modified": "",
        }
    except Exception as e:
        # Return a minimal content project object on error
        return {
            "label": project_label,
            "name": "",
            "description": "",
            "first_environment": "",
            "created": "",
            "modified": "",
            "error": str(e),
        }


def attach_source_to_project(
    client, project_label, source_type, source_label, source_position=0
):
    """
    Attach a source to a content project.

    Args:
        client: The MLM client instance for making API calls.
        project_label (str): The label of the content project.
        source_type (str): The type of the source ('software' or 'config').
        source_label (str): The label of the source.
        source_position (int): The position of the source in the project.

    Returns:
        dict: The result of the attach operation.

    Examples:
        >>> result = attach_source_to_project(client, "my-project", "software", "sles15-sp4-pool", 0)
        >>> print("Attached: {}".format(result))
    """
    path = "/contentmanagement/attachSource"
    data = {
        "projectLabel": project_label,
        "sourceType": source_type,
        "sourceLabel": source_label,
        "sourcePosition": source_position,
    }
    return client.post(path, data=data)


def detach_source_from_project(client, project_label, source_type, source_label):
    """
    Detach a source from a content project.

    Args:
        client: The MLM client instance for making API calls.
        project_label (str): The label of the content project.
        source_type (str): The type of the source ('software' or 'config').
        source_label (str): The label of the source.

    Returns:
        dict: The result of the detach operation.

    Examples:
        >>> result = detach_source_from_project(client, "my-project", "software", "sles15-sp4-pool")
        >>> print("Detached: {}".format(result))
    """
    path = "/contentmanagement/detachSource"
    data = {
        "projectLabel": project_label,
        "sourceType": source_type,
        "sourceLabel": source_label,
    }
    return client.post(path, data=data)


def list_project_sources(client, project_label, source_type=None):
    """
    List sources in a content project.

    Args:
        client: The MLM client instance for making API calls.
        project_label (str): The label of the content project.
        source_type (str, optional): Filter by source type ('software' or 'config').

    Returns:
        list: A list of sources in the project.

    Examples:
        >>> sources = list_project_sources(client, "my-project")
        >>> for source in sources:
        ...     print("Source: {}".format(source["channelLabel"]))
    """
    path = "/contentmanagement/listProjectSources"
    params = {"projectLabel": project_label}

    sources = client.get(path, params=params)

    if not sources:
        return []

    if not isinstance(sources, list):
        sources = [sources] if sources else []

    # Filter by source type if specified
    if source_type:
        filtered_sources = []
        for source in sources:
            if isinstance(source, dict) and source.get("type") == source_type:
                filtered_sources.append(source)
        return filtered_sources

    return sources


def standardize_content_source_data(source_data):
    """
    Standardize content source data format.

    Args:
        source_data: The raw source data from the API.

    Returns:
        dict: The standardized source data.

    Examples:
        >>> source = {"sourceLabel": "test", "type": "software"}
        >>> standardized = standardize_content_source_data(source)
        >>> print(standardized["label"])
        test
    """
    if not source_data:
        return {}

    if isinstance(source_data, str):
        return {
            "label": source_data,
            "name": source_data,
            "type": "unknown",
            "state": "attached",
            "project_label": "",
            "channel_label": source_data,
        }

    standardized_source = {
        "label": source_data.get("sourceLabel", source_data.get("label", "")),
        "name": source_data.get(
            "name", source_data.get("sourceLabel", source_data.get("label", ""))
        ),
        "type": source_data.get("type", source_data.get("sourceType", "unknown")),
        "state": source_data.get("state", "attached"),
        "project_label": source_data.get("contentProjectLabel", ""),
        "channel_label": source_data.get(
            "channelLabel", source_data.get("sourceLabel", source_data.get("label", ""))
        ),
    }

    return standardized_source
