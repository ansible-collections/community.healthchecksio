from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    ChecksInfo,
)


class TestChecksInfoPlugin:
    def test_checks_info(self):
        assert True
