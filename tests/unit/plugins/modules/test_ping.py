from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    Ping,
)
from ansible_collections.community.healthchecksio.plugins.modules import ping as ping_module


class ExitJson(Exception):
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
    return module


def _mock_fetch_success():
    resp = MagicMock()
    resp.read.return_value = b'{"checks": []}'
    info = {"status": 200}
    return resp, info


def _last_fetch_url(mock_fetch_url):
    return mock_fetch_url.call_args_list[-1][0][1]


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url",
    side_effect=lambda *args, **kwargs: _mock_fetch_success(),
)
def test_ping_create_appends_runid_as_rid_query_param(mock_fetch_url):
    module = _make_module()
    ping = Ping(module)

    try:
        ping.create(
            "check-uuid",
            "start",
            "728b3763-ea80-4113-9fc0-f49b3adf226a",
        )
    except ExitJson:
        pass

    assert (
        _last_fetch_url(mock_fetch_url)
        == "https://hc-ping.com/check-uuid/start?rid=728b3763-ea80-4113-9fc0-f49b3adf226a"
    )


def test_run_passes_runid_to_ping():
    module = _make_module(
        state="present",
        uuid="check-uuid",
        signal="success",
        runid="728b3763-ea80-4113-9fc0-f49b3adf226a",
    )

    with patch.object(ping_module, "Ping") as ping_cls:
        ping_module.run(module)

    ping_cls.return_value.create.assert_called_once_with(
        "check-uuid",
        "success",
        "728b3763-ea80-4113-9fc0-f49b3adf226a",
    )
