
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


from synchronizers.new_base.modelaccessor import *
from synchronizers.new_base.policy import Policy

class ControllerUserPolicy(Policy):
    model_name = "ControllerUser"

    def handle_create(self, controller_user):
        return self.handle_update(controller_user)

    def handle_update(self, controller_user):
        my_status_code = int(controller_user.backend_code)
        try:
            his_status_code = int(controller_user.user.backend_code)
        except:
            his_status_code = 0
 
        if (my_status_code not in [0,his_status_code]):
            controller_user.user.backend_status = controller_user.backend_status
            controller_user.user.save(update_fields = ['backend_status'])
