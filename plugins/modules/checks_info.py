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
)
from ansible.module_utils.basic import AnsibleModule, env_fallback


class ChecksInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        endpoint = "checks"

        tags = self.module.params.get("tags", None)
        if tags is not None:
            tags = ["tag=" + tag for tag in tags]
            tags = "&".join(tags)
            if tags:
                endpoint += "?" + tags

        uuid = self.module.params.get("uuid", None)
        if uuid is not None:
            endpoint += "/" + uuid

        response = self.rest.get(endpoint)
        json_data = response.json
        status_code = response.status_code

        if status_code != 200:
            self.module.fail_json(
                changed=False,
                msg="Failed to get {0} [HTTP {1}]".format(
                    endpoint,
                    status_code,
                ),
            )

        self.module.exit_json(changed=False, data=json_data)


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
