#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: checks_ping_body_info
short_description: Get a logged ping body
description:
  - Returns the stored request body for one logged ping as plain text.
  - The API returns HTTP 404 when the check, ping, or body does not exist.
author: "Mark Mercado (@mamercad)"
version_added: 2.0.0
options:
  uuid:
    description:
      - UUID of the check that received the ping.
    type: str
    required: true
  sequence:
    description:
      - Ping sequence number from the C(n) field returned by M(community.healthchecksio.checks_pings_info).
    type: int
    required: true
extends_documentation_fragment:
  - community.healthchecksio.healthchecksio.documentation
"""

EXAMPLES = r"""
- name: Read a logged ping body
  community.healthchecksio.checks_ping_body_info:
    uuid: "{{ check_uuid }}"
    sequence: 42
  register: ping_body
"""

RETURN = r"""
data:
  description: Logged ping request body.
  returned: success
  type: str
  sample: Backup completed successfully
"""

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    ChecksPingBodyInfo,
    HealthchecksioHelper,
)
from ansible.module_utils.basic import AnsibleModule


def run(module):
    ChecksPingBodyInfo(module).get()


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.pop("state", None)
    argument_spec.update(
        uuid=dict(type="str", required=True),
        sequence=dict(type="int", required=True),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    run(module)


if __name__ == "__main__":  # pragma: no cover
    main()
