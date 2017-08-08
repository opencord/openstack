
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

class SlicePolicy(Policy):
    model_name = "Slice"

    def handle_create(self, slice):
        return self.handle_update(slice)

    def handle_update(self, slice):
        support_nat_net = False # Assume we're using VTN rather than nat-net

        # slice = Slice.get(slice_id)

        controller_slices = ControllerSlice.objects.filter(slice_id=slice.id)
        existing_controllers = [cs.controller for cs in controller_slices]
        existing_controllers_ids = [x.id for x in existing_controllers]

        self.logger.info("MODEL POLICY: slice existing_controllers=%s" % existing_controllers)

        all_controllers = Controller.objects.all()
        for controller in all_controllers:
            if controller.id not in existing_controllers_ids:
                self.logger.info("MODEL POLICY: slice adding controller %s" % controller)
                sd = ControllerSlice(slice=slice, controller=controller)
                sd.save()

        if slice.network in ["host", "bridged"]:
            # Host and Bridged docker containers need no networks and they will
            # only get in the way.
            self.logger.info("MODEL POLICY: Skipping network creation")
        elif slice.network in ["noauto"]:
            # do nothing
            pass
        else:
            # make sure slice has at least 1 public and 1 private networkd
            public_nets = []
            private_nets = []
            networks = Network.objects.filter(owner_id=slice.id)
            for network in networks:
                if not network.autoconnect:
                    continue
                if network.template.name == 'Public dedicated IPv4':
                    public_nets.append(network)
                elif network.template.name == 'Public shared IPv4':
                    public_nets.append(network)
                elif network.template.name == 'Private':
                    private_nets.append(network)
            if support_nat_net and (not public_nets):
                # ensure there is at least one public network, and default it to dedicated
                nat_net = Network(
                        name = slice.name+'-nat',
                            template = NetworkTemplate.objects.get(name='Public shared IPv4'),
                        owner = slice
                        )
                if slice.exposed_ports:
                    nat_net.ports = slice.exposed_ports
                nat_net.save()
                public_nets.append(nat_net)
                self.logger.info("MODEL POLICY: slice %s made nat-net" % slice)

            if not private_nets:
                private_net = Network(
                    name = slice.name+'-private',
                    template = NetworkTemplate.objects.get(name='Private'),
                    owner = slice
                )
                private_net.save()
                self.logger.info("MODEL POLICY: slice %s made private net" % slice)
                private_nets = [private_net]
            # create slice networks
            public_net_slice = None
            private_net_slice = None

            public_net_ids = [x.id for x in public_nets]
            private_net_ids = [x.id for x in private_nets]
            net_slices = NetworkSlice.objects.filter(slice_id=slice.id)
            net_slices = [x for x in net_slices if x.network_id in public_net_ids+private_net_ids]

            for net_slice in net_slices:
                if net_slice.network.id in public_net_ids:
                    public_net_slice = net_slice
                elif net_slice.network.id in private_net_ids:
                    private_net_slice = net_slice
            if support_nat_net and (not public_net_slice):
                public_net_slice = NetworkSlice(slice=slice, network=public_nets[0])
                public_net_slice.save()
                self.logger.info("MODEL POLICY: slice %s made public_net_slice" % slice)
            if not private_net_slice:
                private_net_slice = NetworkSlice(slice=slice, network=private_nets[0])
                private_net_slice.save()
                self.logger.info("MODEL POLICY: slice %s made private_net_slice" % slice)

    # TODO: This feels redundant with the reaper
    def handle_delete(self, slice):
        public_nets = []
        private_net = None
        networks = Network.objects.filter(owner_id=slice.id)

        for n in networks:
            n.delete()

        # Note that sliceprivileges and slicecontrollers are autodeleted, through the dependency graph
