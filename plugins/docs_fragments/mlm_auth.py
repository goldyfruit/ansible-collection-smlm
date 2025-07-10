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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):
    # Standard MLM authentication documentation fragment
    DOCUMENTATION = r'''
options:
  url:
    description:
      - URL of the SUSE Multi-Linux Manager server.
      - If not specified, the value of the C(MLM_URL) environment variable will be used.
      - If not specified in environment variables, the value from the credentials file at C(~/.config/smlm/credentials.yaml) will be used if available.
    type: str
    required: false
  username:
    description:
      - Username for authenticating with the SUSE Multi-Linux Manager API.
      - If not specified, the value of the C(MLM_USERNAME) environment variable will be used.
      - If not specified in environment variables, the value from the credentials file at C(~/.config/smlm/credentials.yaml) will be used if available.
    type: str
    required: false
  password:
    description:
      - Password for authenticating with the SUSE Multi-Linux Manager API.
      - If not specified, the value of the C(MLM_PASSWORD) environment variable will be used.
      - If not specified in environment variables, the value from the credentials file at C(~/.config/smlm/credentials.yaml) will be used if available.
    type: str
    required: false
  instance:
    description:
      - The name of the SMLM instance to use from the credentials file at C(~/.config/smlm/credentials.yaml).
      - If not specified, the default instance from the credentials file will be used.
    type: str
    required: false
notes:
  - Credentials can be stored in a YAML file at C(~/.config/smlm/credentials.yaml) with multiple instance configurations.
  - The credentials file should have a structure like:
    code: |
      default: production
      instances:
        production:
          url: "https://smlm-prod.example.com"
          username: "admin"
          password: "secret"
          validate_certs: true
        testing:
          url: "https://smlm-test.example.com"
          username: "testuser"
          password: "testpass"
          validate_certs: false
  - Parameter priority is: module parameters > environment variables > credentials file.
  validate_certs:
    description:
      - Whether to validate SSL certificates when connecting to the SUSE Multi-Linux Manager API.
      - This should only be set to C(false) for testing with self-signed certificates.
    type: bool
    default: true
  timeout:
    description:
      - Timeout in seconds for API requests.
    type: int
    default: 60
  retries:
    description:
      - Number of times to retry failed API requests.
    type: int
    default: 3
  cache:
    description:
      - Whether to cache the results of the inventory.
      - Set to C(false) if you always want fresh data.
    type: bool
    default: true
  cache_timeout:
    description:
      - Time in seconds to cache the inventory results.
    type: int
    default: 3600
  filters:
    description:
      - Dictionary of filters to apply when retrieving systems from MLM.
      - Available filters include C(status), C(patch_status), and C(system_groups).
      - The C(patch_status) filter can be set to C(needs_patches), C(needs_reboot), or C(up_to_date).
    type: dict
    required: false
  group_by:
    description:
      - List of properties to group systems by.
      - Creates Ansible groups automatically based on system attributes.
      - Common values include C(patch_status) and C(system_groups).
    type: list
    elements: str
    required: false
  compose:
    description:
      - Dictionary of custom host variables to create using Jinja2 expressions.
      - These variables will be available for each host in the inventory.
      - Common variables include C(ansible_host), C(registration_date), and C(needs_reboot).
    type: dict
    required: false
  api_base_path:
    description:
      - Base path for the MLM API.
      - If not specified, the default value from the MLM client will be used.
      - If not specified, the value of the C(MLM_API_BASE_PATH) environment variable will be used.
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
'''
