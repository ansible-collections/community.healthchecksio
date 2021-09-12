#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ping
short_description: Signal success, fail, and start events
description:
  - With the Pinging API, you can signal success, fail, and start events from your systems.
author: "Mark Mercado (@mamercad)"
version_added: 0.1.0
options:
  state:
    description:
      - C(present) will send a signal.
    type: str
    choices: ["present"]
    default: present
  uuid:
    description:
      - Check uuid to delete when state is C(absent) or C(pause).
    type: str
    required: true
    default: ""
  signal:
    description:
      - Type of signal to send, C(success), C(fail) or C(start).
    type: str
    choices: ["success", "fail", "start"]
    default: success
extends_documentation_fragment:
  - community.healthchecksio.healthchecksio.documentation
"""

EXAMPLES = r"""
- name: Send a success signal
  community.healthchecksio.ping:
    state: present
    uuid: "{{ check_uuid }}"
    signal: success

- name: Send a fail signal
  community.healthchecksio.ping:
    state: present
    uuid: "{{ check_uuid }}"
    signal: fail

- name: Send a start signal
  community.healthchecksio.ping:
    state: present
    uuid: "{{ check_uuid }}"
    signal: start
"""

RETURN = r"""
msg:
  description: Signal result message
  returned: always
  type: str
  sample: Sent success signal to 8597dcda-23d1-4e6b-b904-83df360bf8a8
"""

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
)
from ansible.module_utils.basic import AnsibleModule, env_fallback


class Ping(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)
        self.api_token = module.params.pop("api_token")

    def create(self, uuid, signal):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        if signal == "success":
            endpoint = "{0}".format(uuid)
        else:
            endpoint = "{0}/{1}".format(uuid, signal)

        response = self.rest.head(endpoint)
        status_code = response.status_code

        if status_code == 200:
            self.module.exit_json(
                changed=True, msg="Sent {0} signal to {1}".format(signal, endpoint)
            )

        else:
            self.module.fail_json(
                changed=False,
                msg="Failed to send {0} signal to {1} [HTTP {2}]".format(
                    signal, endpoint, status_code
                ),
            )


def run(module):
    state = module.params.pop("state")
    uuid = module.params.pop("uuid")
    signal = module.params.pop("signal")
    ping = Ping(module)
    if state == "present":
        ping.create(uuid, signal)


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.update(
        state=dict(type="str", choices=["present"], default="present"),
        uuid=dict(type="str", required=True),
        signal=dict(
            type="str",
            choices=["success", "fail", "start"],
            required=False,
            default="success",
        ),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    run(module)


if __name__ == "__main__":
    main()
