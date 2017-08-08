
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


from collections import defaultdict
from synchronizers.new_base.modelaccessor import *
from synchronizers.new_base.policy import Policy

class ControllerPolicy(Policy):
    model_name = "Controller"

    def handle_create(self, controller):
        return self.handle_update(controller)

    def handle_update(self, controller):
        # relations for all sites
        ctrls_by_site = defaultdict(list)
        ctrl_sites = ControllerSite.objects.all()
        for ctrl_site in ctrl_sites:
            ctrls_by_site[ctrl_site.site.id].append(ctrl_site.controller.id)

        sites = Site.objects.all()
        for site in sites:
            if site.id not in ctrls_by_site or controller.id not in ctrls_by_site[site.id]:
                controller_site = ControllerSite(controller=controller, site=site)
                controller_site.save()

        # relations for all slices
        ctrls_by_slice = defaultdict(list)
        ctrl_slices = ControllerSlice.objects.all()
        for ctrl_slice in ctrl_slices:
            ctrls_by_slice[ctrl_slice.slice.id].append(ctrl_slice.controller.id)

        slices = Slice.objects.all()
        for slice in slices:
            if slice.id not in ctrls_by_slice or controller.id not in ctrls_by_slice[slice.id]:
                controller_slice = ControllerSlice(controller=controller, slice=slice)
                controller_slice.save()

        # relations for all users
        ctrls_by_user = defaultdict(list)
        ctrl_users = ControllerUser.objects.all()
        for ctrl_user in ctrl_users:
            ctrls_by_user[ctrl_user.user.id].append(ctrl_user.controller.id)

        users = User.objects.all()
        for user in users:
            if user.id not in ctrls_by_user or controller.id not in ctrls_by_user[user.id]:
                controller_user = ControllerUser(controller=controller, user=user)
                controller_user.save()

        # relations for all networks
        ctrls_by_network = defaultdict(list)
        ctrl_networks = ControllerNetwork.objects.all()
        for ctrl_network in ctrl_networks:
            ctrls_by_network[ctrl_network.network.id].append(ctrl_network.controller.id)

        networks = Network.objects.all()
        for network in networks:
            if network.id not in ctrls_by_network or controller.id not in ctrls_by_network[network.id]:
                controller_network = ControllerNetwork(controller=controller, network=network)
                if network.subnet and network.subnet.strip():
                    controller_network.subnet = network.subnet.strip()
                controller_network.save()

        # relations for all images
        ctrls_by_image = defaultdict(list)
        ctrl_images = ControllerImages.objects.all()
        for ctrl_image in ctrl_images:
            ctrls_by_image[ctrl_image.image.id].append(ctrl_image.controller.id)

        images = Image.objects.all()
        for image in images:
            if image.id not in ctrls_by_image or controller.id not in ctrls_by_image[image.id]:
                controller_image = ControllerImages(controller=controller, image=image)
                controller_image.save()

