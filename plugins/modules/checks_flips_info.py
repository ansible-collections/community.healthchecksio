#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: checks_flips_info
short_description: Get a list of check flips
description:
  - Get a list of check's status changes.
  - Returns a list of "flips" this check has experienced.
  - A flip is a change of status (from "down" to "up," or from "up" to "down").
author: "Mark Mercado (@mamercad)"
version_added: 0.1.0
options:
  state:
    description:
      - C(present) will return the check pings.
    type: str
    choices: ["present"]
    default: present
  uuid:
    description:
      - Check UUID whose status changes to return.
    type: str
    required: false
  unique_key:
    description:
      - Stable check identifier from a read-only API response.
    type: str
    required: false
    version_added: 2.0.0
  seconds:
    description:
      - Return flips from the last specified number of seconds.
    type: int
    version_added: 2.0.0
  start:
    description:
      - Return flips newer than this UNIX timestamp.
    type: int
    version_added: 2.0.0
  end:
    description:
      - Return flips older than this UNIX timestamp.
    type: int
    version_added: 2.0.0
extends_documentation_fragment:
  - community.healthchecksio.healthchecksio.documentation
"""

EXAMPLES = r"""
- name: Get a list of checks flips
  community.healthchecksio.checks_flips_info:
    state: present
    uuid: cae50618-c97f-483e-9814-0277dc523d1
    seconds: 3600
"""

RETURN = r"""
data:
  description: Check flips response
  returned: always
  type: dict
  sample:
    flips:
      - timestamp: '2020-03-23T10:18:23+00:00'
        up: 1
"""


from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    ChecksFlipsInfo,
)
from ansible.module_utils.basic import AnsibleModule


def run(module):
    state = module.params.pop("state")
    flips = ChecksFlipsInfo(module)
    if state == "present":
        flips.get()


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.update(
        state=dict(type="str", choices=["present"], default="present"),
        uuid=dict(type="str", required=False),
        unique_key=dict(type="str", required=False, no_log=False),
        seconds=dict(type="int"),
        start=dict(type="int"),
        end=dict(type="int"),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[("uuid", "unique_key")],
        mutually_exclusive=[
            ("uuid", "unique_key"),
            ("seconds", "start"),
            ("seconds", "end"),
        ],
    )

    run(module)


if __name__ == "__main__":
    main()
