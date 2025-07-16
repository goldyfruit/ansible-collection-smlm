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
module: user_notifications
short_description: Manage user notifications in SUSE Multi-Linux Manager
description:
  - Manage user notifications in SUSE Multi-Linux Manager.
  - This module allows you to delete notifications or mark them as read.
  - All operations are performed on the current authenticated user's notifications.
author: Gaëtan Trellu (@goldyfruit) <gaetan.trellu@suse.com>
version_added: '1.0.0'
extends_documentation_fragment:
  - goldyfruit.mlm.mlm_auth
options:
  operation:
    description:
      - The operation to perform on the notifications.
      - C(delete) - Delete specific notifications by ID.
      - C(mark_read) - Mark specific notifications as read by ID.
      - C(mark_all_read) - Mark all notifications as read.
    type: str
    choices: [delete, mark_read, mark_all_read]
    required: true
  notification_ids:
    description:
      - List of notification IDs to operate on.
      - Required for C(delete) and C(mark_read) operations.
      - Ignored for C(mark_all_read) operation.
    type: list
    elements: int
notes:
  - This module requires the SUSE Multi-Linux Manager API to be accessible from the Ansible controller.
  - The user running this module must have appropriate permissions to manage user notifications.
  - The module operates on the currently authenticated user's notifications only.
  - Once notifications are deleted, they cannot be recovered.
requirements:
  - python >= 3.6
"""

EXAMPLES = r"""
# Delete specific notifications by ID
- name: Delete specific notifications
  goldyfruit.mlm.user_notifications:
    operation: delete
    notification_ids:
      - 12345
      - 12346
      - 12347

# Mark specific notifications as read
- name: Mark specific notifications as read
  goldyfruit.mlm.user_notifications:
    operation: mark_read
    notification_ids:
      - 12345
      - 12346

# Mark all notifications as read
- name: Mark all notifications as read
  goldyfruit.mlm.user_notifications:
    operation: mark_all_read

# Delete notifications using results from info module
- name: Get unread notifications
  goldyfruit.mlm.user_notifications_info:
    unread_only: true
  register: unread_notifications

- name: Delete all unread notifications
  goldyfruit.mlm.user_notifications:
    operation: delete
    notification_ids: "{{ unread_notifications.notifications | map(attribute='id') | list }}"
  when:
    - unread_notifications.notifications is defined
    - unread_notifications.notifications | length > 0
"""

RETURN = r"""
changed:
  description: Whether any changes were made.
  returned: always
  type: bool
  sample: true
msg:
  description: Status message describing the result of the operation.
  returned: always
  type: str
  sample: "Deleted 3 user notifications successfully"
operation:
  description: The operation that was performed.
  returned: always
  type: str
  sample: "delete"
notification_count:
  description: Number of notifications that were affected by the operation.
  returned: when operation affects specific notifications
  type: int
  sample: 3
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    MLMClient,
    mlm_argument_spec,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_user_notifications_utils import (
    delete_user_notifications,
    set_all_notifications_read,
    set_notifications_read,
)


def main():
    """
    Main module execution.

    This function is the entry point for the Ansible module. It:
    1. Defines the module arguments and creates the AnsibleModule instance
    2. Creates the MLM client and logs in to the API
    3. Performs the requested notification management operation
    4. Returns the result to Ansible
    5. Ensures proper logout from the API

    The module supports three main operations:
    - delete: Remove specific notifications
    - mark_read: Mark specific notifications as read
    - mark_all_read: Mark all notifications as read
    """
    # Define the module arguments
    argument_spec = mlm_argument_spec()
    argument_spec.update(
        operation=dict(
            type="str",
            choices=["delete", "mark_read", "mark_all_read"],
            required=True,
        ),
        notification_ids=dict(type="list", elements="int"),
    )

    # Create the module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("operation", "delete", ["notification_ids"]),
            ("operation", "mark_read", ["notification_ids"]),
        ],
    )

    # Create the MLM client
    client = MLMClient(module)

    # Login to the API
    client.login()

    try:
        # Get the operation parameter
        operation = module.params["operation"]

        # Execute the appropriate operation
        if operation == "delete":
            changed, result, msg = delete_user_notifications(module, client)
            notification_count = len(module.params.get("notification_ids", []))

            module.exit_json(
                changed=changed,
                msg=msg,
                operation=operation,
                notification_count=notification_count,
                **(result or {})
            )

        elif operation == "mark_read":
            changed, result, msg = set_notifications_read(module, client)
            notification_count = len(module.params.get("notification_ids", []))

            module.exit_json(
                changed=changed,
                msg=msg,
                operation=operation,
                notification_count=notification_count,
                **(result or {})
            )

        elif operation == "mark_all_read":
            changed, result, msg = set_all_notifications_read(module, client)

            module.exit_json(
                changed=changed,
                msg=msg,
                operation=operation,
                **(result or {})
            )

        else:
            module.fail_json(msg="Invalid operation: {}".format(operation))

    except Exception as e:
        module.fail_json(msg="Failed to manage user notifications: {}".format(str(e)))
    finally:
        # Logout from the API
        client.logout()


if __name__ == "__main__":
    main()
