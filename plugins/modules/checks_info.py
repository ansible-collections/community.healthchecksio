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
  - Returns checks, optionally filtered by slug or one or more tags.
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
      - If specified, returns this specific check by UUID.
    type: str
    required: false
  unique_key:
    description:
      - If specified, returns a specific check by the stable identifier from read-only API responses.
    type: str
    required: false
  slug:
    description:
      - Filters checks by their exact slug.
    type: str
    required: false
  name:
    description:
      - If specified, filters the checks and returns the check with this name.
    type: str
    required: false
    version_added: 1.5.0
extends_documentation_fragment:
  - community.healthchecksio.healthchecksio.documentation
"""

EXAMPLES = r"""
- name: Get all checks tagged production
  community.healthchecksio.checks_info:
    tags: [production]

- name: Get a check using a read-only API key identifier
  community.healthchecksio.checks_info:
    unique_key: "{{ check_unique_key }}"
"""

RETURN = r"""
"""


from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    ChecksInfo,
)
from ansible.module_utils.basic import AnsibleModule


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
        unique_key=dict(type="str", required=False, no_log=False),
        slug=dict(type="str", required=False),
        name=dict(type="str", required=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ("uuid", "unique_key"),
            ("uuid", "tags"),
            ("uuid", "slug"),
            ("uuid", "name"),
            ("unique_key", "tags"),
            ("unique_key", "slug"),
            ("unique_key", "name"),
        ],
    )

    run(module)


if __name__ == "__main__":
    main()
