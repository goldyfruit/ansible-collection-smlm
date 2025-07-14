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

# Make coding more python3-ish

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: contentproject
short_description: Manage content projects in SUSE Multi-Linux Manager
description:
  - Create, update, or delete content projects in SUSE Multi-Linux Manager.
  - Build and promote content projects.
  - This module uses the SUSE Multi-Linux Manager API to manage content projects.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  label:
    description:
      - Label of the content project.
      - Required for all operations.
    type: str
    required: true
  name:
    description:
      - Name of the content project.
      - Required when creating a new project.
      - Optional when updating an existing project.
    type: str
    required: false
  description:
    description:
      - Description of the content project.
      - Optional when creating or updating a project.
    type: str
    required: false
  build:
    description:
      - Whether to build the content project.
      - Only used when state=build.
    type: bool
    default: false
    required: false
  force_build:
    description:
      - Whether to force the build of the content project.
      - Only used when state=build.
    type: bool
    default: false
    required: false
  target_environment:
    description:
      - Label of the target environment to promote the content project to.
      - Required when state=promote.
    type: str
    required: false
  state:
    description:
      - Whether the content project should exist or not.
      - When C(present), the project will be created if it doesn't exist, or updated if it does.
      - When C(absent), the project will be deleted.
      - When C(build), the project will be built.
      - When C(promote), the project will be promoted to the target environment.
    type: str
    choices: [ present, absent, build, promote ]
    default: present
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have the appropriate permissions to manage content projects.
  - Content projects must have unique labels.
  - When deleting a content project, all associated environments, filters, and sources will also be deleted.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Using credentials configuration file (recommended)
- name: Create a new content project using credentials file
  goldyfruit.mlm.contentproject:
    label: "dev-project"
    name: "Development Project"
    description: "Content project for development"
    state: present
  register: project_result

- name: Update an existing content project using credentials file
  goldyfruit.mlm.contentproject:
    label: "dev-project"
    name: "Development Project Updated"
    description: "Updated content project for development"
    state: present
  register: update_result

- name: Build a content project using credentials file
  goldyfruit.mlm.contentproject:
    label: "dev-project"
    build: true
    force_build: false
    state: build
  register: build_result

- name: Promote a content project to an environment using credentials file
  goldyfruit.mlm.contentproject:
    label: "dev-project"
    target_environment: "test"
    state: promote
  register: promote_result

- name: Delete a content project using credentials file
  goldyfruit.mlm.contentproject:
    label: "dev-project"
    state: absent
  register: delete_result

# Using environment variables
- name: Create content project using environment variables
  goldyfruit.mlm.contentproject:
    label: "prod-project"
    name: "Production Project"
    description: "Content project for production"
    state: present
  environment:
    MLM_URL: "https://mlm.example.com"
    MLM_USERNAME: "admin"
    MLM_PASSWORD: "{{ vault_mlm_password }}"

# Using specific instance from credentials file
- name: Create content project using specific instance
  goldyfruit.mlm.contentproject:
    instance: staging
    label: "staging-project"
    name: "Staging Project"
    description: "Content project for staging environment"
    state: present
"""

RETURN = r"""
project:
  description: Information about the content project.
  returned: when state=present
  type: dict
  contains:
    label:
      description: Label of the content project.
      type: str
      sample: "dev-project"
    name:
      description: Name of the content project.
      type: str
      sample: "Development Project"
    description:
      description: Description of the content project.
      type: str
      sample: "Content project for development"
    first_environment:
      description: Label of the first environment in the project.
      type: str
      sample: "dev"
    created:
      description: Timestamp when the project was created.
      type: str
      sample: "2025-01-01T12:00:00Z"
    modified:
      description: Timestamp when the project was last modified.
      type: str
      sample: "2025-01-01T12:00:00Z"
build_result:
  description: Information about the build result.
  returned: when state=build
  type: dict
  contains:
    success:
      description: Whether the build was successful.
      type: bool
      sample: true
    message:
      description: Message about the build result.
      type: str
      sample: "Project built successfully"
promote_result:
  description: Information about the promote result.
  returned: when state=promote
  type: dict
  contains:
    success:
      description: Whether the promotion was successful.
      type: bool
      sample: true
    message:
      description: Message about the promotion result.
      type: str
      sample: "Project promoted successfully"
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "Content project created successfully"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_contentmanagement_utils import (
    get_content_project_by_label,
    standardize_content_project_data,
    list_content_projects,
    get_content_project_details,
)


def check_project_exists_by_label(client, label):
    """
    Check if a content project exists by its label.
    This function uses the available utility functions.

    Args:
        client: The MLM client.
        label (str): The label of the content project.

    Returns:
        tuple: (exists, project_data)
    """
    try:
        # Use the available utility function
        existing_project = get_content_project_by_label(client, label)

        if existing_project:
            # Standardize the project data
            standardized = standardize_content_project_data(existing_project)
            return True, standardized
        else:
            return False, {}
    except Exception:
        # If that fails, try listing all projects and finding the match
        try:
            projects = list_content_projects(client)
            for project in projects:
                if project.get("label") == label:
                    return True, project
        except Exception:
            pass
        return False, {}


def create_or_update_project(module, client):
    """
    Create or update a content project.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    label = module.params["label"]
    name = module.params.get("name")
    description = module.params.get("description")

    # Make sure we have a name for creating a new project
    if not name:
        module.fail_json(msg="Name is required when creating a new content project")

    # Check if the project exists using our enhanced function
    project_exists, existing_project = check_project_exists_by_label(client, label)

    # Debug output
    module.log("Project exists: {}".format(project_exists))
    module.log("Existing project type: {}".format(type(existing_project)))
    module.log("Existing project content: {}".format(existing_project))

    # If the project exists, check if it needs to be updated
    if project_exists:
        needs_update = False

        # Create a basic project dictionary if existing_project is not a dictionary
        if not isinstance(existing_project, dict):
            module.log(
                "Converting existing_project to dictionary: {}".format(existing_project)
            )
            if isinstance(existing_project, str):
                existing_project = {"label": existing_project}
            else:
                existing_project = {"label": label}

        # Only check name and description if they are provided
        if name and existing_project.get("name") != name:
            needs_update = True

        if (
            description is not None
            and existing_project.get("description") != description
        ):
            needs_update = True

        if not needs_update:
            # Project exists and doesn't need to be updated
            # Create a basic project dictionary with the information we know
            basic_project = {
                "label": label,
                "name": name or existing_project.get("name", ""),
                "description": description or existing_project.get("description", ""),
                "first_environment": existing_project.get("first_environment", ""),
                "created": existing_project.get("created", ""),
                "modified": existing_project.get("modified", ""),
            }
            return (
                False,
                basic_project,
                "Content project already exists with the same properties",
            )

        # Project exists but needs to be updated
        try:
            # Update the project using direct API call
            update_data = {
                "projectLabel": label,
                "name": name,
                "description": description or existing_project.get("description", "")
            }
            path = "/contentmanagement/updateProject"
            client.post(path, data=update_data)

            # Create a basic project dictionary with the information we know
            basic_project = {
                "label": label,
                "name": name or existing_project.get("name", ""),
                "description": description or existing_project.get("description", ""),
                "first_environment": existing_project.get("first_environment", ""),
                "created": existing_project.get("created", ""),
                "modified": existing_project.get("modified", ""),
            }

            return True, basic_project, "Content project updated successfully"
        except Exception as update_e:
            module.fail_json(
                msg="Failed to update content project: {}".format(str(update_e))
            )
    else:
        # Project doesn't exist, create it
        try:
            # Create the project using direct API call
            # Note: API expects projectLabel, not label
            create_data = {
                "projectLabel": label,
                "name": name,
                "description": description or ""
            }
            path = "/contentmanagement/createProject"
            client.post(path, data=create_data)

            # Create a basic project dictionary with the information we know
            basic_project = {
                "label": label,
                "name": name,
                "description": description or "",
                "first_environment": "",
                "created": "",
                "modified": "",
            }

            return True, basic_project, "Content project created successfully"
        except Exception as create_e:
            # For errors, fail
            module.fail_json(
                msg="Failed to create content project: {}".format(str(create_e))
            )


def delete_project_handler(module, client):
    """
    Delete a content project.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    label = module.params["label"]

    # Check if the project exists using our enhanced function
    project_exists, _ = check_project_exists_by_label(client, label)

    # If check_mode is enabled, return now
    if module.check_mode:
        if project_exists:
            return True, None, "Content project '{}' would be deleted".format(label)
        return False, None, "Content project '{}' does not exist".format(label)

    # Delete the project
    try:
        if project_exists:
            # Delete the project using direct API call
            delete_data = {"projectLabel": label}
            path = "/contentmanagement/removeProject"
            client.post(path, data=delete_data)
            return True, None, "Content project '{}' deleted successfully".format(label)
        return False, None, "Content project '{}' does not exist".format(label)
    except Exception as e:
        module.fail_json(msg="Failed to delete content project: {}".format(str(e)))


def build_project_handler(module, client):
    """
    Build a content project.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    label = module.params["label"]
    force = module.params.get("force_build", False)

    # Check if the project exists using our enhanced function
    project_exists, _ = check_project_exists_by_label(client, label)

    if not project_exists:
        module.fail_json(msg="Content project '{}' does not exist".format(label))

    # If check_mode is enabled, return now
    if module.check_mode:
        return (
            True,
            {
                "success": True,
                "message": "Content project '{}' would be built".format(label),
            },
            "Content project '{}' would be built".format(label),
        )

    # Build the project
    try:
        # Build the project using direct API call
        build_data = {
            "projectLabel": label,
            "force": force
        }
        path = "/contentmanagement/buildProject"
        client.post(path, data=build_data)
        return (
            True,
            {
                "success": True,
                "message": "Content project '{}' built successfully".format(label),
            },
            "Content project '{}' built successfully".format(label),
        )
    except Exception as e:
        module.fail_json(msg="Failed to build content project: {}".format(str(e)))


def promote_project_handler(module, client):
    """
    Promote a content project to an environment.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)
    """
    # Extract module parameters
    label = module.params["label"]
    target_environment = module.params.get("target_environment")

    if not target_environment:
        module.fail_json(
            msg="Target environment is required when promoting a content project"
        )

    # Check if the project exists using our enhanced function
    project_exists, _ = check_project_exists_by_label(client, label)

    if not project_exists:
        module.fail_json(msg="Content project '{}' does not exist".format(label))

    # If check_mode is enabled, return now
    if module.check_mode:
        return (
            True,
            {
                "success": True,
                "message": "Content project '{}' would be promoted to environment '{}'".format(
                    label, target_environment
                ),
            },
            "Content project '{}' would be promoted to environment '{}'".format(
                label, target_environment
            ),
        )

    # Promote the project
    try:
        # Promote the project using direct API call
        promote_data = {
            "projectLabel": label,
            "environmentLabel": target_environment
        }
        path = "/contentmanagement/promoteProject"
        client.post(path, data=promote_data)
        return (
            True,
            {
                "success": True,
                "message": "Content project '{}' promoted to environment '{}' successfully".format(
                    label, target_environment
                ),
            },
            "Content project '{}' promoted to environment '{}' successfully".format(
                label, target_environment
            ),
        )
    except Exception as e:
        module.fail_json(msg="Failed to promote content project: {}".format(str(e)))


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Creates the MLM client and logs in to the API
    3. Determines the action to take based on the 'state' parameter
    4. Calls the appropriate function to perform the action
    5. Returns the result to Ansible
    6. Ensures proper logout from the API

    The module supports check mode, which allows for dry runs without making
    actual changes to the system.

    Supported states:
    - present: Create or update a content project
    - absent: Delete a content project
    - build: Build a content project
    - promote: Promote a content project to an environment
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        label=dict(type="str", required=True),
        name=dict(type="str", required=False),
        description=dict(type="str", required=False),
        build=dict(type="bool", default=False, required=False),
        force_build=dict(type="bool", default=False, required=False),
        target_environment=dict(type="str", required=False),
        state=dict(
            type="str",
            default="present",
            choices=["present", "absent", "build", "promote"],
        ),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Create the MLM client (it will handle parameter validation and credentials loading)
    try:
        client = MLMClient(module)
    except Exception as e:
        module.fail_json(msg="Failed to initialize MLM client: {}".format(str(e)))

    login_success = False
    try:
        # Login to the API
        try:
            client.login()
            login_success = True
        except Exception as e:
            module.fail_json(msg="Failed to login to MLM API: {}".format(str(e)))

        # Determine what to do based on the state
        try:
            state = module.params["state"]
            if state == "present":
                changed, result, msg = create_or_update_project(module, client)
            elif state == "absent":
                changed, result, msg = delete_project_handler(module, client)
            elif state == "build":
                changed, result, msg = build_project_handler(module, client)
            else:  # state == 'promote'
                changed, result, msg = promote_project_handler(module, client)

            # Return the result
            if result:
                if state == "present":
                    module.exit_json(changed=changed, msg=msg, project=result)
                elif state == "build":
                    module.exit_json(changed=changed, msg=msg, build_result=result)
                elif state == "promote":
                    module.exit_json(changed=changed, msg=msg, promote_result=result)
            else:
                module.exit_json(changed=changed, msg=msg)
        except Exception as e:
            module.fail_json(msg="Failed to manage content project: {}".format(str(e)))
    except Exception as e:
        module.fail_json(msg="Unexpected error: {}".format(str(e)))
    finally:
        # Logout from the API only if login was successful
        if login_success:
            try:
                client.logout()
            except Exception:
                # Ignore logout errors
                pass


if __name__ == "__main__":
    main()
