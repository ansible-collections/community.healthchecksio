from __future__ import absolute_import, division, print_function

__metaclass__ = type

from http import HTTPStatus

from mock import patch, MagicMock

from ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio import (
    HealthchecksioHelper,
    ChecksInfo,
)

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
    def test_healthchecksio(self):
        assert True


class ResourceTests:

    @staticmethod
    def _setupModule(module_params={}, check_mode=False):
        mockModule = MagicMock()
        mockModule.params = module_params
        mockModule.check_mode = check_mode

        mockModule.fail_json.side_effect = AnsibleFailJson
        mockModule.exit_json.side_effect = AnsibleExitJson

        return mockModule

    @staticmethod
    def _setupHelper(response_json={}, status_code=HTTPStatus.OK):
        mock = MagicMock()
        mock.get.return_value.json = response_json
        mock.get.return_value.status_code = status_code
        return mock


class TestChecksInfo(ResourceTests):

    def test_get_whenErrorStatus(self):
        # Setup
        module_params = {
            'test_param': 'param_value'
        }
        response_json = {
            'test': 'value'
        }

        module = self._setupModule(module_params)
        helper = self._setupHelper(response_json, status_code=HTTPStatus.BAD_REQUEST)

        assert helper.get().status_code == 400

        resource = ChecksInfo(module)
        resource.rest = helper

        # Run
        try:
            result = resource.get()
        except AnsibleFailJson:
            pass

        # Assertions
        helper.get.assert_called_with('checks')
        module.fail_json.assert_called_once_with(changed=False, msg="Failed to get checks [HTTP 400]")
        module.exit_json.assert_not_called()

    def test_get_whenSuccessful(self):
        # Setup
        module_params = {
            'test_param': 'param_value'
        }
        response_json = {
            'test': 'value'
        }

        module = self._setupModule(module_params)
        helper = self._setupHelper(response_json)

        resource = ChecksInfo(module)
        resource.rest = helper

        # Run
        try:
            result = resource.get()
        except AnsibleExitJson:
            pass

        # Assertions
        helper.get.assert_called_with('checks')
        module.exit_json.assert_called_once_with(changed=False, data=response_json)
        module.fail_json.assert_not_called()

    def test_get_whenCheckMode(self):
        # Setup
        module = self._setupModule(check_mode=True)
        helper = self._setupHelper()

        resource = ChecksInfo(module)
        resource.rest = helper

        # Run
        try:
            result = resource.get()
        except AnsibleExitJson:
            pass

        # Assertions
        helper.get.assert_not_called()
        module.exit_json.assert_called_once_with(changed=False, data={})
        module.fail_json.assert_not_called()
