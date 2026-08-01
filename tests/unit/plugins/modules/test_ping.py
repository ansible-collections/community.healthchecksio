from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch

import pytest

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    Ping,
)
from ansible_collections.community.healthchecksio.plugins.modules import (
    ping as ping_module,
)
from ansible_collections.community.healthchecksio.tests.unit.plugins.modules.utils import (
    run_main,
)


class ExitJson(Exception):
    pass


class FailJson(Exception):
    pass


def _make_module(**overrides):
    params = {
        "management_api_token": "test-token",
        "management_api_base_url": "https://healthchecks.io/api/v1",
        "ping_api_base_url": "https://hc-ping.com",
        "ping_api_token": None,
        "validate_certs": True,
        "request_timeout": 30,
    }
    params.update(overrides)
    module = MagicMock()
    module.params = params
    module.check_mode = False
    module.jsonify.side_effect = lambda value: value
    module.exit_json.side_effect = ExitJson
    module.fail_json.side_effect = FailJson
    return module


def _mock_fetch(status=200, body=b'{"checks": []}'):
    resp = MagicMock()
    resp.read.return_value = body
    return resp, {"status": status}


def _last_fetch_url(mock_fetch_url):
    return mock_fetch_url.call_args_list[-1][0][1]


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url"
)
@pytest.mark.parametrize(
    ("signal", "endpoint"),
    [
        ("success", "check-uuid"),
        ("start", "check-uuid/start"),
        ("fail", "check-uuid/fail"),
    ],
)
def test_ping_create_sends_each_signal(mock_fetch_url, signal, endpoint):
    mock_fetch_url.return_value = _mock_fetch()
    module = _make_module()
    with pytest.raises(ExitJson):
        Ping(module).create("check-uuid", signal)
    assert _last_fetch_url(mock_fetch_url) == "https://hc-ping.com/" + endpoint
    module.exit_json.assert_called_once_with(
        changed=True,
        msg="Sent {0} signal to {1}".format(signal, endpoint),
    )


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url"
)
def test_ping_create_appends_encoded_runid_as_rid_query_param(mock_fetch_url):
    mock_fetch_url.return_value = _mock_fetch()
    module = _make_module()
    with pytest.raises(ExitJson):
        Ping(module).create("check-uuid", "start", "run id/1")
    assert (
        _last_fetch_url(mock_fetch_url)
        == "https://hc-ping.com/check-uuid/start?rid=run%20id%2F1"
    )
    module.exit_json.assert_called_once_with(
        changed=True,
        msg="Sent start signal to check-uuid/start",
    )


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url"
)
def test_ping_create_reports_http_failure(mock_fetch_url):
    mock_fetch_url.return_value = _mock_fetch(status=503)
    module = _make_module()
    with pytest.raises(FailJson):
        Ping(module).create("check-uuid", "fail")
    module.fail_json.assert_called_once_with(
        changed=False,
        msg="Failed to send fail signal to check-uuid/fail [HTTP 503]",
    )


def test_ping_create_is_noop_in_check_mode():
    module = _make_module()
    module.check_mode = True
    with pytest.raises(ExitJson):
        Ping(module).create("check-uuid", "success")
    module.exit_json.assert_called_once_with(changed=False, data={})


def test_run_passes_runid_to_ping():
    module = _make_module(
        state="present",
        uuid="check-uuid",
        signal="success",
        runid="728b3763-ea80-4113-9fc0-f49b3adf226a",
    )
    with patch.object(ping_module, "Ping") as ping_class:
        ping_module.run(module)
    ping_class.return_value.create.assert_called_once_with(
        "check-uuid",
        "success",
        "728b3763-ea80-4113-9fc0-f49b3adf226a",
    )


def test_run_ignores_unknown_state():
    module = _make_module(
        state="unknown",
        uuid="check-uuid",
        signal="success",
        runid=None,
    )
    with patch.object(ping_module, "Ping") as ping_class:
        ping_module.run(module)
    ping_class.return_value.create.assert_not_called()


def test_main_builds_ping_arguments_and_runs_module():
    module = _make_module()
    ansible_module = run_main(ping_module, module)
    kwargs = ansible_module.call_args[1]
    assert kwargs["supports_check_mode"] is True
    assert kwargs["argument_spec"]["uuid"] == dict(type="str", required=True)
    assert kwargs["argument_spec"]["signal"]["choices"] == [
        "success",
        "fail",
        "start",
    ]
    assert kwargs["argument_spec"]["runid"] == dict(type="str", required=False)
