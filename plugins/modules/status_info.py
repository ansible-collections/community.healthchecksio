#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: status_info
short_description: Check Healthchecks.io service status
description:
  - Runs the Management API database connectivity check.
  - This endpoint does not require an API key.
author: "Mark Mercado (@mamercad)"
version_added: 2.0.0
extends_documentation_fragment:
  - community.healthchecksio.healthchecksio.documentation
"""

EXAMPLES = r"""
- name: Verify Healthchecks.io database connectivity
  community.healthchecksio.status_info:
"""

RETURN = r"""
status:
  description: Service status.
  returned: success
  type: str
  sample: ok
"""

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    StatusInfo,
)
from ansible.module_utils.basic import AnsibleModule


def run(module):
    StatusInfo(module).get()


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.pop("state", None)
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    run(module)


if __name__ == "__main__":  # pragma: no cover
    main()
