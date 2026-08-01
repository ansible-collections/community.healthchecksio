from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ansible_collections.community.healthchecksio.plugins.modules import channels_info
from ansible_collections.community.healthchecksio.tests.unit.plugins.modules.utils import (
    make_module,
    run_main,
)


def test_run_gets_channels_for_present_state():
    module = make_module(state="present")
    with patch.object(channels_info, "ChannelsInfo") as channels:
        channels_info.run(module)
    channels.assert_called_once_with(module)
    channels.return_value.get.assert_called_once_with()


def test_run_ignores_unknown_state():
    module = make_module(state="unknown")
    with patch.object(channels_info, "ChannelsInfo") as channels:
        channels_info.run(module)
    channels.return_value.get.assert_not_called()


def test_main_builds_check_mode_module_and_runs_it():
    module = make_module()
    ansible_module = run_main(channels_info, module)
    kwargs = ansible_module.call_args.kwargs
    assert kwargs["supports_check_mode"] is True
    assert kwargs["argument_spec"]["state"] == dict(
        type="str", choices=["present"], default="present"
    )
