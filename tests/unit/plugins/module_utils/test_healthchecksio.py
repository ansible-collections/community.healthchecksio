from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
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

    @property
    def resourceClass(self):
        raise NotImplementedError('Resource class property not implemented.')

    def setup_method(self):
        self._module = MagicMock()
        self._module.fail_json.side_effect = AnsibleFailJson
        self._module.exit_json.side_effect = AnsibleExitJson
        self._setupModule()

        # Patch the helper to avoid an auth error
        with patch('ansible_collections.community.healthchecksio.plugins.module_utils.healthchecksio.HealthchecksioHelper') as mockHelper:
            self._hcHelper = mockHelper
            self._resource = self.resourceClass(self._module)
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


class TestChecksInfo(ResourceTests):

    @property
    def resourceClass(self):
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
        self._module.fail_json.assert_called_once_with(changed=False, msg="Failed to get checks [HTTP 400]")
        self._module.exit_json.assert_not_called()

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
        self._module.exit_json.assert_called_once_with(changed=False, data=response_json)
        self._module.fail_json.assert_not_called()

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
        self._module.exit_json.assert_called_once_with(changed=False, data={})
        self._module.fail_json.assert_not_called()

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
        self._module.exit_json.assert_not_called()
        self._module.fail_json.assert_called_once_with(changed=False, msg="tags and uuid arguments are mutually exclusive and cannot both be provided.")
