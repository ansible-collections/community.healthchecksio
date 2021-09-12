#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: checks_info
short_description: Get a list of checks
description:
  - Returns a list of checks belonging to the user, optionally filtered by one or more tags.
author: "Mark Mercado (@mamercad)"
version_added: 0.1.0
options:
  state:
    description:
      - C(present) will return the check(s).
    type: str
    choices: ["present"]
    default: present
  tags:
    description:
      - Filters the checks and returns only the checks that are tagged with the specified value.
    type: list
    elements: str
    required: false
  uuid:
    description:
      - If specified, returns this specific check.
    type: str
    required: false
extends_documentation_fragment:
  - community.healthchecksio.healthchecksio.documentation
"""

EXAMPLES = r"""
"""

RETURN = r"""
"""


from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    ChecksInfo,
)
from ansible.module_utils.basic import AnsibleModule, env_fallback


def run(module):
    state = module.params.pop("state")
    checks = ChecksInfo(module)
    if state == "present":
        checks.get()


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.update(
        state=dict(type="str", choices=["present"], default="present"),
        tags=dict(type="list", elements="str", required=False),
        uuid=dict(type="str", required=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[("tags", "uuid")],
    )

    run(module)


if __name__ == "__main__":
    main()
