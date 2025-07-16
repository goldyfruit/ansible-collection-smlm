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

DOCUMENTATION = r"""
---
module: user_notifications_info
short_description: Gather information about user notifications in SUSE Multi-Linux Manager
description:
  - Retrieve information about user notifications in SUSE Multi-Linux Manager.
  - This module uses the SUSE Multi-Linux Manager API to gather notification data.
  - The module operates on the current authenticated user's notifications.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  unread_only:
    description:
      - If set to true, only return unread notifications.
      - If set to false or not specified, return all notifications.
    type: bool
    default: false
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have appropriate permissions to access user notifications.
  - The module returns notifications for the currently authenticated user only.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Get all notifications for the current user
- name: Get all user notifications
  goldyfruit.mlm.user_notifications_info:
  register: all_notifications

- name: Display notification count
  ansible.builtin.debug:
    msg: "Found {{ all_notifications.notifications | length }} total notifications"

# Get only unread notifications
- name: Get unread notifications only
  goldyfruit.mlm.user_notifications_info:
    unread_only: true
  register: unread_notifications

- name: Display unread notification count
  ansible.builtin.debug:
    msg: "Found {{ unread_notifications.notifications | length }} unread notifications"

# Process notifications with specific types
- name: Show system notifications
  ansible.builtin.debug:
    msg: "{{ item.message }} ({{ item.type }})"
  loop: "{{ all_notifications.notifications }}"
  when:
    - all_notifications.notifications is defined
    - "'system' in item.type"
"""

RETURN = r"""
notifications:
  description: List of user notifications.
  returned: always
  type: list
  elements: dict
  contains:
    id:
      description: Notification ID.
      type: int
      sample: 12345
    read:
      description: Whether the notification has been read.
      type: bool
      sample: false
    message:
      description: Notification message content. If the message contains JSON data, it will be parsed automatically.
      type: raw
      sample: {"systemName": "server01", "systemId": 1000010006, "actionId": 27}
    summary:
      description: Notification summary.
      type: str
      sample: "Error running state.apply on: server01"
    details:
      description: Detailed notification information.
      type: str
      sample: "Detailed update information"
    type:
      description: Notification type.
      type: str
      sample: "StateApplyFailed"
    created:
      description: Notification creation timestamp.
      type: str
      sample: "2025-07-08T12:28:31Z"
total_count:
  description: Total number of notifications returned.
  returned: always
  type: int
  sample: 42
unread_count:
  description: Number of unread notifications (only when unread_only is false).
  returned: when unread_only is false
  type: int
  sample: 15
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "Retrieved 42 user notifications"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_user_notifications_utils import (
    get_user_notifications,
    get_user_notification_count,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Creates the MLM client and logs in to the API
    3. Retrieves user notifications based on the specified parameters
    4. Returns the result to Ansible
    5. Ensures proper logout from the API

    The module supports filtering notifications by read status and provides
    comprehensive information about each notification.
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        unread_only=dict(type="bool", default=False),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Create the MLM client
    client = MLMClient(module)

    # Login to the API
    client.login()

    try:
        # Get the unread_only parameter
        unread_only = module.params["unread_only"]

        # Get user notifications
        try:
            notifications = get_user_notifications(client, unread_only=unread_only)
            total_count = len(notifications)

            # Get unread count if we're returning all notifications
            unread_count = None
            if not unread_only:
                try:
                    unread_count = get_user_notification_count(client, unread_only=True)
                except Exception:
                    # If we can't get unread count, continue without it
                    pass

            # Prepare the result
            result = {
                "notifications": notifications,
                "total_count": total_count,
            }

            # Add unread count if available
            if unread_count is not None:
                result["unread_count"] = unread_count

            # Generate status message
            if unread_only:
                msg = "Retrieved {} unread user notifications".format(total_count)
            else:
                if unread_count is not None:
                    msg = "Retrieved {} user notifications ({} unread)".format(total_count, unread_count)
                else:
                    msg = "Retrieved {} user notifications".format(total_count)

            # Return the result
            module.exit_json(changed=False, msg=msg, **result)

        except Exception as e:
            module.fail_json(msg="Failed to retrieve user notifications: {}".format(str(e)))

    except Exception as e:
        module.fail_json(msg="Failed to retrieve user notifications: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == "__main__":
    main()
