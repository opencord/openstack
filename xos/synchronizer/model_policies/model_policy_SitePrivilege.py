
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

class SitePrivilegePolicy(Policy):
    model_name = "SitePrivilege"

    def handle_create(self, site_privilege):
        return self.handle_update(site_privilege)

    def handle_update(self, site_privilege):
        # site_privilege = SitePrivilege.get(site_privilege_id)
        # apply site privilage at all controllers
        controller_site_privileges = ControllerSitePrivilege.objects.filter(
            site_privilege_id = site_privilege.id,
            )
        existing_controllers = [sp.controller for sp in controller_site_privileges]
        all_controllers = Controller.objects.all()
        for controller in all_controllers:
            if controller not in existing_controllers:
                ctrl_site_priv = ControllerSitePrivilege(controller=controller, site_privilege=site_privilege)
                ctrl_site_priv.save()

