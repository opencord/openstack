
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

class UserPolicy(Policy):
    model_name = "User"

    def handle_create(self, user):
        return self.handle_update(user)

    def handle_update(self, user):
        controller_users = ControllerUser.objects.filter(user_id=user.id)
        existing_controllers = [cu.controller for cu in controller_users]
        existing_controller_ids = [c.id for c in existing_controllers]
        all_controllers = Controller.objects.all()
        for controller in all_controllers:
            if controller.id not in existing_controller_ids:
                ctrl_user = ControllerUser(controller=controller, user=user)
                ctrl_user.save()

