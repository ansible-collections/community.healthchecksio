from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ansible_collections.community.healthchecksio.plugins.modules import (
    checks_pings_info,
)
from ansible_collections.community.healthchecksio.tests.unit.plugins.modules.utils import (
    make_module,
    run_main,
)


def test_run_gets_pings_for_present_state():
    module = make_module(state="present")
    with patch.object(checks_pings_info, "ChecksPingsInfo") as pings:
        checks_pings_info.run(module)
    pings.assert_called_once_with(module)
    pings.return_value.get.assert_called_once_with()


def test_run_ignores_unknown_state():
    module = make_module(state="unknown")
    with patch.object(checks_pings_info, "ChecksPingsInfo") as pings:
        checks_pings_info.run(module)
    pings.return_value.get.assert_not_called()


def test_main_builds_check_mode_module_and_runs_it():
    module = make_module()
    ansible_module = run_main(checks_pings_info, module)
    kwargs = ansible_module.call_args.kwargs
    assert kwargs["supports_check_mode"] is True
    assert kwargs["argument_spec"]["uuid"] == dict(type="str", required=False)
