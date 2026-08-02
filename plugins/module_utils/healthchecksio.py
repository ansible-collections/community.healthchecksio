# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.module_utils.basic import env_fallback

DEFAULT_REQUEST_TIMEOUT = 30
DEFAULT_PING_SIGNAL = "success"
DEFAULT_PING_METHOD = "HEAD"
DEFAULT_PING_CREATE = False


class Response(object):
    def __init__(self, resp, info):
        self.body = None
        if resp:
            self.body = resp.read()
        self.info = info

    @property
    def json(self):
        if not self.body:
            if "body" in self.info:
                try:
                    json_body = json.loads(to_text(self.info["body"]))
                    return json_body
                except ValueError:
                    return {}
            return None
        try:
            return json.loads(to_text(self.body))
        except ValueError:
            return None

    @property
    def text(self):
        if self.body is not None:
            return to_text(self.body)
        if "body" in self.info:
            return to_text(self.info["body"])
        return None

    @property
    def status_code(self):
        return self.info["status"]


class HealthchecksioHelper:
    def __init__(self, module, authenticate=True):
        self.module = module
        self.base_url = self._get_base_url(module)
        self.api_token = self._get_api_token(module)
        self.request_timeout = module.params.get(
            "request_timeout", DEFAULT_REQUEST_TIMEOUT
        )
        self.headers = {"X-Api-Key": self.api_token} if self.api_token else {}

        if authenticate and self.get("checks").status_code == 401:
            self.module.fail_json(
                msg="Failed to login using API token against {0}".format(self.base_url)
            )

    def _get_api_token(self, module):
        return module.params.get("management_api_token")

    def _get_base_url(self, module):
        return module.params.get("management_api_base_url")

    def _url_builder(self, path):
        if path[0] == "/":
            path = path[1:]
        return "%s/%s" % (self.base_url, path)

    def send(self, method, path, data=None):
        url = self._url_builder(path)
        if data is not None:
            data = self.module.jsonify(data)

        resp, info = fetch_url(
            self.module,
            url,
            data=data,
            headers=self.headers,
            method=method,
            timeout=self.request_timeout,
        )

        return Response(resp, info)

    def get(self, path, data=None):
        return self.send("GET", path, data)

    def put(self, path, data=None):
        return self.send("PUT", path, data)

    def post(self, path, data=None):
        return self.send("POST", path, data)

    def delete(self, path, data=None):
        return self.send("DELETE", path, data)

    @staticmethod
    def healthchecksio_argument_spec():
        return dict(
            state=dict(type="str", choices=["present", "absent"], default="present"),
            management_api_token=dict(
                type="str",
                aliases=[
                    "management_api_key",
                    "api_key",
                ],
                fallback=(
                    env_fallback,
                    [
                        "HEALTHCHECKSIO_API_TOKEN",
                        "HEALTHCHECKSIO_API_KEY",
                        "HC_API_TOKEN",
                        "HC_API_KEY",
                        "HEALTHCHECKSIO_MANAGEMENT_API_KEY",
                        "HC_MANAGEMENT_API_KEY",
                        "HC_MANAGEMENT_KEY",
                    ],
                ),
                required=False,
                no_log=True,
            ),
            management_api_base_url=dict(
                type="str",
                fallback=(
                    env_fallback,
                    [
                        "HEALTHCHECKSIO_API_MANAGEMENT_BASE_URL",
                        "HC_API_MANAGEMENT_BASE_URL",
                    ],
                ),
                required=False,
                no_log=False,
                default="https://healthchecks.io/api/v3",
            ),
            ping_api_base_url=dict(
                type="str",
                fallback=(
                    env_fallback,
                    [
                        "HEALTHCHECKSIO_API_PING_BASE_URL",
                        "HC_API_PING_BASE_URL",
                    ],
                ),
                required=False,
                no_log=False,
                default="https://hc-ping.com",
            ),
            ping_api_token=dict(
                type="str",
                fallback=(
                    env_fallback,
                    [
                        "HEALTHCHECKSIO_API_PING_KEY",
                        "HC_API_PING_KEY",
                    ],
                ),
                required=False,
                no_log=True,
            ),
            validate_certs=dict(type="bool", default=True),
            request_timeout=dict(type="int", default=DEFAULT_REQUEST_TIMEOUT),
        )


class HealthchecksioPingHelper(HealthchecksioHelper):
    def __init__(self, module):
        super(HealthchecksioPingHelper, self).__init__(module, authenticate=False)

    def _get_api_token(self, module):
        return module.params.get("ping_api_token")

    def _get_base_url(self, module):
        return module.params.get("ping_api_base_url")

    def ping(self, method, path, data=None):
        if data is not None:
            data = to_bytes(data)
        headers = {"Content-Type": "text/plain; charset=utf-8"} if data else None
        resp, info = fetch_url(
            self.module,
            self._url_builder(path),
            data=data,
            headers=headers,
            method=method,
            timeout=self.request_timeout,
        )
        return Response(resp, info)


class BadgesInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        endpoint = "badges"

        response = self.rest.get(endpoint)
        json_data = response.json
        status_code = response.status_code

        if status_code != 200:
            self.module.fail_json(
                changed=False,
                msg="Failed to get {0} [HTTP {1}: {2}]".format(
                    endpoint,
                    status_code,
                    json_data.get("message", "(empty error message)"),
                ),
            )

        self.module.exit_json(changed=False, data=json_data)


class ChannelsInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        endpoint = "channels"

        response = self.rest.get(endpoint)
        json_data = response.json
        status_code = response.status_code

        if status_code != 200:
            self.module.fail_json(
                changed=False,
                msg="Failed to get {0} [HTTP {1}: {2}]".format(
                    endpoint,
                    status_code,
                    json_data.get("message", "(empty error message)"),
                ),
            )

        self.module.exit_json(changed=False, data=json_data)


class ChecksFlipsInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        identifier = self.module.params.get("unique_key") or self.module.params.get(
            "uuid"
        )
        endpoint = "checks/{0}/flips".format(identifier)
        query = []
        for name in ("seconds", "start", "end"):
            value = self.module.params.get(name)
            if value is not None:
                query.append("{0}={1}".format(name, value))
        if query:
            endpoint += "?" + "&".join(query)

        response = self.rest.get(endpoint)
        json_data = response.json
        status_code = response.status_code

        if status_code != 200:
            self.module.fail_json(
                changed=False,
                msg="Failed to get {0} [HTTP {1}]".format(endpoint, status_code),
            )

        self.module.exit_json(changed=False, data=json_data)


class ChecksInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        identifier = self.module.params.get("unique_key") or self.module.params.get(
            "uuid"
        )
        endpoint = "checks/{0}".format(identifier) if identifier else "checks"

        if not identifier:
            query = []
            for tag in self.module.params.get("tags") or []:
                query.append("tag=" + quote(tag, safe=""))
            for name in ("slug", "name"):
                value = self.module.params.get(name)
                if value is not None:
                    query.append("{0}={1}".format(name, quote(value, safe="")))
            if query:
                endpoint += "?" + "&".join(query)

        response = self.rest.get(endpoint)
        json_data = response.json
        status_code = response.status_code

        if status_code != 200:
            self.module.fail_json(
                changed=False,
                msg="Failed to get {0} [HTTP {1}]".format(endpoint, status_code),
            )

        self.module.exit_json(changed=False, data=json_data)


class ChecksPingsInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        uuid = self.module.params.get("uuid", None)
        endpoint = "checks/{0}/pings".format(uuid)

        response = self.rest.get(endpoint)
        json_data = response.json
        status_code = response.status_code

        if status_code != 200:
            self.module.fail_json(
                changed=False,
                msg="Failed to get {0} [HTTP {1}: {2}]".format(
                    endpoint,
                    status_code,
                    json_data.get("message", "(empty error message)"),
                ),
            )

        self.module.exit_json(changed=False, data=json_data)


class ChecksPingBodyInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        uuid = self.module.params.get("uuid")
        sequence = self.module.params.get("sequence")
        endpoint = "checks/{0}/pings/{1}/body".format(uuid, sequence)
        response = self.rest.get(endpoint)

        if response.status_code != 200:
            self.module.fail_json(
                changed=False,
                msg="Failed to get {0} [HTTP {1}]".format(
                    endpoint, response.status_code
                ),
            )

        self.module.exit_json(changed=False, data=response.text)


class StatusInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module, authenticate=False)

    def get(self):
        response = self.rest.get("status/")
        if response.status_code != 200:
            self.module.fail_json(
                changed=False,
                msg="Healthchecks.io service status check failed [HTTP {0}]".format(
                    response.status_code
                ),
            )
        self.module.exit_json(changed=False, status="ok")


class Checks(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get_uuid(self, json_data):
        uuid = json_data.get("uuid")
        if uuid:
            return uuid
        ping_url = json_data.get("ping_url", None)
        if ping_url is not None:
            uuid = ping_url.split("/")[-1]
            if len(uuid) > 0:
                return uuid
            else:
                return "(unable to determine uuid)"
        else:
            return "(unable to determine uuid)"

    def _resolve_channels(self, request_params):
        channels_param = request_params.get("channels")
        cache = getattr(self, "_resolved_channels", {})
        if channels_param not in cache:
            if channels_param == "*":
                channels = self.rest.get("channels").json.get("channels", [])
                cache[channels_param] = ",".join(channel["id"] for channel in channels)
            else:
                cache[channels_param] = channels_param
            self._resolved_channels = cache
        return cache[channels_param]

    def _matches(self, check, request_params):
        skip = set(["unique", "channels", "tags"])
        params_match = all(
            check.get(key) == value
            for key, value in request_params.items()
            if key not in skip
        )
        if not params_match:
            return False

        if "channels" in request_params:
            expected = self._resolve_channels(request_params) or ""
            actual = check.get("channels", "")
            if sorted(actual.split(",")) != sorted(expected.split(",")):
                return False

        if "tags" in request_params and check.get("tags", "") != request_params["tags"]:
            return False

        return True

    def _find_existing_check(self, request_params):
        unique = request_params.get("unique", [])
        if not unique:
            return None

        checks = self.rest.get("checks").json["checks"]
        matches = [
            check
            for check in checks
            if all(check.get(key) == request_params.get(key) for key in unique)
        ]

        if len(matches) > 1 and unique:
            self.module.fail_json(
                changed=False,
                msg="Expected to find one check matching unique parameters, {0} found".format(
                    len(matches)
                ),
            )

        if len(matches) == 1 and self._matches(matches[0], request_params):
            return matches[0]
        return None

    def create(self):
        uuid = self.module.params.get("uuid")
        endpoint = "checks/{0}".format(uuid) if uuid else "checks/"

        request_params = dict(self.module.params)

        for key in (
            "uuid",
            "state",
            "api_key",
            "management_api_key",
            "management_api_token",
            "management_api_base_url",
            "ping_api_token",
            "ping_api_base_url",
            "validate_certs",
            "request_timeout",
        ):
            request_params.pop(key, None)
        request_params = dict(
            (key, value) for key, value in request_params.items() if value is not None
        )

        if uuid:
            request_params.pop("unique", None)

        if request_params.get("schedule"):
            request_params.pop("timeout", None)
        elif request_params.get("timeout"):
            request_params.pop("schedule", None)
            request_params.pop("tz", None)

        if "tags" in request_params:
            request_params["tags"] = " ".join(request_params["tags"])

        # Look up existing check for idempotency. UUID selects the explicit
        # update endpoint; otherwise the API's upsert fields identify a check.
        if uuid:
            response = self.rest.get("checks/{0}".format(uuid))
            existing = response.json if response.status_code == 200 else None
            matches = existing is not None and self._matches(existing, request_params)
        else:
            existing = self._find_existing_check(request_params)
            matches = existing is not None
        if self.module.check_mode:
            self.module.exit_json(
                changed=not matches,
                data=existing if matches else {},
                uuid=self.get_uuid(existing) if matches else "",
            )

        if matches:
            self.module.exit_json(
                changed=False,
                data=existing,
                uuid=self.get_uuid(existing),
            )

        response = self.rest.post(endpoint, data=request_params)
        json_data = response.json
        status_code = response.status_code

        if status_code == 200:
            uuid = self.get_uuid(json_data)
            self.module.exit_json(
                changed=True,
                msg="Existing check {0} found and updated".format(uuid),
                data=json_data,
                uuid=uuid,
            )

        elif status_code == 201:
            uuid = self.get_uuid(json_data)
            self.module.exit_json(
                changed=True,
                msg="New check {0} created".format(uuid),
                data=json_data,
                uuid=uuid,
            )

        else:
            self.module.fail_json(
                changed=False,
                msg="Failed to create or update check [HTTP {0}: {1}]".format(
                    status_code, json_data.get("error", "(empty error message)")
                ),
            )

    def delete(self):
        uuid = self.module.params.get("uuid")
        endpoint = "checks/{0}".format(uuid)

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg="Check {0} would be deleted".format(uuid),
                uuid=uuid,
            )

        response = self.rest.delete(endpoint)
        status_code = response.status_code

        if status_code == 200:
            self.module.exit_json(
                changed=True, msg="Check {0} successfully deleted".format(uuid)
            )
        elif status_code == 404:
            self.module.exit_json(changed=False, msg="Check {0} not found".format(uuid))
        else:
            self.module.fail_json(
                changed=False,
                msg="Failed delete check {0} [HTTP {1}]".format(uuid, status_code),
            )

    def pause(self):
        uuid = self.module.params.get("uuid")
        endpoint = "checks/{0}/pause".format(uuid)

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg="Check {0} would be paused".format(uuid),
                uuid=uuid,
            )

        response = self.rest.post(endpoint)
        status_code = response.status_code

        if status_code == 200:
            self.module.exit_json(
                changed=True, msg="Check {0} successfully paused".format(uuid)
            )
        elif status_code == 404:
            self.module.exit_json(changed=False, msg="Check {0} not found".format(uuid))
        else:
            self.module.fail_json(
                changed=False,
                msg="Failed to pause check {0} [HTTP {1}]".format(uuid, status_code),
            )

    def resume(self):
        uuid = self.module.params.get("uuid")
        endpoint = "checks/{0}/resume".format(uuid)

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg="Check {0} would be resumed".format(uuid),
                uuid=uuid,
            )

        response = self.rest.post(endpoint)
        status_code = response.status_code

        if status_code == 200:
            self.module.exit_json(
                changed=True, msg="Check {0} successfully resumed".format(uuid)
            )
        elif status_code == 404:
            self.module.exit_json(changed=False, msg="Check {0} not found".format(uuid))
        elif status_code == 409:
            self.module.exit_json(
                changed=False, msg="Check {0} is not paused".format(uuid)
            )
        else:
            self.module.fail_json(
                changed=False,
                msg="Failed to resume check {0} [HTTP {1}]".format(uuid, status_code),
            )


class Ping(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioPingHelper(module)

    def create(
        self,
        uuid=None,
        signal=DEFAULT_PING_SIGNAL,
        runid=None,
        slug=None,
        body=None,
        method=DEFAULT_PING_METHOD,
        create=DEFAULT_PING_CREATE,
        exit_status=None,
    ):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        target = slug if slug is not None else uuid
        if slug is not None:
            endpoint = "{0}/{1}".format(self.rest.api_token, slug)
        else:
            endpoint = "{0}".format(uuid)

        event = str(exit_status) if exit_status is not None else signal
        if event != "success":
            endpoint = "{0}/{1}".format(endpoint, event)

        query = []
        if runid is not None:
            query.append("rid={0}".format(quote(runid, safe="")))
        if create:
            query.append("create=1")
        request_endpoint = endpoint
        if query:
            request_endpoint = "{0}?{1}".format(endpoint, "&".join(query))

        if body is not None and method == "HEAD":
            method = "POST"
        response = self.rest.ping(method, request_endpoint, data=body)

        if response.status_code in (200, 201):
            self.module.exit_json(
                changed=True, msg="Sent {0} signal to {1}".format(event, target)
            )
        self.module.fail_json(
            changed=False,
            msg="Failed to send {0} signal to {1} [HTTP {2}]".format(
                event, target, response.status_code
            ),
        )
