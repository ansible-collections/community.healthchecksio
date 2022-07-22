
from mock import MagicMock
from contextlib import contextmanager


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


class AnsibleModuleTester():

    def __init__(self):
        self.mock_module = MagicMock()

        self.mock_module.fail_json.side_effect = AnsibleFailJson
        self.mock_module.exit_json.side_effect = AnsibleExitJson
        self.setupModule()

        self.__isSuccess = None

    @property
    def isSuccess(self):
        return self.__isSuccess

    @property
    def output(self):
        return self.__output

    def setupModule(self, module_params=None, check_mode=False):
        self.mock_module.params = module_params if module_params else {}
        self.mock_module.check_mode = check_mode

    @contextmanager
    def run(self):
        try:
            yield True
            raise Exception('Module completed without calling exit_json or fail_json')
        except AnsibleExitJson as ae:
            self.__isSuccess = True
            self.__output = self.mock_module.exit_json.call_args_list[0].kwargs
        except AnsibleFailJson as af:
            self.__isSuccess = False
            self.__output = self.mock_module.fail_json.call_args_list[0].kwargs

    def assertOutput(self, **kwargs):
        expected_output = kwargs.copy()
        if 'changed' not in expected_output.keys():
            expected_output.update({
                'changed': False
            })
        assert self.output == expected_output
