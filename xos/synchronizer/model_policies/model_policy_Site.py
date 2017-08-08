
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

class SitePolicy(Policy):
    model_name = "Site"

    def handle_create(self, site):
        return self.handle_update(site)

    def handle_update(self, site):
        # site = Site.get(site_id)
        # make sure site has a ControllerSite record for each controller
        ctrl_sites = ControllerSite.objects.filter(site_id=site.id)
        existing_controllers = [cs.controller for cs in ctrl_sites]
        existing_controller_ids = [c.id for c in existing_controllers]

        all_controllers = Controller.objects.all()
        for ctrl in all_controllers:
            if ctrl.id not in existing_controller_ids:
                ctrl_site = ControllerSite(controller=ctrl, site=site)
                ctrl_site.save()

