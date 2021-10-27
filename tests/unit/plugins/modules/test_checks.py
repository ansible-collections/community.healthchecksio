from __future__ import absolute_import, division, print_function

__metaclass__ = type

from argparse import ArgumentParser

from ansible_collections.community.general.tests.unit.compat import unittest
from ansible_collections.community.general.tests.unit.compat.mock import patch

# from ansible.errors import AnsibleError
from ansible.module_utils import six

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    Checks,
)


class TestChecksPlugin:
    def test_checks(self):
        assert True
