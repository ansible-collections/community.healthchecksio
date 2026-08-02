from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ansible_collections.community.healthchecksio.plugins.modules import checks_info
from ansible_collections.community.healthchecksio.tests.unit.plugins.modules.utils import (
    make_module,
    run_main,
)


def test_run_gets_checks_for_present_state():
    module = make_module(state="present")
    with patch.object(checks_info, "ChecksInfo") as checks:
        checks_info.run(module)
    checks.assert_called_once_with(module)
    checks.return_value.get.assert_called_once_with()


def test_run_ignores_unknown_state():
    module = make_module(state="unknown")
    with patch.object(checks_info, "ChecksInfo") as checks:
        checks_info.run(module)
    checks.return_value.get.assert_not_called()


def test_main_builds_filters_and_runs_module():
    module = make_module()
    ansible_module = run_main(checks_info, module)
    kwargs = ansible_module.call_args[1]
    assert kwargs["supports_check_mode"] is True
    assert ("uuid", "unique_key") in kwargs["mutually_exclusive"]
    assert ("uuid", "slug") in kwargs["mutually_exclusive"]
    assert set(("tags", "uuid", "unique_key", "slug", "name")) <= set(
        kwargs["argument_spec"]
    )
