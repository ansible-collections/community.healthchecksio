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


class ChecksFlipsInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        uuid = self.module.params.get("uuid", None)
        endpoint = "checks/{0}/flips".format(uuid)

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
    flips = ChecksFlipsInfo(module)
    if state == "present":
        flips.get()


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.update(
        state=dict(type="str", choices=["present"], default="present"),
        uuid=dict(type="str", required=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    run(module)


if __name__ == "__main__":
    main()
