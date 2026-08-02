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
        "management_api_base_url": "https://healthchecks.io/api/v3",
        "ping_api_base_url": "https://hc-ping.com",
        "ping_api_token": None,
        "validate_certs": True,
        "request_timeout": 30,
    }
    params.update(overrides)
    module = MagicMock()
    module.params = params
    module.check_mode = False
    module.exit_json.side_effect = ExitJson
    module.fail_json.side_effect = FailJson
    return module


def _mock_fetch(status=200, body=b"OK"):
    resp = MagicMock()
    resp.read.return_value = body
    return resp, {"status": status}


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url"
)
@pytest.mark.parametrize(
    "signal,endpoint",
    [
        ("success", "check-uuid"),
        ("start", "check-uuid/start"),
        ("fail", "check-uuid/fail"),
        ("log", "check-uuid/log"),
    ],
)
def test_ping_create_sends_uuid_signals(fetch, signal, endpoint):
    fetch.return_value = _mock_fetch()
    module = _make_module()
    with pytest.raises(ExitJson):
        Ping(module).create("check-uuid", signal)
    assert fetch.call_args[0][1] == "https://hc-ping.com/" + endpoint
    assert fetch.call_args[1]["method"] == "HEAD"
    assert fetch.call_args[1]["headers"] is None


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url"
)
def test_ping_create_supports_slug_runid_body_and_create(fetch):
    fetch.return_value = _mock_fetch(status=201)
    module = _make_module(ping_api_token="project-key")
    with pytest.raises(ExitJson):
        Ping(module).create(
            slug="backup",
            signal="start",
            runid="run id/1",
            body="diagnostic",
            create=True,
        )
    assert fetch.call_args[0][1] == (
        "https://hc-ping.com/project-key/backup/start?rid=run%20id%2F1&create=1"
    )
    assert fetch.call_args[1]["method"] == "POST"
    assert fetch.call_args[1]["data"] == b"diagnostic"
    assert fetch.call_args[1]["headers"] == {
        "Content-Type": "text/plain; charset=utf-8"
    }
    assert module.exit_json.call_args[1]["msg"] == "Sent start signal to backup"
    assert "project-key" not in module.exit_json.call_args[1]["msg"]


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url"
)
def test_ping_create_reports_exit_status(fetch):
    fetch.return_value = _mock_fetch()
    module = _make_module()
    with pytest.raises(ExitJson):
        Ping(module).create(uuid="check-uuid", exit_status=17, method="GET")
    assert fetch.call_args[0][1] == "https://hc-ping.com/check-uuid/17"
    assert fetch.call_args[1]["method"] == "GET"
    assert "17 signal" in module.exit_json.call_args[1]["msg"]


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url"
)
def test_ping_create_reports_http_failure(fetch):
    fetch.return_value = _mock_fetch(status=503)
    module = _make_module()
    with pytest.raises(FailJson):
        Ping(module).create("check-uuid", "fail")
    module.fail_json.assert_called_once_with(
        changed=False,
        msg="Failed to send fail signal to check-uuid [HTTP 503]",
    )


def test_ping_create_is_noop_in_check_mode():
    module = _make_module()
    module.check_mode = True
    with pytest.raises(ExitJson):
        Ping(module).create("check-uuid")
    module.exit_json.assert_called_once_with(changed=False, data={})


def test_run_passes_complete_request_to_ping():
    module = _make_module(
        state="present",
        uuid=None,
        slug="backup",
        signal="log",
        exit_status=None,
        runid="728b3763-ea80-4113-9fc0-f49b3adf226a",
        body="output",
        method="POST",
        create=True,
        ping_api_token="project-key",
    )
    with patch.object(ping_module, "Ping") as ping_class:
        ping_module.run(module)
    ping_class.return_value.create.assert_called_once_with(
        uuid=None,
        slug="backup",
        signal="log",
        runid="728b3763-ea80-4113-9fc0-f49b3adf226a",
        body="output",
        method="POST",
        create=True,
        exit_status=None,
    )


def test_run_uses_public_ping_defaults_when_parameters_are_missing():
    module = _make_module(
        state="present",
        uuid="abc",
        slug=None,
        exit_status=None,
    )
    with patch.object(ping_module, "Ping") as ping_class:
        ping_module.run(module)
    ping_class.return_value.create.assert_called_once_with(
        uuid="abc",
        slug=None,
        signal="success",
        runid=None,
        body=None,
        method="HEAD",
        create=False,
        exit_status=None,
    )


@pytest.mark.parametrize(
    "params,text",
    [
        ({"state": "present", "slug": "backup", "uuid": None}, "ping_api_token"),
        (
            {
                "state": "present",
                "slug": None,
                "uuid": "abc",
                "create": True,
            },
            "only supported",
        ),
        (
            {
                "state": "present",
                "slug": None,
                "uuid": "abc",
                "exit_status": 256,
            },
            "between 0 and 255",
        ),
        (
            {
                "state": "present",
                "slug": None,
                "uuid": "abc",
                "body": "diagnostic",
                "method": "GET",
            },
            "cannot be used",
        ),
    ],
)
def test_run_validates_conditional_inputs(params, text):
    module = _make_module(**params)
    with pytest.raises(FailJson):
        ping_module.run(module)
    assert text in module.fail_json.call_args[1]["msg"]


def test_run_ignores_unknown_state():
    module = _make_module(state="unknown")
    with patch.object(ping_module, "Ping") as ping_class:
        ping_module.run(module)
    ping_class.return_value.create.assert_not_called()


def test_main_builds_ping_arguments_and_runs_module():
    module = _make_module()
    ansible_module = run_main(ping_module, module)
    kwargs = ansible_module.call_args[1]
    assert kwargs["supports_check_mode"] is True
    assert kwargs["required_one_of"] == [("uuid", "slug")]
    assert kwargs["mutually_exclusive"] == [("uuid", "slug")]
    assert kwargs["argument_spec"]["signal"]["choices"] == [
        "success",
        "fail",
        "start",
        "log",
    ]
    assert kwargs["argument_spec"]["method"]["choices"] == ["HEAD", "GET", "POST"]
    assert kwargs["argument_spec"]["signal"]["default"] == "success"
    assert kwargs["argument_spec"]["method"]["default"] == "HEAD"
    assert kwargs["argument_spec"]["create"]["default"] is False
    assert set(("slug", "exit_status", "body", "create")) <= set(
        kwargs["argument_spec"]
    )
