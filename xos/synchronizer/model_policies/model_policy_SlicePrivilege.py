
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


from xossynchronizer.modelaccessor import *
from xossynchronizer.model_policies.policy import Policy

class SlicePrivilegePolicy(Policy):
    model_name = "SlicePrivilege"

    def handle_create(self, slice_privilege):
        return self.handle_update(slice_privilege)

    def handle_update(self, slice_privilege):
        # slice_privilege = SlicePrivilege.get(slice_privilege_id)
        # apply slice privilage at all controllers
        controller_slice_privileges = ControllerSlicePrivilege.objects.filter(
            slice_privilege = slice_privilege,
            )
        existing_controllers = [sp.controller for sp in controller_slice_privileges]
        all_controllers = Controller.objects.all()
        for controller in all_controllers:
            if controller not in existing_controllers:
                ctrl_slice_priv = ControllerSlicePrivilege(controller=controller, slice_privilege=slice_privilege)
                ctrl_slice_priv.save()

