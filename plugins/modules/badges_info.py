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
  - Returns a map of all tags in the project, with badge URLs for each tag.
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
- name: Get the project badges
  community.healthchecksio.badges_info:
    state: present
    api_token: "{{ lookup('ansible.builtin.env', 'HEALTHCHECKSIO_API_TOKEN') }}"
"""

RETURN = r"""
data:
  description: Project badges
  returned: always
  type: dict
  sample:
    badges:
      '*':
        json: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/_JD3lXcF-2.json
        json3: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/_JD3lXcF.json
        shields: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/_JD3lXcF-2.shields
        shields3: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/_JD3lXcF.shields
        svg: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/_JD3lXcF-2.svg
        svg3: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/_JD3lXcF.svg
      test:
        json: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/e823bLfZ-2/test.json
        json3: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/e823bLfZ/test.json
        shields: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/e823bLfZ-2/test.shields
        shields3: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/e823bLfZ/test.shields
        svg: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/e823bLfZ-2/test.svg
        svg3: https://healthchecks.io/badge/5dc9afdd-f4da-4b74-bb83-84430f/e823bLfZ/test.svg
"""


from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    BadgesInfo,
)
from ansible.module_utils.basic import AnsibleModule, env_fallback


def run(module):
    state = module.params.pop("state")
    badges = BadgesInfo(module)
    if state == "present":
        badges.get()


def main():
    argument_spec = HealthchecksioHelper.healthchecksio_argument_spec()
    argument_spec.update(state=dict(type="str", choices=["present"], default="present"))
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    run(module)


if __name__ == "__main__":
    main()
