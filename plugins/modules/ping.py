#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: ping
short_description: Send Healthchecks.io ping events
description:
  - Signals success, failure, start, log, or process exit status events.
  - Identifies a check by C(uuid), or by C(slug) together with the project C(ping_api_token).
  - A request body is sent with HTTP POST and stored as diagnostic data by Healthchecks.io.
author: "Mark Mercado (@mamercad)"
version_added: 0.1.0
options:
  state:
    description:
      - C(present) sends the event.
    type: str
    choices: [present]
    default: present
  uuid:
    description:
      - Immutable check UUID.
      - Mutually exclusive with C(slug).
    type: str
  slug:
    description:
      - Check slug. Requires the project ping key in C(ping_api_token).
      - Mutually exclusive with C(uuid).
    type: str
    version_added: 2.0.0
  signal:
    description:
      - Event type to send.
      - C(log) stores diagnostic data without changing check status.
      - Ignored when C(exit_status) is specified.
    type: str
    choices: [success, fail, start, log]
    default: success
  exit_status:
    description:
      - Process exit status from 0 through 255.
      - Healthchecks.io interprets 0 as success and all other values as failure.
    type: int
    version_added: 2.0.0
  runid:
    description:
      - Optional run ID sent in the Healthchecks.io C(rid) query parameter.
      - Use the same canonical UUID for matching start and completion pings from one execution.
    type: str
    version_added: 1.5.0
  body:
    description:
      - Optional diagnostic text to store with the ping.
      - Supplying a body changes the default C(method) from C(HEAD) to C(POST).
    type: str
    version_added: 2.0.0
  method:
    description:
      - HTTP method used for the ping request.
      - C(GET) cannot be used together with C(body); use C(POST) instead.
    type: str
    choices: [HEAD, GET, POST]
    default: HEAD
    version_added: 2.0.0
  create:
    description:
      - Automatically create a missing check when pinging by C(slug).
      - Maps to the Pinging API C(create=1) query parameter.
    type: bool
    default: false
    version_added: 2.0.0
extends_documentation_fragment:
  - community.healthchecksio.healthchecksio.documentation
"""

EXAMPLES = r"""
- name: Send a success signal by UUID
  community.healthchecksio.ping:
    uuid: "{{ check_uuid }}"

- name: Send a failure signal with diagnostic output
  community.healthchecksio.ping:
    uuid: "{{ check_uuid }}"
    signal: fail
    body: "{{ job_stderr }}"

- name: Send a start signal by slug and run ID
  community.healthchecksio.ping:
    slug: database-backup
    ping_api_token: "{{ project_ping_key }}"
    signal: start
    runid: "{{ run_id }}"

- name: Report a process exit status
  community.healthchecksio.ping:
    uuid: "{{ check_uuid }}"
    exit_status: "{{ command_result.rc }}"
"""

RETURN = r"""
msg:
  description: Event result message.
  returned: success
  type: str
  sample: Sent success signal to 8597dcda-23d1-4e6b-b904-83df360bf8a8
"""

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    DEFAULT_PING_CREATE,
    DEFAULT_PING_METHOD,
    DEFAULT_PING_SIGNAL,
    HealthchecksioHelper,
    Ping,
)
from ansible.module_utils.basic import AnsibleModule


def run(module):
    params = dict(module.params)
    state = params.pop("state")
    if state != "present":
        return

    uuid = params.pop("uuid", None)
    slug = params.pop("slug", None)
    exit_status = params.pop("exit_status", None)
    if slug and not params.get("ping_api_token"):
        module.fail_json(msg="ping_api_token is required when slug is specified")
    if params.get("create") and not slug:
        module.fail_json(msg="create is only supported when slug is specified")
    if exit_status is not None and not 0 <= exit_status <= 255:
        module.fail_json(msg="exit_status must be between 0 and 255")
    if params.get("body") is not None and params.get("method") == "GET":
        module.fail_json(msg="body cannot be used with method=GET; use POST")

    ping = Ping(module)
    ping.create(
        uuid=uuid,
        slug=slug,
        signal=params.pop("signal", DEFAULT_PING_SIGNAL),
        runid=params.pop("runid", None),
        body=params.pop("body", None),
        method=params.pop("method", DEFAULT_PING_METHOD),
        create=params.pop("create", DEFAULT_PING_CREATE),
        exit_status=exit_status,
    )


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.update(
        state=dict(type="str", choices=["present"], default="present"),
        uuid=dict(type="str"),
        slug=dict(type="str"),
        signal=dict(
            type="str",
            choices=["success", "fail", "start", "log"],
            default=DEFAULT_PING_SIGNAL,
        ),
        exit_status=dict(type="int"),
        runid=dict(type="str"),
        body=dict(type="str"),
        method=dict(
            type="str",
            choices=["HEAD", "GET", "POST"],
            default=DEFAULT_PING_METHOD,
        ),
        create=dict(type="bool", default=DEFAULT_PING_CREATE),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[("uuid", "slug")],
        mutually_exclusive=[("uuid", "slug")],
    )
    run(module)


if __name__ == "__main__":
    main()
