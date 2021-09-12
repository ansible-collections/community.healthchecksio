#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: badges_info
short_description: Get the project badges
description:
  - Get the project badges
author: "Mark Mercado (@mamercad)"
version_added: 0.1.0
options:
  state:
    description:
      - C(present) will return the integrations.
    type: str
    choices: ["present"]
    default: present
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


class BadgesInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        endpoint = "badges"

        response = self.rest.get(endpoint)
        json_data = response.json
        status_code = response.status_code

        if status_code != 200:
            self.module.fail_json(
                changed=False,
                msg="Failed to get {0} [HTTP {1}: {2}]".format(
                    endpoint,
                    status_code,
                    json_data.get("message", "(empty error message)"),
                ),
            )

        self.module.exit_json(changed=False, data=json_data)


def run(module):
    state = module.params.pop("state")
    badges = BadgesInfo(module)
    if state == "present":
        badges.get()


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.update(
        state=dict(type="str", choices=["present"], default="present"),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    run(module)


if __name__ == "__main__":
    main()
