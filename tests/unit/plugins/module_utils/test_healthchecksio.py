from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.community.general.tests.unit.compat import unittest
from ansible_collections.community.general.tests.unit.compat.mock import MagicMock

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    Response,
)


class TestResponseObject(unittest.TestCase):
    def test_reads_repoonse_body(self):
        resp = MagicMock()
        resp.read = MagicMock()
        resp.read.return_value = '{"foo":"bar"}'
        info = {}
        Response(resp, info)
        self.assertEquals(resp.read.call_count, 1)

    def test_json_decodes(self):
        resp = MagicMock()
        resp.read = MagicMock()
        resp.read.return_value = '{"foo":"bar"}'
        info = {}
        r = Response(resp, info)
        j = r.json
        self.assertEquals(j, {"foo": "bar"})

    def test_json_returns_None_for_bad_json_response(self):
        resp = MagicMock()
        resp.read = MagicMock()
        resp.read.return_value = "{"
        info = MagicMock()
        r = Response(resp, info)
        j = r.json
        self.assertIsNone(j)

    def test_json_returns_empty_dict_for_body_decode_error(self):
        info = {"body": "{"}
        r = Response(None, info)
        j = r.json
        self.assertEquals(j, {})

    def test_json_returns_json_for_body_in_info(self):
        info = {"body": '{"bar":"baz"}'}
        r = Response(None, info)
        j = r.json
        self.assertEquals(j, {"bar": "baz"})

    def test_json_returns_none_if_no_body_in_info(self):
        info = {}
        r = Response(None, info)
        j = r.json
        self.assertIsNone(j, None)

    def test_status_code(self):
        info = {"status": 404}
        r = Response(None, info)
        status = r.status_code
        self.assertEquals(status, 404)
