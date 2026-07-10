from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, patch

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    HealthchecksioPingHelper,
)


def _make_module(**overrides):
    params = {
        "state": "present",
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
    module.jsonify.side_effect = lambda value: value
    return module


def _mock_fetch_success():
    resp = MagicMock()
    resp.read.return_value = b'{"checks": []}'
    info = {"status": 200}
    return resp, info


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url",
    side_effect=lambda *args, **kwargs: _mock_fetch_success(),
)
def test_helper_fetch_url_defaults(mock_fetch_url):
    module = _make_module()
    helper = HealthchecksioHelper(module)
    helper.get("checks")

    _, kwargs = mock_fetch_url.call_args_list[-1]
    assert kwargs["validate_certs"] is True
    assert kwargs["timeout"] == 30


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url",
    side_effect=lambda *args, **kwargs: _mock_fetch_success(),
)
def test_helper_fetch_url_validate_certs_false(mock_fetch_url):
    module = _make_module(validate_certs=False)
    helper = HealthchecksioHelper(module)
    helper.get("checks")

    _, kwargs = mock_fetch_url.call_args_list[-1]
    assert kwargs["validate_certs"] is False


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url",
    side_effect=lambda *args, **kwargs: _mock_fetch_success(),
)
def test_helper_fetch_url_request_timeout(mock_fetch_url):
    module = _make_module(request_timeout=99)
    helper = HealthchecksioHelper(module)
    helper.get("checks")

    _, kwargs = mock_fetch_url.call_args_list[-1]
    assert kwargs["timeout"] == 99


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url",
    side_effect=lambda *args, **kwargs: _mock_fetch_success(),
)
def test_helper_fetch_url_ignores_check_timeout_param(mock_fetch_url):
    module = _make_module(timeout=77)
    helper = HealthchecksioHelper(module)
    helper.get("checks")

    _, kwargs = mock_fetch_url.call_args_list[-1]
    assert kwargs["timeout"] == 30


@patch(
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url",
    side_effect=lambda *args, **kwargs: _mock_fetch_success(),
)
def test_ping_helper_head_forwards_connection_params(mock_fetch_url):
    module = _make_module(validate_certs=False, request_timeout=45)
    helper = HealthchecksioPingHelper(module)
    helper.head("check-uuid", no_headers=True)

    _, kwargs = mock_fetch_url.call_args_list[-1]
    assert kwargs["method"] == "HEAD"
    assert kwargs["validate_certs"] is False
    assert kwargs["timeout"] == 45
