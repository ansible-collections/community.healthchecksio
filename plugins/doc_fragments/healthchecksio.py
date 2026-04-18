# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  management_api_token:
    aliases:
      - management_api_key
      - api_key
    description:
      - Healthchecks.io management API token.
      - "There are several environment variables which can be used to provide this value:"
      - C(HEALTHCHECKSIO_API_TOKEN), C(HEALTHCHECKSIO_API_KEY), C(HC_API_TOKEN), C(HC_API_KEY)
      - C(HEALTHCHECKSIO_MANAGEMENT_API_KEY), C(HC_MANAGEMENT_API_KEY), C(HC_MANAGEMENT_KEY)
    type: str
    required: false
  management_api_base_url:
    description:
      - Base URL of the Healthchecks.io management API.
      - "There are several environment variables which can be used to provide this value:"
      - C(HEALTHCHECKSIO_API_MANAGEMENT_BASE_URL), C(HC_API_MANAGEMENT_BASE_URL)
      - Defaults to C(https://healthchecks.io/api/v1).
    type: str
    required: false
    default: https://healthchecks.io/api/v1
  ping_api_base_url:
    description:
      - Base URL of the Healthchecks.io ping API.
      - "There are several environment variables which can be used to provide this value:"
      - C(HEALTHCHECKSIO_API_PING_BASE_URL), C(HC_API_PING_BASE_URL)
      - Defaults to C(https://hc-ping.com).
    type: str
    required: false
    default: https://hc-ping.com
  ping_api_token:
    description:
      - Healthchecks.io ping API token (optional, can be used instead of management_api_token).
      - "There are several environment variables which can be used to provide this value:"
      - C(HEALTHCHECKSIO_API_PING_KEY), C(HC_API_PING_KEY)
    type: str
    required: false
"""
