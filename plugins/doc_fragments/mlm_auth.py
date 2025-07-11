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


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  url:
    description:
      - URL of the SUSE Multi-Linux Manager server.
      - If not specified, the value of the C(MLM_URL) environment variable will be used.
      - If not specified in environment variables, the value from the credentials file will be used.
    type: str
    required: false
  username:
    description:
      - Username for authenticating with the SUSE Multi-Linux Manager API.
      - If not specified, the value of the C(MLM_USERNAME) environment variable will be used.
      - If not specified in environment variables, the value from the credentials file will be used.
    type: str
    required: false
  password:
    description:
      - Password for authenticating with the SUSE Multi-Linux Manager API.
      - If not specified, the value of the C(MLM_PASSWORD) environment variable will be used.
      - If not specified in environment variables, the value from the credentials file will be used.
    type: str
    required: false
    no_log: true
  instance:
    description:
      - The name of the SMLM instance to use from the credentials file.
      - If not specified, the default instance from the credentials file will be used.
    type: str
    required: false
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
"""
