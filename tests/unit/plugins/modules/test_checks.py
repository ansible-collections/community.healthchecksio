from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

import pytest

from ansible_collections.community.healthchecksio.plugins.modules import checks
from ansible_collections.community.healthchecksio.tests.unit.plugins.modules.utils import (
    make_module,
    run_main,
)


@pytest.mark.parametrize(
    ("state", "method"),
    [("present", "create"), ("absent", "delete"), ("pause", "pause")],
)
def test_run_dispatches_state(state, method):
    module = make_module(state=state)
    with patch.object(checks, "Checks") as checks_class:
        checks.run(module)
    checks_class.assert_called_once_with(module)
    getattr(checks_class.return_value, method).assert_called_once_with()


def test_run_ignores_unknown_state():
    module = make_module(state="unknown")
    with patch.object(checks, "Checks") as checks_class:
        checks.run(module)
    checks_class.return_value.create.assert_not_called()
    checks_class.return_value.delete.assert_not_called()
    checks_class.return_value.pause.assert_not_called()


def test_main_builds_state_constraints_and_runs_module():
    module = make_module()
    ansible_module = run_main(checks, module)
    kwargs = ansible_module.call_args[1]
    assert kwargs["supports_check_mode"] is True
    assert kwargs["required_if"] == [
        ("state", "absent", ["uuid"]),
        ("state", "pause", ["uuid"]),
    ]
    assert kwargs["required_together"] == [("schedule", "tz")]
    assert kwargs["mutually_exclusive"] == [
        ("timeout", "schedule"),
        ("timeout", "tz"),
    ]
    assert kwargs["argument_spec"]["state"]["choices"] == [
        "present",
        "absent",
        "pause",
    ]
