
# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

def setup_sync_unit_test(test_path, globals_dict, models, config_fn="test_config.yaml"):
    """ Perform the common steps associated with setting up a synchronizer unit test.
           1) Import xosconfig.Config and set it up to test_config.yaml in the current dir
           2) Build the mock modelaccessor and import it
           3) Import all model accessor classes into global space

        Arguments:
            test_path - path to the test case that is being run
            globals_dict - a dictionary to add global models to
            models - a list of pairs (service_name, xproto_name)
            config_fn - filename of config file)

        Returns:
            Dictionary containing the following:
                sys_path_save: the original sys.path
                model_accessor: model accessor class
                Config: the Config object
                xos_dir: xos directory
                services_dir: services directory
    """
    sys_path_save = sys.path

    # Setting up the config module
    from xosconfig import Config
    config = os.path.join(test_path, config_fn)
    Config.clear()
    Config.init(config, "synchronizer-config-schema.yaml")

    from xossynchronizer.mock_modelaccessor_build import mock_modelaccessor_config
    mock_modelaccessor_config(test_path, models)

    import xossynchronizer.modelaccessor
    reload(xossynchronizer.modelaccessor)  # in case nose2 loaded it in a previous testp

    from xossynchronizer.modelaccessor import model_accessor

    # modelaccessor.py will have ensure mock_modelaccessor is in sys.path
    from mock_modelaccessor import MockObjectList

    # import all class names to globals
    for (k, v) in model_accessor.all_model_classes.items():
        globals_dict[k] = v

    return {"sys_path_save": sys_path_save,
            "model_accessor": model_accessor,
            "Config": Config,
            "MockObjectList": MockObjectList}
