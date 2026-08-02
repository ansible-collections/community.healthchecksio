from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ansible_collections.community.healthchecksio.plugins.modules import (
    checks_flips_info,
)
from ansible_collections.community.healthchecksio.tests.unit.plugins.modules.utils import (
    make_module,
    run_main,
)


def test_run_gets_flips_for_present_state():
    module = make_module(state="present")
    with patch.object(checks_flips_info, "ChecksFlipsInfo") as flips:
        checks_flips_info.run(module)
    flips.assert_called_once_with(module)
    flips.return_value.get.assert_called_once_with()


def test_run_ignores_unknown_state():
    module = make_module(state="unknown")
    with patch.object(checks_flips_info, "ChecksFlipsInfo") as flips:
        checks_flips_info.run(module)
    flips.return_value.get.assert_not_called()


def test_main_builds_check_mode_module_and_runs_it():
    module = make_module()
    ansible_module = run_main(checks_flips_info, module)
    kwargs = ansible_module.call_args[1]
    assert kwargs["supports_check_mode"] is True
    assert kwargs["argument_spec"]["uuid"] == dict(type="str", required=False)
    assert kwargs["required_one_of"] == [("uuid", "unique_key")]
    assert ("seconds", "start") in kwargs["mutually_exclusive"]
    assert set(("unique_key", "seconds", "start", "end")) <= set(
        kwargs["argument_spec"]
    )
