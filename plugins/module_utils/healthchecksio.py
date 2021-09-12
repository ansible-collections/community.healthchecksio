# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback


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
        self.baseurl = "https://healthchecks.io/api/v1"
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
            "https://hc-ping.com/{0}".format(path),
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
        )
