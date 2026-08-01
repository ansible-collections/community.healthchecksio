from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch


def make_module(**params):
    module = MagicMock()
    module.params = dict(params)
    module.check_mode = False
    module.diff_mode = False
    return module


def run_main(module_under_test, module):
    with patch.object(
        module_under_test, "AnsibleModule", return_value=module
    ) as ansible_module:
        with patch.object(module_under_test, "run") as run:
            module_under_test.main()
    run.assert_called_once_with(module)
    return ansible_module
