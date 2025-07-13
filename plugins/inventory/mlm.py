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
Ansible inventory plugin for SUSE Multi-Linux Manager.

This plugin retrieves system information from a SUSE Multi-Linux Manager server
and creates an Ansible inventory from it. It supports filtering systems based on
their status, patch status, and system group membership.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
name: mlm
short_description: SUSE Multi-Linux Manager inventory source
description:
    - Get inventory hosts from SUSE Multi-Linux Manager (MLM).
    - Uses a YAML configuration file that ends with C(mlm.yml) or C(mlm.yaml).
    - Supports filtering systems by status, patch status, and system group membership.
    - Automatically adds systems to groups based on their properties.
    - Allows creating custom host variables using Jinja2 expressions.
author:
    - Gaëtan Trellu (@goldyfruit)
options:
    plugin:
        description: Token that ensures this is a source file for the 'mlm' plugin.
        required: true
        choices: ['goldyfruit.mlm.mlm', 'mlm']
    url:
        description:
            - URL of the SUSE Multi-Linux Manager server.
            - If not specified, the value of the C(MLM_URL) environment variable will be used.
        type: str
        required: false
    username:
        description:
            - Username for authenticating with the SUSE Multi-Linux Manager API.
            - If not specified, the value of the C(MLM_USERNAME) environment variable will be used.
        type: str
        required: false
    password:
        description:
            - Password for authenticating with the SUSE Multi-Linux Manager API.
            - If not specified, the value of the C(MLM_PASSWORD) environment variable will be used.
        type: str
        required: false
    validate_certs:
        description:
            - Whether to validate SSL certificates when connecting to the SUSE Multi-Linux Manager API.
            - This should only be set to C(false) for testing with self-signed certificates.
        type: bool
        default: true
    timeout:
        description: Timeout in seconds for API requests.
        type: int
        default: 60
    retries:
        description: Number of times to retry failed API requests.
        type: int
        default: 3
    cache:
        description: Toggle to enable/disable the caching of the inventory's source data.
        type: bool
        default: true
    cache_plugin:
        description: Cache plugin to use for the inventory's source data.
        type: str
        default: jsonfile
    cache_timeout:
        description: Cache duration in seconds.
        type: int
        default: 3600
    cache_connection:
        description: Path to the cache connection file.
        type: str
        default: "{{ ansible_env.HOME }}/.ansible/tmp/ansible_mlm_inventory"
    cache_prefix:
        description: Prefix to use for the cache file.
        type: str
        default: mlm
    filters:
        description:
            - A dictionary of filter values that will be used to filter the systems returned by the API.
            - Filters are applied as AND conditions (all must match).
        type: dict
        default: {}
        suboptions:
            status:
                description: Filter systems by their status.
                type: str
                choices: ['active', 'inactive', 'all']
                default: 'active'
            patch_status:
                description: Filter systems by their patch status.
                type: str
                choices: ['up_to_date', 'needs_patches', 'needs_reboot', 'all']
                default: 'all'
            system_groups:
                description: Filter systems by their group membership.
                type: list
                elements: str
    group_by:
        description:
            - A list of properties to create inventory groups from.
            - Each system will be added to groups based on these properties.
            - Available options are 'patch_status' and 'system_groups'.
            - Systems are always added to their respective system groups regardless of this setting.
        type: list
        elements: str
        default: ['patch_status']
    compose:
        description:
            - Create custom host variables using Jinja2 expressions.
            - The expressions are evaluated for each host and added as host variables.
        type: dict
        default: {}
    api_base_path:
        description:
            - Base path for the MLM API.
            - If not specified, the default value from the MLM client will be used.
        type: str
        required: false
    api_endpoints:
        description:
            - Dictionary of API endpoints to use for the MLM API.
            - If not specified, the default values from the MLM client will be used.
        type: dict
        required: false
    field_mappings:
        description:
            - Dictionary of field mappings to use for the MLM API responses.
            - If not specified, the default values from the MLM client will be used.
        type: dict
        required: false
"""

EXAMPLES = r"""
# Minimal example using environment variables for authentication (recommended)
plugin: goldyfruit.mlm.mlm

# Example using credentials configuration file (recommended)
plugin: goldyfruit.mlm.mlm
instance: production  # Use specific instance from ~/.config/smlm/credentials.yaml

# Example with filters using credentials file
plugin: goldyfruit.mlm.mlm
filters:
  status: active
  patch_status: needs_patches
  system_groups:
    - production
    - web_servers

# Example with custom grouping and variables using credentials file
plugin: goldyfruit.mlm.mlm
group_by:
  - patch_status
  - system_groups
compose:
  ansible_host: network_info.ip
  registration_date: "registration_date | string"
  needs_reboot: "patch_status == 'needs_reboot'"

# Example showing how to use system groups in playbooks
# Systems are automatically added to their respective groups
# For example, if a system belongs to 'web_servers' group:
#
# - name: Update web servers
#   hosts: web_servers
#   tasks:
#     - name: Update packages
#       ansible.builtin.package:
#         name: "*"
#         state: latest
"""

import re
import os
from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable, Constructable

try:
    from ansible_collections.goldyfruit.mlm.plugins.module_utils.mlm_client import (
        MLMClient,
    )

    HAS_MLM_CLIENT = True
except ImportError:
    HAS_MLM_CLIENT = False


class InventoryModule(BaseInventoryPlugin, Cacheable, Constructable):
    """
    SUSE Multi-Linux Manager inventory plugin.

    This plugin retrieves system information from a SUSE Multi-Linux Manager server
    and creates an Ansible inventory from it.
    """

    NAME = "mlm"  # used internally by Ansible, must match the filename

    def __init__(self):
        """Initialize the inventory plugin."""
        super(InventoryModule, self).__init__()
        from ansible.utils.display import Display

        self._display = Display()

    def verify_file(self, path):
        """
        Verify that the source file is valid.

        Args:
            path (str): Path to the inventory file.

        Returns:
            bool: True if the file is valid, False otherwise.
        """
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(("mlm.yml", "mlm.yaml")):
                return True
        return False

    def parse(self, inventory, loader, path, cache=True):
        """
        Parse the inventory file and generate inventory from MLM systems.

        This method is called by Ansible to parse the inventory file and generate
        the inventory. It loads the configuration from the inventory file, connects
        to the MLM API, retrieves the systems, and adds them to the inventory.

        Args:
            inventory (obj): The Ansible inventory object to populate.
            loader (obj): The Ansible file loader object.
            path (str): Path to the inventory file.
            cache (bool): Whether to use cache for inventory data.
        """
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        # Load configuration from the inventory file
        self._read_config_data(path)

        # Check if MLM client is available
        if not HAS_MLM_CLIENT:
            raise AnsibleParserError(
                "The SUSE MLM inventory plugin requires the MLM client module utils. "
                "Make sure the collection is properly installed."
            )

        # Set cache options
        self.cache_key = self.get_option("cache_prefix")
        cache_timeout = self.get_option("cache_timeout")

        # Get systems from cache or API with optimized caching logic
        systems = self._get_cached_or_live_systems(cache)

        # Add systems to inventory
        self._populate_inventory(systems)

    def _get_systems_from_api(self):
        """
        Retrieve systems from the MLM API.

        This method initializes the MLMClient with the necessary parameters,
        authenticates with the MLM API, retrieves all systems, applies any
        configured filters, and returns the filtered list of systems.

        Returns:
            list: A list of dictionaries, each containing system information such as
                 id, name, hostname, IP address, OS details, and status.

        Raises:
            AnsibleParserError: If there is an error connecting to the API or
                                retrieving the systems.
        """
        # Create a module-like object for MLMClient
        module_params = {
            "url": self.get_option("url"),
            "username": self.get_option("username"),
            "password": self.get_option("password"),
            "validate_certs": self.get_option("validate_certs"),
            "timeout": self.get_option("timeout"),
            "retries": self.get_option("retries"),
        }

        # Add API configuration if provided
        if self.get_option("api_base_path"):
            module_params["api_base_path"] = self.get_option("api_base_path")
        if self.get_option("api_endpoints"):
            module_params["api_endpoints"] = self.get_option("api_endpoints")
        if self.get_option("field_mappings"):
            module_params["field_mappings"] = self.get_option("field_mappings")

        # Create an instance of the AnsibleModuleAdapter
        module = self._create_ansible_module_adapter(module_params)

        try:
            # Initialize MLM client
            client = MLMClient(module)

            # Authenticate
            client.login()

            # Get systems with patch status using the REST API method
            systems = client.get_systems_with_patch_status()

            # Apply filters
            systems = self._filter_systems(systems)

            # Logout
            client.logout()

            return systems

        except Exception as e:
            # Raise an error with detailed information if we can't connect to the API
            raise AnsibleParserError(
                "Error fetching systems from MLM API: {}. Please check URL ({}), credentials, and network connectivity.".format(
                    str(e), self.get_option("url")
                )
            )

    def _filter_systems(self, systems):
        """
        Filter systems based on the filters specified in the inventory configuration.

        This method applies all filters defined in the inventory configuration to the
        list of systems retrieved from the API. Filters are applied as AND conditions,
        meaning a system must match all specified filters to be included in the result.

        Args:
            systems (list): List of system dictionaries to filter.

        Returns:
            list: A filtered list of systems that match all specified filter criteria.
        """
        filters = self.get_option("filters")
        if not filters:
            return systems

        # Filter systems using list comprehension for efficiency
        filtered_systems = [
            system
            for system in systems
            if self._system_matches_filters(system, filters)
        ]

        return filtered_systems

    def _system_matches_filters(self, system, filters):
        """
        Check if a system matches all the specified filters.

        This method evaluates each filter against the system properties and returns
        True only if the system matches all filter criteria.

        Args:
            system (dict): The system dictionary to check against filters.
            filters (dict): Dictionary of filter criteria to apply.

        Returns:
            bool: True if the system matches all filters, False otherwise.
        """
        # Define filter handlers for different filter types
        filter_handlers = {
            "status": self._filter_by_status,
            "patch_status": self._filter_by_patch_status,
            "system_groups": self._filter_by_system_groups,
        }

        # Apply each filter
        for filter_key, filter_value in filters.items():
            # Skip 'all' values for filters that support it
            if filter_key in ["status", "patch_status"]:
                if filter_value == "all":
                    continue
            # Handle 'all' value for system_groups filter
            elif filter_key == "system_groups" and (
                filter_value == "all" or filter_value == ["all"]
            ):
                continue

            # Use the appropriate filter handler if available
            if filter_key in filter_handlers:
                if not filter_handlers[filter_key](system, filter_value):
                    return False

        return True

    def _filter_by_status(self, system, filter_value):
        """
        Filter a system by its active status.

        Args:
            system (dict): The system to filter.
            filter_value (str): The status value to filter by ('active', 'inactive', or 'all').

        Returns:
            bool: True if the system matches the filter, False otherwise.
        """
        status_filters = {
            "active": lambda s: s.get("active", True),
            "inactive": lambda s: not s.get("active", True),
            "all": lambda s: True,
        }
        return status_filters.get(filter_value, lambda s: True)(system)

    def _filter_by_patch_status(self, system, filter_value):
        """
        Filter a system by its patch status.

        Args:
            system (dict): The system to filter.
            filter_value (str): The patch status value to filter by ('up_to_date', 'needs_patches', 'needs_reboot', or 'all').

        Returns:
            bool: True if the system matches the filter, False otherwise.
        """
        patch_status_filters = {
            "up_to_date": lambda s: s.get("patch_status") == "up_to_date",
            "needs_patches": lambda s: s.get("patch_status") == "needs_patches",
            "needs_reboot": lambda s: s.get("patch_status") == "needs_reboot",
            "all": lambda s: True,
        }
        return patch_status_filters.get(filter_value, lambda s: True)(system)

    def _filter_by_system_groups(self, system, filter_value):
        """
        Filter a system by its group membership.

        Args:
            system (dict): The system to filter.
            filter_value (list): List of group names to filter by.

        Returns:
            bool: True if the system belongs to any of the specified groups, False otherwise.
        """
        # Get system groups, ensuring it's a list
        system_groups = system.get("groups", [])
        if not isinstance(system_groups, list):
            system_groups = [system_groups]

        # Handle empty system groups
        if not system_groups:
            return False

        # Handle empty filter value
        if not filter_value:
            return True

        # Convert all group names to lowercase for case-insensitive comparison
        system_groups_lower = [str(g).lower() for g in system_groups]
        filter_value_lower = [str(g).lower() for g in filter_value]

        # Check if any of the system's groups match any of the filter groups
        return any(sg in filter_value_lower for sg in system_groups_lower)

    def _populate_inventory(self, systems):
        """
        Add systems to the inventory and create groups based on system properties.

        This method processes each system retrieved from the API, adds it to the
        inventory with the system's hostname as the inventory hostname, sets host
        variables based on system properties, and adds the host to appropriate groups
        based on the group_by configuration.

        Args:
            systems (list): List of system dictionaries to add to the inventory.
        """
        # Add all systems to the 'mlm_systems' group
        self.inventory.add_group("mlm_systems")

        # Get grouping options
        group_by = self.get_option("group_by")

        # Process each system
        for system in systems:
            # Skip systems without hostname or ID
            system_hostname = system.get("hostname") or system.get("name")
            system_id = system.get("id")
            if not system_hostname or not system_id:
                continue

            # Use the system hostname as the inventory hostname
            inventory_hostname = system_hostname

            # Ensure patch_status is set
            if "patch_status" not in system:
                system["patch_status"] = "up_to_date"

            # Add the host to the inventory
            self.inventory.add_host(inventory_hostname, group="mlm_systems")

            # Add system properties as host variables
            self._set_host_variables(inventory_hostname, system)

            # Add the system to groups based on its properties
            self._add_host_to_groups(inventory_hostname, system, group_by)

            # Add composed variables
            self._set_composite_vars(
                self.get_option("compose"),
                self.inventory.get_host(inventory_hostname).get_vars(),
                inventory_hostname,
                strict=False,
            )

    def _set_host_variables(self, inventory_hostname, system):
        """
        Set host variables from system properties.

        Args:
            inventory_hostname (str): The inventory hostname of the system.
            system (dict): The system data dictionary containing properties.
        """
        # Set basic system properties
        self._set_basic_system_properties(inventory_hostname, system)

        # Set registration date
        self._set_registration_date(inventory_hostname, system)

        # Set connection variables (ansible_host)
        self._set_connection_variables(inventory_hostname, system)

        # Set OS information
        self._set_os_information(inventory_hostname, system)

    def _set_basic_system_properties(self, inventory_hostname, system):
        """
        Set basic system properties as host variables.

        Args:
            inventory_hostname (str): The inventory hostname of the system.
            system (dict): The system data dictionary containing properties.
        """
        for key, value in system.items():
            # Handle special cases
            if key == "name":
                # Avoid using reserved variable names
                self.inventory.set_variable(inventory_hostname, "system_name", value)
            elif key == "errata_counts":
                # Skip legacy field
                pass
            else:
                self.inventory.set_variable(inventory_hostname, key, value)

    def _set_registration_date(self, inventory_hostname, system):
        """
        Set the registration date variable, trying multiple possible field names.

        Args:
            inventory_hostname (str): The inventory hostname of the system.
            system (dict): The system data dictionary containing properties.
        """
        for field in ["registration_date", "created", "registered", "registrationDate"]:
            if field in system:
                self.inventory.set_variable(
                    inventory_hostname, "registration_date", str(system[field])
                )
                break

    def _set_connection_variables(self, inventory_hostname, system):
        """
        Set connection variables like ansible_host based on available system properties.

        Args:
            inventory_hostname (str): The inventory hostname of the system.
            system (dict): The system data dictionary containing properties.
        """
        # Determine the best value for ansible_host (connection address)
        # Priority: ip > ipAddress > hostname > name
        ansible_host = None
        if "ip" in system and system["ip"]:
            ansible_host = system["ip"]
        elif "ipAddress" in system and system["ipAddress"]:
            ansible_host = system["ipAddress"]
            # Also set ip for consistency
            self.inventory.set_variable(inventory_hostname, "ip", system["ipAddress"])
        elif "hostname" in system and system["hostname"]:
            ansible_host = system["hostname"]
        elif "name" in system:
            ansible_host = system["name"]

        # Set ansible_host if we found a suitable value
        if ansible_host:
            self.inventory.set_variable(
                inventory_hostname, "ansible_host", ansible_host
            )

    def _set_os_information(self, inventory_hostname, system):
        """
        Set OS information variables based on available system properties.

        Args:
            inventory_hostname (str): The inventory hostname of the system.
            system (dict): The system data dictionary containing properties.
        """
        if "os" in system:
            os_info = system["os"]
            if isinstance(os_info, dict):
                # Map OS info fields to inventory variables, but only if not already set
                os_field_mapping = {
                    "name": "os_name",
                    "version": "os_version",
                    "family": "os_family",
                }

                for os_key, var_name in os_field_mapping.items():
                    if os_key in os_info and var_name not in system:
                        self.inventory.set_variable(
                            inventory_hostname, var_name, os_info[os_key]
                        )
            elif isinstance(os_info, str) and "os_name" not in system:
                # If os is a string and os_name isn't set, use it as os_name
                self.inventory.set_variable(inventory_hostname, "os_name", os_info)

    def _add_host_to_groups(self, inventory_hostname, system, group_by):
        """
        Add a host to groups based on its properties.

        This method creates Ansible inventory groups based on system properties
        specified in the group_by configuration, and adds the host to those groups.
        Groups are created for patch status and system groups.

        Args:
            inventory_hostname (str): The inventory hostname of the system.
            system (dict): The system data dictionary containing properties.
            group_by (list): List of property names to create groups from.
        """

        # Add to patch status group
        if "patch_status" in group_by:
            # Use the patch_status field that was already set in get_systems_with_patch_status
            patch_status = system.get("patch_status", "up_to_date")
            self._add_host_to_group(
                inventory_hostname, "patch_status_{}".format(patch_status)
            )

        # Add to system groups - always add systems to their respective groups
        # regardless of group_by configuration to ensure groups are exposed
        if system.get("groups"):
            # Create a group for each system group
            for group in system["groups"]:
                # Create a direct group with the original group name
                direct_group_name = self._sanitize_group_name(group)
                self._add_host_to_group(inventory_hostname, direct_group_name)

    def _add_host_to_group(self, inventory_hostname, group_name):
        """
        Add a host to a group, creating the group if it doesn't exist.

        This is a helper method that ensures the group exists before adding
        the host to it, creating the group if necessary.

        Args:
            inventory_hostname (str): The inventory hostname of the system.
            group_name (str): The name of the group to add the host to.
        """
        if group_name not in self.inventory.groups:
            self.inventory.add_group(group_name)
        self.inventory.add_host(inventory_hostname, group=group_name)

    def _sanitize_group_name(self, name):
        """
        Sanitize a group name to ensure it's valid for Ansible.

        This method converts a group name to a format that is valid for Ansible
        inventory groups by converting to lowercase, replacing special characters
        with underscores, and ensuring the name starts with a letter or underscore.

        Args:
            name (str): The original group name to sanitize.

        Returns:
            str: A sanitized name safe for use as an Ansible group name.
        """
        if not name:
            return "unknown"

        # Convert to string if not already
        name = str(name)

        # Convert to lowercase
        name = name.lower()

        # Replace spaces and special characters with underscores
        name = re.sub(r"[^a-z0-9_]", "_", name)

        # Ensure the name starts with a letter or underscore
        if name and not (name[0].isalpha() or name[0] == "_"):
            name = "group_" + name

        return name

    def _create_ansible_module_adapter(self, params):
        """
        Create an adapter that mimics the AnsibleModule interface.

        This method creates an object that provides the minimal interface
        required by the MLMClient class, allowing it to be used with the
        inventory plugin without requiring a full AnsibleModule instance.

        Args:
            params (dict): Parameters to initialize the adapter with.

        Returns:
            object: An object that mimics the AnsibleModule interface.
        """

        class AnsibleModuleAdapter:
            def __init__(self, params):
                self.params = params
                self.tmpdir = os.environ.get(
                    "ANSIBLE_REMOTE_TMP",
                    os.path.join(os.environ.get("HOME", "/tmp"), ".ansible/tmp"),
                )

            def fail_json(self, **kwargs):
                msg = kwargs.get("msg", "Unknown error")
                raise AnsibleParserError(msg)

            def get_bin_path(self, *args, **kwargs):
                return None

            def boolean(self, x):
                return bool(x)

            def log(self, msg, level=None):
                # Dummy log method to satisfy MLMClient requirements
                pass

        # Create and return an instance of the adapter
        return AnsibleModuleAdapter(params)

    def _get_cached_or_live_systems(self, use_cache=True):
        """
        Get systems from cache if available and valid, otherwise from the API.

        This method implements an optimized caching strategy that checks if
        cached data exists and is valid before deciding whether to use it or
        fetch fresh data from the API. The cache key includes the filter settings
        to ensure that different filter configurations use different cache entries.

        Args:
            use_cache (bool): Whether to use cache at all. If False, always
                             fetch fresh data from the API.

        Returns:
            list: A list of system dictionaries.
        """
        # If caching is disabled, always get fresh data
        if not use_cache or not self.get_option("cache"):
            return self._get_systems_from_api()

        # Create a more specific cache key based on filters
        filters = self.get_option("filters") or {}
        filter_str = "_".join(
            "{}_{}".format(k, v) for k, v in sorted(filters.items()) if v != "all"
        )
        cache_key = (
            "{}_{}".format(self.cache_key, filter_str) if filter_str else self.cache_key
        )

        # Try to get data from cache
        try:
            # Check if we have valid cached data
            cached_systems = self._cache.get(cache_key)

            # If we have valid cached data, use it
            if cached_systems:
                return cached_systems

        except KeyError:
            # Cache miss, continue to API call
            pass
        except Exception:
            # Log any other cache errors but continue to API call
            pass

        # If we get here, we need to fetch data from the API
        systems = self._get_systems_from_api()

        # Save to cache for future use
        try:
            self._cache[cache_key] = systems
        except Exception:
            pass

        return systems
