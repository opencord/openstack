
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
from collections import defaultdict
from synchronizers.new_base.policy import Policy

class NetworkPolicy(Policy):
    model_name = "Network"

    def handle_create(self, network):
        return self.handle_update(network)

    def handle_update(self, network):
        # For simplicity, let's assume that a network gets deployed on all controllers.
        expected_controllers =  Controller.objects.all()

        existing_controllers = []
        for cn in ControllerNetwork.objects.all():
            if cn.network.id == network.id:
                existing_controllers.append(cn.controller)

        existing_controller_ids = [c.id for c in existing_controllers]

        for expected_controller in expected_controllers:
            if expected_controller.id not in existing_controller_ids:
                lazy_blocked=False

                nd = ControllerNetwork(network=network, controller=expected_controller, lazy_blocked=lazy_blocked)
                self.logger.info("MODEL POLICY: network %s create ControllerNetwork %s lazy_blocked %s" % (network, nd, lazy_blocked))
                if network.subnet:
                    # XXX: Possibly unpredictable behavior if there is
                    # more than one ControllerNetwork and the subnet
                    # is specified.
                    nd.subnet = network.subnet
                nd.save()
