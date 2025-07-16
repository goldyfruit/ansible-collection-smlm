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
This module provides utility functions for working with user notifications in SUSE Multi-Linux Manager.

It contains common functions used by the user_notifications and user_notifications_info modules to avoid code duplication.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from typing import Dict, List, Optional, Any, Tuple
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
    check_api_response,
    format_error_message,
)
from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_common import (
    standardize_api_response,
    validate_required_params,
    format_module_result,
    check_mode_exit,
    MLMAPIError,
    handle_module_errors,
)


def standardize_notification_data(
    notification_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Standardize the notification data format.

    Args:
        notification_data: The raw notification data from the API.

    Returns:
        dict: The standardized notification data.
    """
    if not notification_data:
        return {}

    # Parse the message field if it contains JSON data
    message = notification_data.get("message", "")
    parsed_message = message

    # Try to parse message as JSON if it's a string that looks like JSON
    if (
        isinstance(message, str)
        and message.strip().startswith("{")
        and message.strip().endswith("}")
    ):
        try:
            parsed_message = json.loads(message)
        except (json.JSONDecodeError, ValueError):
            # If parsing fails, keep the original string
            parsed_message = message
    elif isinstance(message, list):
        # If message is already a list, keep it as is
        parsed_message = message

    return {
        "id": notification_data.get("id"),
        "read": notification_data.get("read", False),
        "message": parsed_message,
        "summary": notification_data.get("summary", ""),
        "details": notification_data.get("details", ""),
        "type": notification_data.get("type", ""),
        "created": notification_data.get("created", ""),
    }


def get_user_notifications(
    client: Any, unread_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Get all notifications for the current user.

    Note: User notifications functionality may not be available in all SUSE Multi-Linux Manager versions.
    This function will return an empty list if the API endpoints are not available.

    Args:
        client: The MLM client.
        unread_only: If True, return only unread notifications.

    Returns:
        list: A list of standardized notification data, or empty list if feature unavailable.

    Raises:
        Exception: Only if there's a critical error in processing available data.
    """
    try:
        # Try different possible API endpoints for user notifications
        # Note: This feature may not be available in all SUSE Multi-Linux Manager versions
        possible_paths = [
            "/user/notifications",
            "/user/listNotifications",
            "/user/getNotifications",
            "/notification/list",
            "/notification/listUserNotifications",
            "/user/notification/list",
            "/api/user/notifications",
        ]

        notifications = None
        successful_path = None
        last_error = None

        for path in possible_paths:
            try:
                response, info = client._request("GET", path)
                # Check for successful response
                if info and info.get("status") == 200 and response:
                    try:
                        import json
                        from ansible.module_utils._text import to_text

                        notifications = json.loads(to_text(response.read()))
                        successful_path = path
                        break
                    except Exception:
                        continue
                else:
                    # Track the last error for debugging
                    if info:
                        last_error = "HTTP {} for {}".format(
                            info.get("status", "Unknown"), path
                        )
            except Exception as e:
                last_error = "Exception for {}: {}".format(path, str(e))
                continue

        # If no endpoints work, user notifications feature is not available
        if notifications is None:
            # Return empty list - this is not a failure condition
            # User notifications may not be available in this SUSE Multi-Linux Manager version
            return []

        if not notifications:
            return []

        if isinstance(notifications, dict) and "result" in notifications:
            notifications = notifications["result"]

        if not isinstance(notifications, list):
            return []

        # Standardize all notifications
        standardized_notifications = [
            standardize_notification_data(notification)
            for notification in notifications
            if isinstance(notification, dict)
        ]

        # Filter for unread notifications if requested
        if unread_only:
            standardized_notifications = [
                notification
                for notification in standardized_notifications
                if not notification.get("read", True)
            ]

        return standardized_notifications
    except Exception as e:
        # Only raise exception for processing errors, not API availability
        if "Failed to parse" in str(e) or "processing" in str(e).lower():
            raise Exception("Failed to process user notifications: {}".format(str(e)))
        # For API endpoint issues, return empty list
        return []


def get_user_notification_count(client: Any, unread_only: bool = False) -> int:
    """
    Get the count of notifications for the current user.

    Note: Returns 0 if user notifications functionality is not available in this SUSE Multi-Linux Manager version.

    Args:
        client: The MLM client.
        unread_only: If True, count only unread notifications.

    Returns:
        int: The number of notifications, or 0 if feature unavailable.

    Raises:
        Exception: Only if there's a critical error in processing available data.
    """
    try:
        notifications = get_user_notifications(client, unread_only=unread_only)
        return len(notifications)
    except Exception as e:
        # If it's a processing error, re-raise it
        if "Failed to process" in str(e):
            raise Exception("Failed to get user notification count: {}".format(str(e)))
        # For API availability issues, return 0
        return 0


@handle_module_errors
def delete_user_notifications(
    module: Any, client: Any
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Delete specific user notifications.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)

    Raises:
        MLMAPIError: If the API request fails.
    """
    # Extract module parameters
    notification_ids = module.params.get("notification_ids", [])

    # Validate required parameters
    if not notification_ids:
        raise MLMAPIError(
            format_error_message(
                "delete notifications", "notification_ids parameter is required"
            ),
            response={"notification_ids": notification_ids},
        )

    # Ensure notification_ids is a list
    if not isinstance(notification_ids, list):
        notification_ids = [notification_ids]

    # Convert to integers if needed
    try:
        notification_ids = [int(nid) for nid in notification_ids]
    except (ValueError, TypeError) as e:
        raise MLMAPIError(
            format_error_message(
                "delete notifications", "Invalid notification IDs: {}".format(str(e))
            ),
            response={"notification_ids": notification_ids},
        )

    # Handle check mode
    check_mode_exit(
        module,
        True,
        "deleted",
        "{} notifications".format(len(notification_ids)),
        "user notifications",
    )

    # Make the API request
    try:
        delete_path = "/user/notifications/deleteNotifications"
        result = client.post(delete_path, data={"notifications": notification_ids})

        # API returns int (1 on success)
        standardized_result = standardize_api_response(
            result, "delete notifications", expected_type="any"
        )

        if standardized_result == 1:
            return format_module_result(
                True,
                None,
                "deleted",
                "{} notifications".format(len(notification_ids)),
                "user notifications",
            )
        else:
            raise MLMAPIError(
                format_error_message(
                    "delete notifications",
                    "API returned unexpected result: {}".format(standardized_result),
                ),
                response={
                    "notification_ids": notification_ids,
                    "api_result": standardized_result,
                },
            )

    except Exception as e:
        raise MLMAPIError(
            format_error_message("delete notifications", str(e)),
            response={"notification_ids": notification_ids},
        )


@handle_module_errors
def set_all_notifications_read(
    module: Any, client: Any
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Mark all user notifications as read.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)

    Raises:
        MLMAPIError: If the API request fails.
    """
    # Handle check mode
    check_mode_exit(
        module, True, "marked as read", "all notifications", "user notifications"
    )

    # Make the API request
    try:
        mark_read_path = "/user/notifications/setAllNotificationsRead"
        result = client.post(mark_read_path, data={})

        # API returns int (1 on success)
        standardized_result = standardize_api_response(
            result, "mark all notifications as read", expected_type="any"
        )

        if standardized_result == 1:
            return format_module_result(
                True, None, "marked as read", "all notifications", "user notifications"
            )
        else:
            raise MLMAPIError(
                format_error_message(
                    "mark all notifications as read",
                    "API returned unexpected result: {}".format(standardized_result),
                ),
                response={"api_result": standardized_result},
            )

    except Exception as e:
        raise MLMAPIError(
            format_error_message("mark all notifications as read", str(e)), response={}
        )


@handle_module_errors
def set_notifications_read(
    module: Any, client: Any
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Mark specific user notifications as read.

    Args:
        module: The AnsibleModule instance.
        client: The MLM client.

    Returns:
        tuple: (changed, result, msg)

    Raises:
        MLMAPIError: If the API request fails.
    """
    # Extract module parameters
    notification_ids = module.params.get("notification_ids", [])

    # Validate required parameters
    if not notification_ids:
        raise MLMAPIError(
            format_error_message(
                "mark notifications as read", "notification_ids parameter is required"
            ),
            response={"notification_ids": notification_ids},
        )

    # Ensure notification_ids is a list
    if not isinstance(notification_ids, list):
        notification_ids = [notification_ids]

    # Convert to integers if needed
    try:
        notification_ids = [int(nid) for nid in notification_ids]
    except (ValueError, TypeError) as e:
        raise MLMAPIError(
            format_error_message(
                "mark notifications as read",
                "Invalid notification IDs: {}".format(str(e)),
            ),
            response={"notification_ids": notification_ids},
        )

    # Handle check mode
    check_mode_exit(
        module,
        True,
        "marked as read",
        "{} notifications".format(len(notification_ids)),
        "user notifications",
    )

    # Make the API request
    try:
        mark_read_path = "/user/notifications/setNotificationsRead"
        result = client.post(mark_read_path, data={"notifications": notification_ids})

        # API returns int (1 on success)
        standardized_result = standardize_api_response(
            result, "mark notifications as read", expected_type="any"
        )

        if standardized_result == 1:
            return format_module_result(
                True,
                None,
                "marked as read",
                "{} notifications".format(len(notification_ids)),
                "user notifications",
            )
        else:
            raise MLMAPIError(
                format_error_message(
                    "mark notifications as read",
                    "API returned unexpected result: {}".format(standardized_result),
                ),
                response={
                    "notification_ids": notification_ids,
                    "api_result": standardized_result,
                },
            )

    except Exception as e:
        raise MLMAPIError(
            format_error_message("mark notifications as read", str(e)),
            response={"notification_ids": notification_ids},
        )
