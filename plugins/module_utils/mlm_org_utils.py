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
This module provides utility functions for working with organizations in SUSE Multi-Linux Manager.

It contains common functions used by the org and org_info modules to avoid code duplication.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    check_api_response,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_api_utils import (
    get_entity_by_field,
)


def get_organization(client, org_id=None, org_name=None):
    """
    Get an organization by ID or name.

    Args:
        client: The MLM client.
        org_id: The ID of the organization to find.
        org_name: The name of the organization to find.

    Returns:
        dict: The organization if found, None otherwise.
    """
    if org_id is None and org_name is None:
        return None

    orgs_path = "/org/listOrgs"
    if org_id is not None:
        return get_entity_by_field(client, orgs_path, "id", org_id)
    if org_name is not None:
        return get_entity_by_field(client, orgs_path, "name", org_name)
    return None


def get_organization_by_name(client, org_name):
    """
    Get an organization by name.

    Args:
        client: The MLM client.
        org_name: The name of the organization to find.

    Returns:
        dict: The organization if found, None otherwise.
    """
    return get_organization(client, org_name=org_name)


def get_organization_by_id(client, org_id):
    """
    Get an organization by ID.

    Args:
        client: The MLM client.
        org_id: The ID of the organization to find.

    Returns:
        dict: The organization if found, None otherwise.
    """
    return get_organization(client, org_id=org_id)


def standardize_org_data(org_data):
    """
    Standardize the organization data format.

    Args:
        org_data: The raw organization data from the API.

    Returns:
        dict: The standardized organization data.
    """
    if not org_data:
        return {}

    standardized_org = {
        "id": org_data.get("id"),
        "name": org_data.get("name"),
        "active_users": org_data.get("active_users", 0),
        "systems": org_data.get("systems", 0),
        "trusts": org_data.get("trusts", 0),
    }

    # Add optional fields if they exist
    if "system_groups" in org_data:
        standardized_org["system_groups"] = org_data["system_groups"]
    if "activation_keys" in org_data:
        standardized_org["activation_keys"] = org_data["activation_keys"]
    if "kickstart_profiles" in org_data:
        standardized_org["kickstart_profiles"] = org_data["kickstart_profiles"]
    if "configuration_channels" in org_data:
        standardized_org["configuration_channels"] = org_data["configuration_channels"]
    if "staging_content_enabled" in org_data:
        standardized_org["staging_content_enabled"] = org_data[
            "staging_content_enabled"
        ]

    return standardized_org


def list_organizations(client):
    """
    List all organizations.

    Args:
        client: The MLM client.

    Returns:
        list: A list of standardized organization data.
    """
    path = "/org/listOrgs"
    orgs = client.get(path)
    if not orgs:
        return []

    if isinstance(orgs, dict) and "result" in orgs:
        orgs = orgs["result"]

    if not isinstance(orgs, list):
        return []

    return [standardize_org_data(org) for org in orgs if isinstance(org, dict)]


def get_organization_details(client, org_id=None, org_name=None):
    """
    Get detailed information about a specific organization.

    Args:
        client: The MLM client.
        org_id: The ID of the organization to get details for.
        org_name: The name of the organization to get details for.

    Returns:
        dict: The standardized organization details.
    """
    try:
        # If org_id is provided, try to get the organization by ID
        if org_id is not None:
            org = get_organization_by_id(client, org_id)
            if org:
                return standardize_org_data(org)

        # If org_name is provided, try to get the organization by name
        if org_name:
            org = get_organization_by_name(client, org_name)
            if org:
                return standardize_org_data(org)

        # If we get here, we couldn't find the organization
        return {
            "id": org_id,
            "name": org_name,
            "active_users": 0,
            "systems": 0,
            "trusts": 0,
        }
    except Exception as e:
        # Return a minimal organization object on error
        return {
            "id": org_id,
            "name": org_name,
            "active_users": 0,
            "systems": 0,
            "trusts": 0,
            "error": str(e),
        }


def create_organization(module, client):
    """
    Create a new organization.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """

    # Extract module parameters
    org_name = module.params["org_name"]
    admin_login = module.params["admin_login"]
    admin_password = module.params["admin_password"]
    first_name = module.params["first_name"]
    last_name = module.params["last_name"]
    email = module.params["email"]
    prefix = module.params.get("prefix")
    use_pam_auth = module.params["use_pam_auth"]

    # Check if the organization already exists
    org = get_organization_by_name(client, org_name)
    if org:
        return False, org, "Organization '{}' already exists".format(org_name)

    # If check_mode is enabled, return now
    if module.check_mode:
        return (
            True,
            {"name": org_name},
            "Organization '{}' would be created".format(org_name),
        )

    # Create the organization using SUSE Multi-Linux Manager API
    # Prepare the request data
    create_data = {
        "orgName": org_name,
        "adminLogin": admin_login,
        "adminPassword": admin_password,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "usePamAuth": use_pam_auth,
    }

    # Add prefix if provided
    if prefix:
        create_data["prefix"] = prefix

    # Make the API request
    create_path = "/org/create"
    result = client.post(create_path, data=create_data)
    check_api_response(result, "Create organization", module)

    return (
        True,
        result,
        "Organization '{}' created successfully".format(org_name),
    )


def delete_organization(module, client):
    """
    Delete an organization.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """

    # Extract module parameters
    org_id = module.params.get("org_id")
    org_name = module.params.get("org_name")

    # Find the organization
    org = None
    if org_id is not None:
        org = get_organization_by_id(client, org_id)
        if not org:
            return False, None, "Organization with ID {} does not exist".format(org_id)
    elif org_name:
        org = get_organization_by_name(client, org_name)
        if not org:
            return False, None, "Organization '{}' does not exist".format(org_name)
    else:
        module.fail_json(
            msg="Either org_id or org_name must be specified when state=absent"
        )

    # Get the organization ID
    org_id = org["id"]
    org_name = org["name"]

    # If check_mode is enabled, return now
    if module.check_mode:
        return (
            True,
            None,
            "Organization '{}' (ID: {}) would be deleted".format(org_name, org_id),
        )

    # Delete the organization
    try:
        # Make the API request
        delete_path = "/org/delete"
        result = client.post(delete_path, data={"orgId": org_id})
        check_api_response(result, "Delete organization", module)

        return (
            True,
            None,
            "Organization '{}' (ID: {}) deleted successfully".format(org_name, org_id),
        )
    except Exception as e:
        module.fail_json(msg="Failed to delete organization: {}".format(str(e)))
