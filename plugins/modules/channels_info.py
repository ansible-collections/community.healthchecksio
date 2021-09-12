#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: channels_info
short_description: Get a list of integrations
description:
  - Returns a list of integrations belonging to the project.
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
- name: Get a list of integrations
  community.healthchecksio.channels_info:
    state: present
    api_token: "{{ lookup('ansible.builtin.env', 'HEALTHCHECKSIO_API_TOKEN') }}"
"""

RETURN = r"""
data:
  description: Project integrations
  returned: always
  type: dict
  sample:
    channels:
    - id: 82a60fd3-5ae3-4a9e-9747-00097de67711
      kind: email
      name: Email
    - id: 853de669-6910-4bc1-a4cc-55f774a135fd
      kind: slack
      name: ''
"""


from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
)
from ansible.module_utils.basic import AnsibleModule, env_fallback


class ChannelsInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        endpoint = "channels"

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
    channels = ChannelsInfo(module)
    if state == "present":
        channels.get()


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
