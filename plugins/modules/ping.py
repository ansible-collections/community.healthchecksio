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
    Ping,
)
from ansible.module_utils.basic import AnsibleModule, env_fallback


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
