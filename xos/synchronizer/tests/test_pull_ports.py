
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

import json
import os
import sys
import unittest
from mock import patch, PropertyMock, ANY, MagicMock
from unit_test_common import setup_sync_unit_test

def fake_connect_openstack_admin(self, service, required_version=None):
    return MagicMock()

class TestPullPorts(unittest.TestCase):

    def setUp(self):
        self.unittest_setup = setup_sync_unit_test(os.path.abspath(os.path.dirname(os.path.realpath(__file__))),
                                                   globals(),
                                                   [("openstack", "openstack.xproto")] )

        sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), "../pull_steps"))

        from pull_ports import OpenStackPortPullStep
        self.step_class = OpenStackPortPullStep

        self.service = OpenStackService()
        self.site = Site(name="test-site")
        self.trust_domain = TrustDomain(owner=self.service, name="test-trust")
        self.flavor = Flavor(name="test-flavor", backend_handle=1114)
        self.node = Node(name="test-node", backend_handle=1113)
        self.slice = Slice(name="test-slice", trust_domain=self.trust_domain, backend_handle=1112)
        self.image = Image(name="test-image", backend_handle=1111)
        self.net_management = Network(name="management", backend_handle=1115)

    def tearDown(self):
        sys.path = self.unittest_setup["sys_path_save"]

    def test_pull_records(self):
        fakeconn = MagicMock()
        with patch.object(self.step_class, "connect_openstack_admin") as fake_connect_openstack_admin, \
             patch.object(Port.objects, "get_items") as port_objects, \
             patch.object(Network.objects, "get_items") as network_objects, \
             patch.object(OpenStackServiceInstance.objects, "get_items") as ossi_objects, \
             patch.object(OpenStackService.objects, "get_items") as osi_objects, \
             patch.object(Port, "save", autospec=True) as port_save:
            fake_connect_openstack_admin.return_value = fakeconn

            xos_instance = OpenStackServiceInstance(name="test-instance", slice=self.slice, image=self.image,
                                                    node=self.node, flavor=self.flavor, backend_handle=2112)

            port_objects.return_value = []
            network_objects.return_value = [self.net_management]
            ossi_objects.return_value = [xos_instance]
            osi_objects.return_value = [self.service]

            cn = ControllerNetwork(net_id=self.net_management.backend_handle)
            self.net_management.controllernetworks = self.unittest_setup["MockObjectList"]([cn])

            fakeconn.network.ports.return_value = [MagicMock(id=2111, device_id=xos_instance.backend_handle,
                                                             network_id=self.net_management.backend_handle,
                                                             fixed_ips=[{"ip_address": "1.2.3.4"}],
                                                             mac_address="11:22:33:44:55:66")]

            step = self.step_class()
            step.pull_records()

            self.assertEqual(port_save.call_count, 1)
            saved_port = port_save.call_args[0][0]

            self.assertEqual(saved_port.network, self.net_management)
            self.assertEqual(saved_port.ip, "1.2.3.4")
            self.assertEqual(saved_port.mac, "11:22:33:44:55:66")
            self.assertEqual(saved_port.port_id, 2111)
            self.assertEqual(saved_port.service_instance, xos_instance)



if __name__ == '__main__':
    unittest.main()
