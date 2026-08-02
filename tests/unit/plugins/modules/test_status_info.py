from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ansible_collections.community.healthchecksio.plugins.modules import status_info
from ansible_collections.community.healthchecksio.tests.unit.plugins.modules.utils import (
    make_module,
    run_main,
)


def test_run_gets_status():
    module = make_module()
    with patch.object(status_info, "StatusInfo") as status:
        status_info.run(module)
    status.assert_called_once_with(module)
    status.return_value.get.assert_called_once_with()


def test_main_does_not_require_state_or_api_key():
    module = make_module()
    ansible_module = run_main(status_info, module)
    kwargs = ansible_module.call_args[1]
    assert kwargs["supports_check_mode"] is True
    assert "state" not in kwargs["argument_spec"]
    assert kwargs["argument_spec"]["management_api_token"]["required"] is False
