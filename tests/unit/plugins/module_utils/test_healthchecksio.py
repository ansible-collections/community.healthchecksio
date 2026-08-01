from __future__ import absolute_import, division, print_function

try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch

import pytest

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    BadgesInfo,
    ChannelsInfo,
    Checks,
    ChecksFlipsInfo,
    ChecksInfo,
    ChecksPingsInfo,
    HealthchecksioHelper,
    HealthchecksioPingHelper,
    Response,
)


class AnsibleResult(Exception):
    def __init__(self, values=None, **kwargs):
        self.kwargs = values or kwargs
        Exception.__init__(self, self.kwargs)


class ExitJson(AnsibleResult):
    pass


class FailJson(AnsibleResult):
    pass


PATH = (
    "ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio"
)


def module(**overrides):
    params = dict(
        state="present",
        management_api_token="token",
        management_api_base_url="https://healthchecks.io/api/v1",
        ping_api_base_url="https://hc-ping.com",
        ping_api_token=None,
        validate_certs=True,
        request_timeout=30,
    )
    params.update(overrides)
    result = MagicMock()
    result.params = params
    result.check_mode = False
    result.diff_mode = False
    result.jsonify.side_effect = lambda value: value
    result.exit_json.side_effect = ExitJson
    result.fail_json.side_effect = FailJson
    return result


def response(status=200, data=None):
    result = MagicMock()
    result.status_code = status
    result.json = {} if data is None else data
    return result


def service(cls, mod=None):
    result = cls.__new__(cls)
    result.module = mod or module()
    result.rest = MagicMock()
    return result


def result_kwargs(mod):
    call = mod.fail_json.call_args if mod.fail_json.called else mod.exit_json.call_args
    return call.kwargs


def fetch_success():
    resp = MagicMock()
    resp.read.return_value = b'{"checks": []}'
    return resp, {"status": 200}


def test_response_parses_body_and_status():
    resp = MagicMock()
    resp.read.return_value = b'{"ok": true}'
    result = Response(resp, {"status": 201})
    assert result.json == {"ok": True}
    assert result.status_code == 201


@pytest.mark.parametrize(
    "resp,info,expected",
    [
        (None, {"status": 204}, None),
        (None, {"status": 400, "body": b'{"error": "bad"}'}, {"error": "bad"}),
        (None, {"status": 500, "body": b"bad"}, {}),
    ],
)
def test_response_handles_info_body(resp, info, expected):
    assert Response(resp, info).json == expected


def test_response_handles_invalid_body():
    resp = MagicMock()
    resp.read.return_value = b"bad"
    assert Response(resp, {"status": 200}).json is None


@patch(PATH + ".fetch_url", side_effect=lambda *args, **kwargs: fetch_success())
def test_helper_initializes_and_forwards_connection_settings(fetch):
    mod = module(validate_certs=False, request_timeout=45, timeout=90)
    helper = HealthchecksioHelper(mod)
    helper.get("checks")
    kwargs = fetch.call_args.kwargs
    assert fetch.call_args.args[0] is mod
    assert kwargs["timeout"] == 45
    assert kwargs["headers"] == {"X-Api-Key": "token"}
    assert "validate_certs" not in kwargs


@patch(PATH + ".fetch_url")
def test_helper_rejects_invalid_token(fetch):
    fetch.return_value = (None, {"status": 401, "body": b"{}"})
    mod = module()
    with pytest.raises(FailJson):
        HealthchecksioHelper(mod)
    assert "Failed to login" in result_kwargs(mod)["msg"]


@patch(PATH + ".fetch_url", side_effect=lambda *args, **kwargs: fetch_success())
def test_helper_builds_urls(fetch):
    helper = HealthchecksioHelper(module())
    assert helper._url_builder("checks") == "https://healthchecks.io/api/v1/checks"
    assert helper._url_builder("/checks") == "https://healthchecks.io/api/v1/checks"


@pytest.mark.parametrize(
    "name,method",
    [("get", "GET"), ("put", "PUT"), ("post", "POST"), ("delete", "DELETE")],
)
@patch(PATH + ".fetch_url", side_effect=lambda *args, **kwargs: fetch_success())
def test_helper_dispatches_methods(fetch, name, method):
    mod = module()
    mod.jsonify.side_effect = lambda value: '{"name":"x"}'
    helper = HealthchecksioHelper(mod)
    getattr(helper, name)("checks", {"name": "x"})
    assert fetch.call_args.kwargs["method"] == method
    assert fetch.call_args.kwargs["data"] == '{"name":"x"}'


@patch(PATH + ".fetch_url", side_effect=lambda *args, **kwargs: fetch_success())
def test_helper_delete_omits_null_body(fetch):
    mod = module()
    mod.jsonify.return_value = "null"
    helper = HealthchecksioHelper(mod)
    helper.delete("checks/id")
    assert fetch.call_args.kwargs["data"] is None


@pytest.mark.parametrize("no_headers", [False, True])
@patch(PATH + ".fetch_url", side_effect=lambda *args, **kwargs: fetch_success())
def test_helper_head_headers(fetch, no_headers):
    helper = HealthchecksioHelper(module())
    helper.head("id", data=b"x", no_headers=no_headers)
    kwargs = fetch.call_args.kwargs
    assert kwargs["method"] == "HEAD"
    assert kwargs["data"] == b"x"
    assert ("headers" not in kwargs) is no_headers


def test_argument_spec():
    spec = HealthchecksioHelper.healthchecksio_argument_spec()
    assert spec["state"]["choices"] == ["present", "absent"]
    assert spec["management_api_token"]["no_log"] is True
    assert (
        spec["management_api_base_url"]["default"] == "https://healthchecks.io/api/v1"
    )
    assert spec["ping_api_base_url"]["default"] == "https://hc-ping.com"
    assert spec["validate_certs"]["default"] is True
    assert spec["request_timeout"]["default"] == 30


@pytest.mark.parametrize(
    "ping_token,expected", [("ping", "ping"), ("", "token"), (None, None)]
)
def test_ping_helper_settings(ping_token, expected):
    helper = HealthchecksioPingHelper.__new__(HealthchecksioPingHelper)
    mod = module(ping_api_token=ping_token)
    assert helper._get_api_token(mod) == expected
    assert helper._get_base_url(mod) == "https://hc-ping.com"


@pytest.mark.parametrize(
    "cls,endpoint", [(BadgesInfo, "badges"), (ChannelsInfo, "channels")]
)
def test_simple_info_success(cls, endpoint):
    obj = service(cls)
    obj.rest.get.return_value = response(data={"items": [1]})
    with pytest.raises(ExitJson) as exc:
        obj.get()
    obj.rest.get.assert_called_once_with(endpoint)
    assert result_kwargs(obj.module) == {"changed": False, "data": {"items": [1]}}


@pytest.mark.parametrize(
    "cls,endpoint", [(BadgesInfo, "badges"), (ChannelsInfo, "channels")]
)
@pytest.mark.parametrize(
    "data,text", [({"message": "denied"}, "denied"), ({}, "(empty error message)")]
)
def test_simple_info_failure(cls, endpoint, data, text):
    obj = service(cls)
    obj.rest.get.return_value = response(403, data)
    with pytest.raises(FailJson) as exc:
        obj.get()
    assert endpoint in result_kwargs(obj.module)["msg"]
    assert text in result_kwargs(obj.module)["msg"]


@pytest.mark.parametrize(
    "cls,suffix", [(ChecksFlipsInfo, "flips"), (ChecksPingsInfo, "pings")]
)
@pytest.mark.parametrize("status,exception", [(200, ExitJson), (500, FailJson)])
def test_check_events(cls, suffix, status, exception):
    obj = service(cls, module(uuid="abc"))
    obj.rest.get.return_value = response(status, {"message": "down"})
    with pytest.raises(exception) as exc:
        obj.get()
    obj.rest.get.assert_called_once_with("checks/abc/" + suffix)
    if status == 200:
        assert result_kwargs(obj.module)["data"] == {"message": "down"}
    elif cls is ChecksPingsInfo:
        assert "down" in result_kwargs(obj.module)["msg"]


@pytest.mark.parametrize(
    "params,endpoint",
    [
        ({}, "checks"),
        ({"tags": []}, "checks"),
        ({"tags": ["prod", "web"]}, "checks?tag=prod&tag=web"),
        ({"uuid": "abc"}, "checks/abc"),
        ({"name": "nightly job"}, "checks?name=nightly%20job"),
        ({"tags": ["prod"], "name": "a/b"}, "checks?tag=prod&name=a%2Fb"),
    ],
)
def test_checks_info_endpoints(params, endpoint):
    obj = service(ChecksInfo, module(**params))
    obj.rest.get.return_value = response(data={"checks": []})
    with pytest.raises(ExitJson):
        obj.get()
    obj.rest.get.assert_called_once_with(endpoint)


def test_checks_info_failure():
    obj = service(ChecksInfo, module(tags=["prod"]))
    obj.rest.get.return_value = response(500)
    with pytest.raises(FailJson) as exc:
        obj.get()
    assert "checks?tag=prod" in result_kwargs(obj.module)["msg"]


@pytest.mark.parametrize(
    "data,expected",
    [
        ({"ping_url": "https://hc-ping.com/abc"}, "abc"),
        ({"ping_url": "https://hc-ping.com/"}, "(unable to determine uuid)"),
        ({}, "(unable to determine uuid)"),
    ],
)
def test_get_uuid(data, expected):
    assert service(Checks).get_uuid(data) == expected


def check_params(**overrides):
    result = dict(
        name="nightly",
        slug="nightly",
        timeout=60,
        schedule=None,
        tz=None,
        grace=3600,
        channels="email,slack",
        tags=["prod", "web"],
        unique=["name"],
        desc=None,
        uuid=None,
        state="present",
        validate_certs=True,
        request_timeout=30,
        management_api_token="token",
        management_api_base_url="https://healthchecks.io/api/v1",
        ping_api_token=None,
        ping_api_base_url="https://hc-ping.com",
    )
    result.update(overrides)
    return result


def existing(**overrides):
    result = dict(
        name="nightly",
        slug="nightly",
        timeout=60,
        schedule=None,
        tz=None,
        channels="email,slack",
        tags="prod web",
        ping_url="https://hc-ping.com/abc",
    )
    result.update(overrides)
    return result


def checks(**overrides):
    return service(Checks, module(**check_params(**overrides)))


def request_params(obj):
    result = dict(obj.module.params)
    for key in ("uuid", "state", "validate_certs", "request_timeout"):
        result.pop(key, None)
    if result.get("schedule") and result.get("tz"):
        result.pop("timeout")
    if result.get("timeout"):
        result.pop("schedule")
        result.pop("tz")
    result["tags"] = " ".join(obj.module.params.get("tags", []))
    return result


def test_find_existing_match():
    obj = checks()
    found = existing()
    obj.rest.get.return_value = response(data={"checks": [found]})
    assert obj._find_existing_check(request_params(obj)) == found


@pytest.mark.parametrize(
    "change", [{"slug": "other"}, {"channels": "other"}, {"tags": "other"}]
)
def test_find_existing_rejects_difference(change):
    obj = checks()
    obj.rest.get.return_value = response(data={"checks": [existing(**change)]})
    assert obj._find_existing_check(request_params(obj)) is None


def test_find_existing_channel_order():
    obj = checks()
    found = existing(channels="slack,email")
    obj.rest.get.return_value = response(data={"checks": [found]})
    assert obj._find_existing_check(request_params(obj)) == found


def test_find_existing_resolves_all_channels():
    obj = checks(channels="*")
    found = existing()
    obj.rest.get.side_effect = [
        response(data={"checks": [found]}),
        response(data={"channels": [{"id": "email"}, {"id": "slack"}]}),
    ]
    assert obj._find_existing_check(request_params(obj)) == found


def test_find_existing_ambiguous_unique_fails():
    obj = checks()
    obj.rest.get.return_value = response(data={"checks": [existing(), existing()]})
    with pytest.raises(FailJson) as exc:
        obj._find_existing_check(request_params(obj))
    assert "2 found" in result_kwargs(obj.module)["msg"]


def test_find_existing_empty_unique_allows_multiple():
    obj = checks(unique=[])
    obj.rest.get.return_value = response(data={"checks": [existing(), existing()]})
    assert obj._find_existing_check(request_params(obj)) is None


@pytest.mark.parametrize("found,changed", [(existing(), False), (None, True)])
def test_create_check_mode(found, changed):
    obj = checks()
    obj.module.check_mode = True
    obj._find_existing_check = MagicMock(return_value=found)
    with pytest.raises(ExitJson) as exc:
        obj.create()
    assert result_kwargs(obj.module)["changed"] is changed
    assert result_kwargs(obj.module)["uuid"] == ("abc" if found else "")
    obj.rest.post.assert_not_called()


def test_create_idempotent():
    obj = checks()
    obj._find_existing_check = MagicMock(return_value=existing())
    with pytest.raises(ExitJson) as exc:
        obj.create()
    assert result_kwargs(obj.module)["changed"] is False
    obj.rest.post.assert_not_called()


def test_create_idempotent_with_all_channels():
    obj = checks(channels="*")
    obj._find_existing_check = MagicMock(return_value=existing())
    obj.rest.get.return_value = response(
        data={"channels": [{"id": "email"}, {"id": "slack"}]}
    )
    with pytest.raises(ExitJson) as exc:
        obj.create()
    assert result_kwargs(obj.module)["changed"] is False


def test_create_simple_payload():
    obj = checks()
    obj._find_existing_check = MagicMock(return_value=None)
    obj.rest.post.return_value = response(201, existing())
    with pytest.raises(ExitJson) as exc:
        obj.create()
    payload = obj.rest.post.call_args.kwargs["data"]
    assert payload["tags"] == "prod web"
    assert payload["timeout"] == 60
    for key in ("schedule", "tz", "uuid", "state", "validate_certs", "request_timeout"):
        assert key not in payload
    assert result_kwargs(obj.module)["msg"] == "New check abc created"


def test_create_cron_payload():
    obj = checks(timeout=None, schedule="0 1 * * *", tz="UTC")
    obj._find_existing_check = MagicMock(return_value=None)
    obj.rest.post.return_value = response(201, existing())
    with pytest.raises(ExitJson):
        obj.create()
    payload = obj.rest.post.call_args.kwargs["data"]
    assert payload["schedule"] == "0 1 * * *"
    assert "timeout" not in payload


def test_create_updates_changed_check():
    obj = checks(slug="new")
    obj._find_existing_check = MagicMock(return_value=existing())
    obj.rest.post.return_value = response(200, existing(slug="new"))
    with pytest.raises(ExitJson) as exc:
        obj.create()
    assert result_kwargs(obj.module)["changed"] is True
    assert "found and updated" in result_kwargs(obj.module)["msg"]


@pytest.mark.parametrize(
    "data,text", [({"error": "invalid"}, "invalid"), ({}, "(empty error message)")]
)
def test_create_failure(data, text):
    obj = checks()
    obj._find_existing_check = MagicMock(return_value=None)
    obj.rest.post.return_value = response(422, data)
    with pytest.raises(FailJson) as exc:
        obj.create()
    assert text in result_kwargs(obj.module)["msg"]


@pytest.mark.parametrize(
    "operation,http_method", [("delete", "delete"), ("pause", "post")]
)
def test_destructive_check_mode(operation, http_method):
    obj = checks(uuid="abc")
    obj.module.check_mode = True
    with pytest.raises(ExitJson) as exc:
        getattr(obj, operation)()
    assert result_kwargs(obj.module)["changed"] is True
    getattr(obj.rest, http_method).assert_not_called()


@pytest.mark.parametrize(
    "operation,http_method,suffix",
    [("delete", "delete", ""), ("pause", "post", "/pause")],
)
@pytest.mark.parametrize(
    "status,changed,text,exception",
    [
        (200, True, "successfully", ExitJson),
        (404, False, "not found", ExitJson),
        (500, False, "Failed", FailJson),
    ],
)
def test_destructive_results(
    operation, http_method, suffix, status, changed, text, exception
):
    obj = checks(uuid="abc")
    getattr(obj.rest, http_method).return_value = response(status)
    with pytest.raises(exception) as exc:
        getattr(obj, operation)()
    getattr(obj.rest, http_method).assert_called_once_with("checks/abc" + suffix)
    assert result_kwargs(obj.module)["changed"] is changed
    assert text in result_kwargs(obj.module)["msg"]
