
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

class InstancePolicy(Policy):
    model_name = "Instance"

    def handle_create(self, instance):
        return self.handle_update(instance)

    def handle_update(self, instance):
        networks = [ns.network for ns in NetworkSlice.objects.filter(slice_id=instance.slice.id)]
        controller_networks = ControllerNetwork.objects.filter(controller_id=instance.node.site_deployment.controller.id)

        # a little clumsy because the API ORM doesn't support __in queries
        network_ids = [x.id for x in networks]
        controller_networks = [x for x in controller_networks if x.network.id in network_ids]

        for cn in controller_networks:
            if (cn.lazy_blocked):
                    self.logger.info("MODEL POLICY: instance %s unblocking network %s" % (instance, cn.network))
            cn.lazy_blocked=False
            cn.backend_register = '{}'
            cn.save()
