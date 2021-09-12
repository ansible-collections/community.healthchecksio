# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  api_token:
    aliases: ["api_key"]
    description:
      - Healthchecks.io API token.
      - "There are several environment variables which can be used to provide this value:"
      - C(HEALTHCHECKSIO_API_TOKEN), C(HEALTHCHECKSIO_API_KEY), C(HC_API_TOKEN), C(HC_API_KEY)
    type: str
    required: true
"""
