# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from urllib.parse import urljoin


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
                except json.decoder.JSONDecodeError:
                    return {}
            return None
        try:
            return json.loads(to_text(self.body))
        except ValueError:
            return None

    @property
    def status_code(self):
        return self.info["status"]


class HealthchecksioHelper:
    def __init__(self, module):
        self.module = module
        api_base_url = module.params.get("api_base_url")
        if api_base_url == self.healthchecksio_argument_spec().get("api_base_url").get("default"):
            self.ping_api_base_url = "https://hc-ping.com"
        else:
            self.ping_api_base_url = urljoin(api_base_url, "/ping")
        self.baseurl = urljoin(api_base_url, "/api/v1")
        self.timeout = module.params.get("timeout", 30)
        self.api_token = module.params.get("api_token")
        self.headers = {"X-Api-Key": self.api_token}

        response = self.get("checks")
        if response.status_code == 401:
            self.module.fail_json(msg="Failed to login using API token")

    def _url_builder(self, path):
        if path[0] == "/":
            path = path[1:]
        return "%s/%s" % (self.baseurl, path)

    def send(self, method, path, data=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)

        if method == "DELETE":
            if data == "null":
                data = None

        resp, info = fetch_url(
            self.module,
            url,
            data=data,
            headers=self.headers,
            method=method,
            timeout=self.timeout,
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

    def head(self, path, data=None):
        resp, info = fetch_url(
            self.module,
            "{0}/{1}".format(self.ping_api_base_url, path),
            data=data,
            headers=self.headers,
            method="HEAD",
            timeout=self.timeout,
        )
        return Response(resp, info)

    @staticmethod
    def healthchecksio_argument_spec():
        return dict(
            state=dict(type="str", choices=["present", "absent"], default="present"),
            api_token=dict(
                type="str",
                aliases=["api_key"],
                fallback=(
                    env_fallback,
                    [
                        "HEALTHCHECKSIO_API_TOKEN",
                        "HEALTHCHECKSIO_API_KEY",
                        "HC_API_TOKEN",
                        "HC_API_KEY",
                    ],
                ),
                required=True,
                no_log=True,
            ),
            api_base_url=dict(
                type="str",
                fallback=(
                    env_fallback,
                    [
                        "HEALTHCHECKSIO_API_BASE_URL",
                        "HC_API_BASE_URL"
                    ],
                ),
                required=False,
                no_log=True,
                default="https://healthchecks.io"
            ),
        )


class BadgesInfo(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)

    def get(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

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
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

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
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        uuid = self.module.params.get("uuid", None)
        endpoint = "checks/{0}/flips".format(uuid)

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
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        endpoint = "checks"

        tags = self.module.params.get("tags", None)
        if tags is not None:
            tags = ["tag=" + tag for tag in tags]
            tags = "&".join(tags)
            if tags:
                endpoint += "?" + tags

        uuid = self.module.params.get("uuid", None)
        if uuid is not None:
            endpoint += "/" + uuid

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
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

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


class Checks(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)
        self.api_token = module.params.pop("api_token")

    def get_uuid(self, json_data):
        ping_url = json_data.get("ping_url", None)
        if ping_url is not None:
            uuid = ping_url.split("/")[-1]
            if len(uuid) > 0:
                return uuid
            else:
                return "(unable to determine uuid)"
        else:
            return "(unable to determine uuid)"

    def create(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        endpoint = "checks/"

        request_params = dict(self.module.params)

        # uuid is not used to create or update, pop it
        del request_params["uuid"]

        # if schedule and tz, create a Cron check
        if request_params.get("schedule") and request_params.get("tz"):
            del request_params["timeout"]

        # if timeout, create a Simple check
        if request_params.get("timeout"):
            del request_params["schedule"]
            del request_params["tz"]

        tags = self.module.params.get("tags", [])
        request_params["tags"] = " ".join(tags)

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
                msg="Failed to create or update delete check [HTTP {0}: {1}]".format(
                    status_code, json_data.get("error", "(empty error message)")
                ),
            )

        self.module.exit_json(changed=True, data=json_data)

    def delete(self):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        uuid = self.module.params.get("uuid")
        endpoint = "checks/{0}".format(uuid)
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
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        uuid = self.module.params.get("uuid")
        endpoint = "checks/{0}/pause".format(uuid)
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
                msg="Failed delete check {0} [HTTP {1}]".format(uuid, status_code),
            )


class Ping(object):
    def __init__(self, module):
        self.module = module
        self.rest = HealthchecksioHelper(module)
        self.api_token = module.params.pop("api_token")

    def create(self, uuid, signal):
        if self.module.check_mode:
            self.module.exit_json(changed=False, data={})

        if signal == "success":
            endpoint = "{0}".format(uuid)
        else:
            endpoint = "{0}/{1}".format(uuid, signal)

        response = self.rest.head(endpoint)
        status_code = response.status_code

        if status_code == 200:
            self.module.exit_json(
                changed=True, msg="Sent {0} signal to {1}".format(signal, endpoint)
            )

        else:
            self.module.fail_json(
                changed=False,
                msg="Failed to send {0} signal to {1} [HTTP {2}]".format(
                    signal, endpoint, status_code
                ),
            )
