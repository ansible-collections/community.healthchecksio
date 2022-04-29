from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from http import HTTPStatus
from mock import patch, MagicMock

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    BadgesInfo,
    ChannelsInfo,
    ChecksFlipsInfo,
    ChecksInfo,
    ChecksPingsInfo,
    Checks,
    Ping,
)


@pytest.fixture(params=[
    '00000000-0000-0000-0000-000000000000',
    'dfa582de-caa3-447f-9d02-7c481c80408c',
])
def uuid(request):
    return request.param


class AnsibleExitJson(Exception):
    """
    Exception class to be raised by module.exit_json and caught by the test case

    This prevents the method continuing when it would usually exit
    """
    pass


class AnsibleFailJson(Exception):
    """
    Exception class to be raised by module.fail_json and caught by the test case

    This prevents the method continuing when it would usually exit
    """
    pass


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
        self._module = MagicMock()
        self._module.fail_json.side_effect = AnsibleFailJson
        self._module.exit_json.side_effect = AnsibleExitJson
        self._setupModule()

        # Patch the helper to avoid an auth error
        with patch('ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.HealthchecksioHelper') as mockHelper:
            self._hcHelper = mockHelper
            self._resource = self.resource_class(self._module)
            self._resource.rest = self._hcHelper

        self._hcHelper.reset_mock()
        self._setupHelper()

    def _setupModule(self, module_params=None, check_mode=False):
        module_params = module_params if module_params else {}

        self._module.params = module_params
        self._module.check_mode = check_mode

    def _setupHelper(self, response_json=None, status_code=HTTPStatus.OK):
        response_json = response_json if response_json else {}

        self._hcHelper.get.return_value.json = response_json
        self._hcHelper.get.return_value.status_code = status_code
        self._hcHelper.head.return_value.json = response_json
        self._hcHelper.head.return_value.status_code = status_code

    def _assertModuleFail(self, expected_msg):
        self._module.fail_json.assert_called_once_with(changed=False, msg=expected_msg)
        self._module.exit_json.assert_not_called()

    def _assertModuleExit(self, expected_data=None, expected_changed=False):
        expected_data = expected_data if expected_data else {}

        self._module.exit_json.assert_called_once_with(changed=expected_changed, data=expected_data)
        self._module.fail_json.assert_not_called()

    def _assertModuleExitMsg(self, expected_msg, expected_changed=False):
        self._module.exit_json.assert_called_once_with(changed=expected_changed, msg=expected_msg)
        self._module.fail_json.assert_not_called()


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
        try:
            result = self._resource.get()
        except AnsibleFailJson:
            pass

        # Assertions
        self._hcHelper.get.assert_called_with(self.expected_url)
        self._assertModuleFail("Failed to get {0} [HTTP 400: (empty error message)]".format(self.expected_url))

    def test_get_whenSuccessful(self):
        # Setup
        response_json = {
            'test': 'value'
        }
        self._setupHelper(response_json)

        # Run
        try:
            result = self._resource.get()
        except AnsibleExitJson:
            pass

        # Assertions
        self._hcHelper.get.assert_called_with(self.expected_url)
        self._assertModuleExit(response_json)

    def test_get_whenCheckMode(self):
        # Setup
        self._setupModule(check_mode=True)

        # Run
        try:
            result = self._resource.get()
        except AnsibleExitJson:
            pass

        # Assertions
        self._hcHelper.get.assert_not_called()
        self._assertModuleExit()


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
        self._setupModule({'uuid': uuid})

        # Run
        try:
            result = self._resource.get()
        except AnsibleFailJson:
            pass

        # Assertions
        expected_url = self._get_expected_url(uuid)
        self._hcHelper.get.assert_called_with(expected_url)
        self._assertModuleFail("Failed to get {0} [HTTP 400: (empty error message)]".format(expected_url))

    def test_get_whenSuccessful(self, uuid):
        # Setup
        response_json = {
            'test': 'value'
        }
        self._setupHelper(response_json)
        self._setupModule({'uuid': uuid})

        # Run
        try:
            result = self._resource.get()
        except AnsibleExitJson:
            pass

        # Assertions
        self._hcHelper.get.assert_called_with(self._get_expected_url(uuid))
        self._assertModuleExit(response_json)

    def test_get_whenCheckMode(self):
        # Setup
        self._setupModule(check_mode=True)

        # Run
        try:
            result = self._resource.get()
        except AnsibleExitJson:
            pass

        # Assertions
        self._hcHelper.get.assert_not_called()
        self._assertModuleExit()


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
        try:
            result = self._resource.get()
        except AnsibleFailJson:
            pass

        # Assertions
        self._hcHelper.get.assert_called_with('checks')
        self._assertModuleFail("Failed to get checks [HTTP 400]")

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
        self._setupModule({
            'tags': tags,
            'uuid': uuid
        })

        response_json = {
            'test': 'value'
        }
        self._setupHelper(response_json)

        # Run
        try:
            result = self._resource.get()
        except AnsibleExitJson:
            pass

        # Assertions
        self._hcHelper.get.assert_called_with(expected_url)
        self._assertModuleExit(response_json)

    def test_get_whenCheckMode(self):
        # Setup
        self._setupModule(check_mode=True)

        # Run
        try:
            result = self._resource.get()
        except AnsibleExitJson:
            pass

        # Assertions
        self._hcHelper.get.assert_not_called()
        self._assertModuleExit()

    def test_get_whenTagsAndUuidPresent(self):
        # Setup
        self._setupModule({
            'tags': ['a'],
            'uuid': '12345'
        })

        # Run
        try:
            result = self._resource.get()
        except AnsibleFailJson:
            pass

        # Assertions
        self._hcHelper.get.assert_not_called()
        self._assertModuleFail("tags and uuid arguments are mutually exclusive and cannot both be provided.")


class TestCheck(ResourceTests):

    @property
    def resource_class(self):
        return Checks

    def _setupModule(self, module_params=None, check_mode=False):
        super()._setupModule(module_params, check_mode)

        if not self._module.params.get('api_token'):
            self._module.params['api_token'] = 'test_token'

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


class TestPing(ResourceTests):

    @property
    def resource_class(self):
        return Ping

    @pytest.fixture(params=['success', 'fail', 'start'])
    def signal(self, request):
        return request.param

    def _setupModule(self, module_params=None, check_mode=False):
        super()._setupModule(module_params, check_mode)

        if not self._module.params.get('api_token'):
            self._module.params['api_token'] = 'test_token'

    def test_create_whenSuccess(self, uuid, signal):
        # Setup
        expected_url = uuid if signal == 'success' else "{0}/{1}".format(uuid, signal)

        # Run
        try:
            result = self._resource.create(uuid, signal)
        except AnsibleExitJson:
            pass

        # Assertions
        self._hcHelper.head.assert_called_with(expected_url)
        self._assertModuleExitMsg('Sent {0} signal to {1}'.format(signal, expected_url), expected_changed=True)

    def test_create_whenErrorStatus(self, uuid, signal):
        # Setup
        expected_url = uuid if signal == 'success' else "{0}/{1}".format(uuid, signal)
        self._setupHelper(status_code=HTTPStatus.BAD_REQUEST)

        # Run
        try:
            result = self._resource.create(uuid, signal)
        except AnsibleFailJson:
            pass

        # Assertions
        self._hcHelper.head.assert_called_with(expected_url)
        self._assertModuleFail('Failed to send {0} signal to {1} [HTTP 400]'.format(signal, expected_url))

    def test_create_whenCheckMode(self):
        # Setup
        self._setupModule(check_mode=True)

        # Run
        try:
            result = self._resource.create('test', 'success')
        except AnsibleExitJson:
            pass

        # Assertions
        self._hcHelper.head.assert_not_called()
        self._assertModuleExit()
