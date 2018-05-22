
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
           1) Add synchronizers/new_base to sys.path
           2) Import xosconfig.Config and set it up to test_config.yaml in the current dir
           3) Build the mock modelaccessor and import it
           4) Import all model accessor classes into global space

        Arguments:
            test_path - path to the test case that is being run
            globals_dict - a dictionary to add global models to
            models - a list of pairs (service_name, xproto_name,
            config_fn - filename of config file)

        Returns:
            Dictionary containing the following:
                sys_path_save: the original sys.path
                model_accessor: model accessor class
                Config: the Config object
                xos_dir: xos directory
                services_dir: services directory
    """
    def get_models_fn(services_dir, service_name, xproto_name):
        name = os.path.join(service_name, "xos", xproto_name)
        if os.path.exists(os.path.join(services_dir, name)):
            return name
        else:
            name = os.path.join(service_name, "xos", "synchronizer", "models", xproto_name)
            if os.path.exists(os.path.join(services_dir, name)):
                return name
        raise Exception("Unable to find service=%s xproto=%s" % (service_name, xproto_name))

    sys_path_save = sys.path

    xos_dir = os.path.join(test_path, "../../..")
    if not os.path.exists(os.path.join(test_path, "new_base")):
        xos_dir = os.path.join(test_path, "../../../../../../orchestration/xos/xos")
        services_dir = os.path.join(xos_dir, "../../xos_services")
    sys.path.append(xos_dir)
    sys.path.append(os.path.join(xos_dir, 'synchronizers', 'new_base'))

    # Setting up the config module
    from xosconfig import Config
    config = os.path.join(test_path, config_fn)
    Config.clear()
    Config.init(config, "synchronizer-config-schema.yaml")

    xprotos = []
    for (service_name, xproto_name) in models:
        xprotos.append(get_models_fn(services_dir, service_name, xproto_name))

    from synchronizers.new_base.mock_modelaccessor_build import build_mock_modelaccessor
    build_mock_modelaccessor(xos_dir, services_dir, xprotos)
    import synchronizers.new_base.modelaccessor
    from synchronizers.new_base.modelaccessor import model_accessor
    from mock_modelaccessor import MockObjectList

    # import all class names to globals
    for (k, v) in model_accessor.all_model_classes.items():
        globals_dict[k] = v

    return {"sys_path_save": sys_path_save,
            "model_accessor": model_accessor,
            "Config": Config,
            "xos_dir": xos_dir,
            "services_dir": services_dir,
            "MockObjectList": MockObjectList}
