#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: checks
short_description: Create, update, pause, resume, and delete checks
description:
  - Creates a new check and returns its ping URL.
  - For C(state=absent), will delete the check with the given C(uuid).
  - For C(state=pause), will pause the check with the given C(uuid).
  - For C(state=resume), will resume the check with the given C(uuid).
  - Set C(uuid) with C(state=present) to update a specific existing check.
  - All request parameters are optional and will use their default values if omitted.
  - To create a Simple check, specify the C(timeout) parameter.
  - To create a Cron check, specify the C(schedule) and C(tz) parameters.
author: "Mark Mercado (@mamercad)"
version_added: 0.1.0
options:
  state:
    description:
      - C(present) will create or update a check.
      - C(absent) will delete a check.
      - C(pause) will pause a check.
      - C(resume) will resume a paused check.
    type: str
    choices: ["present", "absent", "pause", "resume"]
    default: present
  name:
    description:
      - Name for the new check.
    type: str
    required: false
  tags:
    description:
      - Tags for the check.
    type: list
    elements: str
    required: false
  desc:
    description:
      - Description of the check.
    type: str
    required: false
  timeout:
    description:
      - A number of seconds, the expected period of this check.
      - Minimum 60 (one minute), maximum 31536000 (365 days).
    type: int
    required: false
  grace:
    description:
      - A number of seconds, the grace period for this check.
    type: int
    required: false
  schedule:
    description:
      - A cron or systemd OnCalendar expression defining this check's schedule.
      - If both C(timeout) and C(schedule) are specified, C(schedule) takes precedence.
    type: str
    required: false
  tz:
    description:
      - Server's timezone. This setting only has an effect in combination with the schedule parameter.
    type: str
    required: false
  manual_resume:
    description:
      - Controls whether a paused check automatically resumes when pinged (the default) or not.
      - If set to false, a paused check will leave the paused state when it receives a ping.
      - If set to true, a paused check will ignore pings and stay paused until you manually resume it from the web dashboard.
    type: bool
    required: false
  methods:
    description:
      - Specifies the allowed HTTP methods for making ping requests.
      - Must be one of the two values "" (an empty string) or "POST".
      - Set this field to "" (an empty string) to allow HEAD, GET, and POST requests.
      - Set this field to "POST" to allow only POST requests.
    type: str
    choices: ["", "POST"]
    required: false
  channels:
    description:
      - By default, this API call assigns no integrations to the newly created check.
      - Set this field to a special value "*" to automatically assign all existing integrations.
      - To assign specific integrations, use a comma-separated list of integration UUIDs.
    type: str
    required: false
  unique:
    description:
      - Enables upsert functionality when C(uuid) is not specified.
      - Before creating a check, Healthchecks.io looks for existing checks, filtered by fields listed in C(unique).
      - Accepted values are C(name), C(slug), C(tags), C(timeout), and C(grace).
    type: list
    elements: str
    choices: [name, slug, tags, timeout, grace]
    required: false
  start_kw:
    description:
      - Comma-separated, case-sensitive keywords that classify pings as start signals.
    type: str
  success_kw:
    description:
      - Comma-separated, case-sensitive keywords that classify pings as success signals.
    type: str
  failure_kw:
    description:
      - Comma-separated, case-sensitive keywords that classify pings as failure signals.
    type: str
  filter_subject:
    description:
      - Look for signal keywords in inbound email subject lines.
    type: bool
  filter_body:
    description:
      - Look for signal keywords in inbound email bodies.
    type: bool
  filter_http_body:
    description:
      - Look for signal keywords in HTTP ping request bodies.
    type: bool
  filter_default_fail:
    description:
      - Classify unmatched messages as failures when keyword filtering is enabled.
    type: bool
  uuid:
    description:
      - Check UUID to update, delete, pause, or resume.
      - When set with C(state=present), the module uses the explicit update endpoint.
    type: str
    required: false
  slug:
    description:
      - Optional slug for the check URL.
    type: str
    required: false
extends_documentation_fragment:
  - community.healthchecksio.healthchecksio.documentation
"""

EXAMPLES = r"""
- name: Create a Simple check named "test simple"
  community.healthchecksio.checks:
    state: present
    name: "test simple"
    desc: "my simple test check"
    unique: ["name"]
    tags: ["test", "simple"]
    timeout: 60

- name: Create a Cron check named "test hourly"
  community.healthchecksio.checks:
    state: present
    name: "test hourly"
    unique: ["name"]
    tags: ["test", "hourly"]
    desc: "my hourly test check"
    schedule: "0 * * * *"
    tz: UTC

- name: Resume a manually paused check
  community.healthchecksio.checks:
    state: resume
    uuid: "{{ check_uuid }}"
"""

RETURN = r"""
data:
  description: Create, update, pause or delete response
  returned: always
  type: dict
  sample:
    channels: ''
    desc: ''
    grace: 3600
    last_ping: null
    manual_resume: false
    methods: ''
    n_pings: 0
    name: test
    next_ping: null
    pause_url: https://healthchecks.io/api/v3/checks/524d0f69-0ff3-4120-a2e2-03ebd5736b25/pause
    ping_url: https://hc-ping.com/524d0f69-0ff3-4120-a2e2-03ebd5736b25
    schedule: '* * * * *'
    slug: test
    status: new
    tags: ''
    tz: UTC
    update_url: https://healthchecks.io/api/v3/checks/524d0f69-0ff3-4120-a2e2-03ebd5736b25
msg:
  description: Create, update, pause or delete message
  returned: always
  type: str
  sample: New check 524d0f69-0ff3-4120-a2e2-03ebd5736b25 created
uuid:
  description: Check UUID from create or update
  returned: changed
  type: str
  sample: 524d0f69-0ff3-4120-a2e2-03ebd5736b25
"""

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    Checks,
)
from ansible.module_utils.basic import AnsibleModule


def run(module):
    state = module.params.pop("state")
    checks = Checks(module)
    if state == "present":
        checks.create()
    elif state == "absent":
        checks.delete()
    elif state == "pause":
        checks.pause()
    elif state == "resume":
        checks.resume()


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.update(
        state=dict(
            type="str",
            choices=["present", "absent", "pause", "resume"],
            default="present",
        ),
        name=dict(type="str"),
        tags=dict(type="list", elements="str"),
        desc=dict(type="str"),
        timeout=dict(type="int"),
        grace=dict(type="int"),
        schedule=dict(type="str"),
        tz=dict(type="str"),
        manual_resume=dict(type="bool"),
        methods=dict(type="str", choices=["", "POST"]),
        channels=dict(type="str"),
        unique=dict(
            type="list",
            elements="str",
            choices=["name", "slug", "tags", "timeout", "grace"],
        ),
        uuid=dict(type="str"),
        slug=dict(type="str"),
        start_kw=dict(type="str"),
        success_kw=dict(type="str"),
        failure_kw=dict(type="str"),
        filter_subject=dict(type="bool"),
        filter_body=dict(type="bool"),
        filter_http_body=dict(type="bool"),
        filter_default_fail=dict(type="bool"),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["uuid"]),
            ("state", "pause", ["uuid"]),
            ("state", "resume", ["uuid"]),
        ],
        required_by={"tz": "schedule"},
    )

    run(module)


if __name__ == "__main__":
    main()
