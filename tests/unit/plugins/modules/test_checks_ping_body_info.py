from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ansible_collections.community.healthchecksio.plugins.modules import (
    checks_ping_body_info,
)
from ansible_collections.community.healthchecksio.tests.unit.plugins.modules.utils import (
    make_module,
    run_main,
)


def test_run_gets_ping_body():
    module = make_module()
    with patch.object(checks_ping_body_info, "ChecksPingBodyInfo") as body_info:
        checks_ping_body_info.run(module)
    body_info.assert_called_once_with(module)
    body_info.return_value.get.assert_called_once_with()


def test_main_requires_uuid_and_sequence():
    module = make_module()
    ansible_module = run_main(checks_ping_body_info, module)
    kwargs = ansible_module.call_args[1]
    assert kwargs["supports_check_mode"] is True
    assert "state" not in kwargs["argument_spec"]
    assert kwargs["argument_spec"]["uuid"]["required"] is True
    assert kwargs["argument_spec"]["sequence"] == dict(type="int", required=True)
