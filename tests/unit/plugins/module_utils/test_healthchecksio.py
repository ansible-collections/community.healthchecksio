from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from http import HTTPStatus
from mock import patch, MagicMock

from ansible_collections.community.healthchecksio.tests.unit.test_utils import AnsibleModuleTester
from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    BadgesInfo,
    ChannelsInfo,
    ChecksFlipsInfo,
    ChecksInfo,
    ChecksPingsInfo,
    Checks,
    Ping,
    delete_if_exists,
    Response,
)


@pytest.fixture(params=[
    '00000000-0000-0000-0000-000000000000',
    'dfa582de-caa3-447f-9d02-7c481c80408c',
])
def uuid(request):
    return request.param


class TestDeleteIfExists:

    __EXPECTED_DICT = {
        'TEST': 'value'
    }

    @pytest.mark.parametrize("value", ['value', '', None])
    def test_values(self, value):
        test_dict = {
            'TEST': 'value',
            'test': value
        }
        assert test_dict['test'] == value
        delete_if_exists(test_dict, 'test')
        assert test_dict == self.__EXPECTED_DICT

    def test_missing(self):
        test_dict = self.__EXPECTED_DICT.copy()
        delete_if_exists(test_dict, 'test')
        assert test_dict == self.__EXPECTED_DICT


class TestResponseObject:

    def test_reads_repoonse_body(self):
        resp = MagicMock()
        resp.read.return_value = '{"foo":"bar"}'
        info = {}
        Response(resp, info)
        assert resp.read.call_count == 1

    def test_json_decodes(self):
        resp = MagicMock()
        resp.read.return_value = '{"foo":"bar"}'
        info = {}
        r = Response(resp, info)
        j = r.json
        assert j == {"foo": "bar"}

    def test_json_returns_None_for_bad_json_response(self):
        resp = MagicMock()
        resp.read.return_value = "{"
        info = MagicMock()
        r = Response(resp, info)
        j = r.json
        assert j is None

    def test_json_returns_empty_dict_for_body_decode_error(self):
        info = {"body": "{"}
        r = Response(None, info)
        j = r.json
        assert j == {}

    def test_json_returns_json_for_body_in_info(self):
        info = {"body": '{"bar":"baz"}'}
        r = Response(None, info)
        j = r.json
        assert j == {"bar": "baz"}

    def test_json_returns_none_if_no_body_in_info(self):
        info = {}
        r = Response(None, info)
        j = r.json
        assert j is None

    def test_status_code(self):
        info = {"status": 404}
        r = Response(None, info)
        status = r.status_code
        assert status == 404


class TestHealthchecksioModuleUtil:

    @pytest.fixture(params=['get', 'post', 'put', 'delete'])
    def standard_send_method(self, request):
        '''
        Names of methods on HealthchecksIoHelper implementing the standard send functionality
        '''
        return request.param

    @pytest.fixture(params=['', '/', 'test', '/test', '/test/', '/test/test', '/test?test=test'])
    def path(self, request):
        return request.param

    @pytest.fixture(params=['test_token', 'test_token2'])
    def api_token(self, request):
        return request.param

    @pytest.fixture(params=[1, 10, 30, None])
    def timeout(self, request):
        return request.param

    @pytest.fixture(params=[None, {'test': 'value'}])
    def data(self, request):
        return request.param

    @pytest.fixture(params=[HTTPStatus.OK, HTTPStatus.BAD_REQUEST])
    def response_status_code(self, request):
        return request.param

    @staticmethod
    def _setup_response(mock_fetch, mock_response, data, status_code):
        mock_fetch.return_value = (MagicMock(), MagicMock())
        mock_response.return_value.json = data
        mock_response.return_value.status_code = status_code

    def test_standard_send_methods(self, standard_send_method, path, data, api_token, timeout, response_status_code):
        module = MagicMock()
        module.params = {
            "api_token": api_token,
            "timeout": timeout,
        }
        module.jsonify.return_value = 'jsonified_data'

        with patch('ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url') as mock_fetch:
            with patch('ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.Response') as mock_response:
                self._setup_response(mock_fetch, mock_response, data, response_status_code)

                helper = HealthchecksioHelper(module)
                call_method = getattr(helper, standard_send_method)
                response = call_method(path, data)

                assert response.status_code == response_status_code
                assert response.json == data
                mock_fetch.assert_called_with(
                    module,
                    'https://healthchecks.io/api/v1{0}{1}'.format(
                        ('' if path.startswith('/') else '/'),
                        path),
                    data='jsonified_data',
                    headers={'X-Api-Key':api_token},
                    method=standard_send_method.upper(),
                    timeout=timeout)
                module.jsonify.assert_called_with(data)

    def test_head(self, path, data, api_token, timeout, response_status_code):
        module = MagicMock()
        module.params = {
            "api_token": api_token,
            "timeout": timeout,
        }

        with patch('ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.fetch_url') as mock_fetch:
            with patch('ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.Response') as mock_response:
                self._setup_response(mock_fetch, mock_response, data, response_status_code)

                helper = HealthchecksioHelper(module)
                response = helper.head(path, data)

                assert response.status_code == response_status_code
                assert response.json == data
                mock_fetch.assert_called_with(
                    module,
                    'https://hc-ping.com/{0}'.format(path),
                    data=data,
                    headers={'X-Api-Key':api_token},
                    method='HEAD',
                    timeout=timeout)

class ResourceTests:

    @property
    def resource_class(self):
        raise NotImplementedError()

    def setup_method(self):
        self._moduleTester = AnsibleModuleTester()

        # Setup initially with API token defined to prevent error from resource constructor.
        self._moduleTester.setupModule({'api_token': 'test_token'})

        # Patch the helper to avoid an auth error
        with patch('ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.HealthchecksioHelper') as mockHelper:
            self._hcHelper = mockHelper
            self._resource = self.resource_class(self._moduleTester.mock_module)
            self._resource.rest = self._hcHelper

        self._hcHelper.reset_mock()
        self._setupHelper()

    def _setupHelper(self, response_json=None, status_code=HTTPStatus.OK):
        response_json = response_json if response_json else {}

        for method in ['get', 'post', 'put', 'delete', 'head']:
            getattr(self._hcHelper, method).return_value.json = response_json
            getattr(self._hcHelper, method).return_value.status_code = status_code


class SimpleResourceTests(ResourceTests):
    '''
    Base class for testing simple resources which do not have any parameters and passthrough response data.

    Includes 3 tests which are used for all inheriting classes.
    '''

    @property
    def expected_url(self):
        raise NotImplementedError()

    def test_get_whenErrorStatus(self):
        # Setup
        self._setupHelper(status_code=HTTPStatus.BAD_REQUEST)

        # Run
        with self._moduleTester.run():
            self._resource.get()

        # Assertions
        assert not self._moduleTester.isSuccess
        self._moduleTester.assertOutput(msg='Failed to get {0} [HTTP 400: (empty error message)]'.format(self.expected_url))
        self._hcHelper.get.assert_called_with(self.expected_url)

    def test_get_whenSuccessful(self):
        # Setup
        response_json = {
            'test': 'value'
        }
        self._setupHelper(response_json)

        # Run
        with self._moduleTester.run():
            self._resource.get()

        # Assertions
        self._hcHelper.get.assert_called_with(self.expected_url)
        assert self._moduleTester.isSuccess
        self._moduleTester.assertOutput(data=response_json)

    def test_get_whenCheckMode(self):
        # Setup
        self._moduleTester.setupModule(check_mode=True)

        # Run
        with self._moduleTester.run():
            self._resource.get()

        # Assertions
        self._hcHelper.get.assert_not_called()
        assert self._moduleTester.isSuccess


class CheckSubResourceTests(ResourceTests):
    '''
    Base class for testing sub-resources of checks (e.g. pings and flips)
    '''
    @property
    def expected_sub_url(self):
        raise NotImplementedError()

    def _get_expected_url(self, uuid):
        return "checks/{0}/{1}".format(uuid, self.expected_sub_url)

    def test_get_whenErrorStatus(self, uuid):
        # Setup
        self._setupHelper(status_code=HTTPStatus.BAD_REQUEST)
        self._moduleTester.setupModule({'uuid': uuid})

        # Run
        with self._moduleTester.run():
            self._resource.get()

        # Assertions
        expected_url = self._get_expected_url(uuid)
        self._hcHelper.get.assert_called_with(expected_url)
        assert not self._moduleTester.isSuccess
        self._moduleTester.assertOutput(msg="Failed to get {0} [HTTP 400: (empty error message)]".format(expected_url))

    def test_get_whenSuccessful(self, uuid):
        # Setup
        response_json = {
            'test': 'value'
        }
        self._setupHelper(response_json)
        self._moduleTester.setupModule({'uuid': uuid})

        # Run
        with self._moduleTester.run():
            self._resource.get()

        # Assertions
        self._hcHelper.get.assert_called_with(self._get_expected_url(uuid))
        assert self._moduleTester.isSuccess
        self._moduleTester.assertOutput(data=response_json)

    def test_get_whenCheckMode(self):
        # Setup
        self._moduleTester.setupModule(check_mode=True)

        # Run
        with self._moduleTester.run():
            self._resource.get()

        # Assertions
        self._hcHelper.get.assert_not_called()
        assert self._moduleTester.isSuccess


class TestBadgesInfo(SimpleResourceTests):

    @property
    def resource_class(self):
        return BadgesInfo

    @property
    def expected_url(self):
        return 'badges'


class TestChannelsInfo(SimpleResourceTests):

    @property
    def resource_class(self):
        return ChannelsInfo

    @property
    def expected_url(self):
        return 'channels'


class TestChecksFlipsInfo(CheckSubResourceTests):

    @property
    def resource_class(self):
        return ChecksFlipsInfo

    @property
    def expected_sub_url(self):
        return 'flips'


class TestChecksPingsInfo(CheckSubResourceTests):

    @property
    def resource_class(self):
        return ChecksPingsInfo

    @property
    def expected_sub_url(self):
        return 'pings'


class TestChecksInfo(ResourceTests):

    @property
    def resource_class(self):
        return ChecksInfo

    def test_get_whenErrorStatus(self):
        # Setup
        self._setupHelper(status_code=HTTPStatus.BAD_REQUEST)

        # Run
        with self._moduleTester.run():
            self._resource.get()

        # Assertions
        self._hcHelper.get.assert_called_with('checks')
        assert not self._moduleTester.isSuccess
        self._moduleTester.assertOutput(msg="Failed to get checks [HTTP 400]")

    @pytest.mark.parametrize(
        "tags,uuid,expected_url",
        [
            (None, None, 'checks'),
            (['a'], None, 'checks?tag=a'),
            (['a', 'b', 'c'], None, 'checks?tag=a&tag=b&tag=c'),
            (None, '12345', 'checks/12345'),
        ]
    )
    def test_get_whenSuccessful(self, tags, uuid, expected_url):
        # Setup
        self._moduleTester.setupModule({
            'tags': tags,
            'uuid': uuid
        })

        response_json = {
            'test': 'value'
        }
        self._setupHelper(response_json)

        # Run
        with self._moduleTester.run():
            self._resource.get()

        # Assertions
        self._hcHelper.get.assert_called_with(expected_url)
        assert self._moduleTester.isSuccess
        self._moduleTester.assertOutput(data=response_json)

    def test_get_whenCheckMode(self):
        # Setup
        self._moduleTester.setupModule(check_mode=True)

        # Run
        with self._moduleTester.run():
            self._resource.get()

        # Assertions
        self._hcHelper.get.assert_not_called()
        assert self._moduleTester.isSuccess

    def test_get_whenTagsAndUuidPresent(self):
        # Setup
        self._moduleTester.setupModule({
            'tags': ['a'],
            'uuid': '12345'
        })

        # Run
        with self._moduleTester.run():
            self._resource.get()

        # Assertions
        self._hcHelper.get.assert_not_called()
        assert not self._moduleTester.isSuccess
        self._moduleTester.assertOutput(msg="tags and uuid arguments are mutually exclusive and cannot both be provided.")


class TestCheck(ResourceTests):

    @property
    def resource_class(self):
        return Checks

    @pytest.mark.parametrize(
        "ping_url,expected_result",
        [
            # Valid healthchecks.io ping address
            ('http://hc-ping.com/803f680d-e89b-492b-82ef-2be7b774a92d', '803f680d-e89b-492b-82ef-2be7b774a92d'),
            # Valid self-host ping address
            ('http://example.com/ping/803f680d-e89b-492b-82ef-2be7b774a92d', '803f680d-e89b-492b-82ef-2be7b774a92d'),
            # Invalid addresses
            ('http://hc-ping.com/', '(unable to determine uuid)'),
            ('http://example.com/ping/', '(unable to determine uuid)'),
            ('http://example.com/', '(unable to determine uuid)'),
            ('', '(unable to determine uuid)'),
            (None, '(unable to determine uuid)'),
        ]
    )
    def test_get_uuid(self, ping_url, expected_result):
        json_data = {
            'ping_url': ping_url
        }
        result = Checks.get_uuid(json_data)
        assert result == expected_result

    @staticmethod
    def _build_ping_url(uuid):
        return 'https://hc-ping.com/{0}'.format(uuid)

    @pytest.fixture(params=['create', 'delete', 'pause'])
    def method(self, request):
        return request.param

    def test_checkMode(self, method):
        # Setup
        self._moduleTester.setupModule(check_mode=True)

        # Run
        with self._moduleTester.run():
            call_method = getattr(self._resource, method)
            call_method()

        # Assertions
        self._hcHelper.send.assert_not_called()
        assert self._moduleTester.isSuccess

    def _runCreateTest(self, status_code, uuid):
        # Setup
        self._setupHelper(
            status_code=status_code,
            response_json = {
                'ping_url': self._build_ping_url(uuid)
            })

        # Run
        with self._moduleTester.run():
            self._resource.create()

        # Assertions
        expected_url = 'checks/'
        self._hcHelper.post.assert_called_once_with(expected_url, data={})

    def test_create_whenCreated(self, uuid):
        self._runCreateTest(HTTPStatus.CREATED, uuid)
        assert self._moduleTester.isSuccess
        self._moduleTester.assertOutput(
            changed=True,
            msg='New check {0} created'.format(uuid),
            data={
                'ping_url': self._build_ping_url(uuid)
            },
            uuid=uuid)

    def test_create_whenUpdated(self, uuid):
        self._runCreateTest(HTTPStatus.OK, uuid)
        assert self._moduleTester.isSuccess
        self._moduleTester.assertOutput(
            changed=True,
            msg='Existing check {0} found and updated'.format(uuid),
            data={
                'ping_url': self._build_ping_url(uuid)
            },
            uuid=uuid)

    def test_create_whenOtherStatus(self, uuid):
        self._runCreateTest(HTTPStatus.BAD_REQUEST, uuid)
        assert not self._moduleTester.isSuccess
        self._moduleTester.assertOutput(msg='Failed to create or update check [HTTP {0}: (empty error message)]'.format(HTTPStatus.BAD_REQUEST))

    def _runDeleteTest(self, uuid):
        # Setup
        self._moduleTester.setupModule({'uuid': uuid})

        # Run
        with self._moduleTester.run():
            self._resource.delete()

        # Assertions
        expected_url = 'checks/{0}'.format(uuid)
        self._hcHelper.delete.assert_called_once_with(expected_url)

    def test_delete_whenSuccess(self, uuid):
        self._runDeleteTest(uuid)
        assert self._moduleTester.isSuccess
        self._moduleTester.assertOutput(
            msg="Check {0} successfully deleted".format(uuid),
            changed=True)

    def test_delete_whenNotFound(self, uuid):
        self._setupHelper(status_code=HTTPStatus.NOT_FOUND)
        self._runDeleteTest(uuid)
        assert self._moduleTester.isSuccess
        self._moduleTester.assertOutput(msg='Check {0} not found'.format(uuid))

    def test_delete_whenOther(self, uuid):
        self._setupHelper(status_code=HTTPStatus.BAD_REQUEST)
        self._runDeleteTest(uuid)
        assert not self._moduleTester.isSuccess
        self._moduleTester.assertOutput(msg='Failed to delete check {0} [HTTP {1}]'.format(uuid, HTTPStatus.BAD_REQUEST))

    def _runPauseTest(self, uuid):
        # Setup
        self._moduleTester.setupModule({
            'uuid': uuid
        })

        # Run
        with self._moduleTester.run():
            self._resource.pause()

        # Assertions
        expected_url = 'checks/{0}/pause'.format(uuid)
        self._hcHelper.post.assert_called_once_with(expected_url)

    def test_pause_whenSuccess(self, uuid):
        self._runPauseTest(uuid)
        assert self._moduleTester.isSuccess
        self._moduleTester.assertOutput(
            msg="Check {0} successfully paused".format(uuid),
            changed=True)

    def test_pause_whenNotFound(self, uuid):
        self._setupHelper(status_code=HTTPStatus.NOT_FOUND)
        self._runPauseTest(uuid)
        assert not self._moduleTester.isSuccess
        self._moduleTester.assertOutput(msg='Check {0} not found'.format(uuid))

    def test_pause_whenOther(self, uuid):
        self._setupHelper(status_code=HTTPStatus.BAD_REQUEST)
        self._runPauseTest(uuid)
        assert not self._moduleTester.isSuccess
        self._moduleTester.assertOutput(msg='Failed to pause check {0} [HTTP {1}]'.format(uuid, HTTPStatus.BAD_REQUEST))


class TestPing(ResourceTests):

    @property
    def resource_class(self):
        return Ping

    @pytest.fixture(params=['success', 'fail', 'start'])
    def signal(self, request):
        return request.param

    def test_create_whenSuccess(self, uuid, signal):
        # Setup
        expected_url = uuid if signal == 'success' else "{0}/{1}".format(uuid, signal)

        # Run
        with self._moduleTester.run():
            self._resource.create(uuid, signal)

        # Assertions
        self._hcHelper.head.assert_called_with(expected_url)
        assert self._moduleTester.isSuccess
        self._moduleTester.assertOutput(
            msg='Sent {0} signal to {1}'.format(signal, expected_url),
            changed=True)

    def test_create_whenErrorStatus(self, uuid, signal):
        # Setup
        expected_url = uuid if signal == 'success' else "{0}/{1}".format(uuid, signal)
        self._setupHelper(status_code=HTTPStatus.BAD_REQUEST)

        # Run
        with self._moduleTester.run():
            self._resource.create(uuid, signal)

        # Assertions
        self._hcHelper.head.assert_called_with(expected_url)
        assert not self._moduleTester.isSuccess
        self._moduleTester.assertOutput(msg='Failed to send {0} signal to {1} [HTTP 400]'.format(signal, expected_url))

    def test_create_whenCheckMode(self):
        # Setup
        self._moduleTester.setupModule(check_mode=True)

        # Run
        with self._moduleTester.run():
            self._resource.create('test', 'success')

        # Assertions
        self._hcHelper.head.assert_not_called()
        assert self._moduleTester.isSuccess
