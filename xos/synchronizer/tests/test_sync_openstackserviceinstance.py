
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

import base64
import os
import sys
import unittest
from mock import patch, PropertyMock, ANY, MagicMock
from unit_test_common import setup_sync_unit_test

def fake_connect_openstack_admin(self, service, required_version=None):
    return MagicMock()

class TestSyncOpenStackServiceInstance(unittest.TestCase):

    def setUp(self):
        self.unittest_setup = setup_sync_unit_test(os.path.abspath(os.path.dirname(os.path.realpath(__file__))),
                                                   globals(),
                                                   [("openstack", "openstack.xproto")] )

        sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), "../steps"))

        from sync_openstackserviceinstance import SyncOpenStackServiceInstance
        self.step_class = SyncOpenStackServiceInstance

        self.service = OpenStackService()
        self.site = Site(name="test-site")
        self.trust_domain = TrustDomain(owner=self.service, name="test-trust")
        self.flavor = Flavor(name="test-flavor", backend_handle=1114)
        self.node = Node(name="test-node", backend_handle=1113)
        self.slice = Slice(name="test-slice", trust_domain=self.trust_domain, backend_handle=1112)
        self.image = Image(name="test-image", backend_handle=1111)

    def tearDown(self):
        sys.path = self.unittest_setup["sys_path_save"]

    def test_sync_record_create_noexist(self):
        fakeconn = MagicMock()
        with patch.object(self.step_class, "connect_openstack_admin") as fake_connect_openstack_admin:
            fake_connect_openstack_admin.return_value = fakeconn

            xos_instance = OpenStackServiceInstance(name="test-instance", slice=self.slice, image=self.image,
                                                    node=self.node, flavor=self.flavor)

            step = self.step_class()
            fakeconn.compute.servers.return_value = []
            fakeconn.identity.find_project.return_value = MagicMock(id=self.slice.backend_handle)
            fakeconn.identity.find_domain.return_value = MagicMock(id=self.trust_domain.backend_handle)
            fakeconn.compute.find_image.return_value = MagicMock(id=self.image.backend_handle)
            fakeconn.compute.find_flavor.return_value = MagicMock(id=self.flavor.backend_handle)

            os_instance = MagicMock()
            os_instance.id = "1234"
            fakeconn.compute.create_server.return_value = os_instance

            step.sync_record(xos_instance)

            fakeconn.compute.create_server.assert_called_with(admin_password=ANY,
                                                              availability_zone="nova:test-node",
                                                              config_drive=True,
                                                              flavor_id=self.flavor.backend_handle,
                                                              image_id=self.image.backend_handle,
                                                              name=xos_instance.name,
                                                              networks=[],
                                                              project_domain_id=self.slice.backend_handle,
                                                              user_data=ANY)
            self.assertEqual(xos_instance.backend_handle, "1234")

    def test_sync_record_create_noexist_noflavor(self):
        """ Create a ServiceInstance with no flavor. It should automatically default to m1.small """
        fakeconn = MagicMock()
        with patch.object(self.step_class, "connect_openstack_admin") as fake_connect_openstack_admin:
            fake_connect_openstack_admin.return_value = fakeconn

            xos_instance = OpenStackServiceInstance(name="test-instance", slice=self.slice, image=self.image,
                                                    node=self.node)

            step = self.step_class()
            fakeconn.compute.servers.return_value = []
            fakeconn.identity.find_project.return_value = MagicMock(id=self.slice.backend_handle)
            fakeconn.identity.find_domain.return_value = MagicMock(id=self.trust_domain.backend_handle)
            fakeconn.compute.find_image.return_value = MagicMock(id=self.image.backend_handle)
            fakeconn.compute.find_flavor.return_value = MagicMock(id=self.flavor.backend_handle)

            os_instance = MagicMock()
            os_instance.id = "1234"
            fakeconn.compute.create_server.return_value = os_instance

            step.sync_record(xos_instance)

            fakeconn.compute.create_server.assert_called_with(admin_password=ANY,
                                                              availability_zone="nova:test-node",
                                                              config_drive=True,
                                                              flavor_id=self.flavor.backend_handle,
                                                              image_id=self.image.backend_handle,
                                                              name=xos_instance.name,
                                                              networks=[],
                                                              project_domain_id=self.slice.backend_handle,
                                                              user_data=ANY)
            self.assertEqual(xos_instance.backend_handle, "1234")

    def test_sync_record_create_noexist_nohost(self):
        """ create a ServiceInstance with no node. It should be assigned to the "nova" availability zone
        """

        fakeconn = MagicMock()
        with patch.object(self.step_class, "connect_openstack_admin") as fake_connect_openstack_admin:
            fake_connect_openstack_admin.return_value = fakeconn

            xos_instance = OpenStackServiceInstance(name="test-instance", slice=self.slice, image=self.image,
                                                    flavor=self.flavor)

            step = self.step_class()
            fakeconn.compute.servers.return_value = []
            fakeconn.identity.find_project.return_value = MagicMock(id=self.slice.backend_handle)
            fakeconn.identity.find_domain.return_value = MagicMock(id=self.trust_domain.backend_handle)
            fakeconn.compute.find_image.return_value = MagicMock(id=self.image.backend_handle)
            fakeconn.compute.find_flavor.return_value = MagicMock(id=self.flavor.backend_handle)

            os_instance = MagicMock()
            os_instance.id = "1234"
            fakeconn.compute.create_server.return_value = os_instance

            step.sync_record(xos_instance)

            fakeconn.compute.create_server.assert_called_with(admin_password=ANY,
                                                              availability_zone="nova",
                                                              config_drive=True,
                                                              flavor_id=self.flavor.backend_handle,
                                                              image_id=self.image.backend_handle,
                                                              name=xos_instance.name,
                                                              networks=[],
                                                              project_domain_id=self.slice.backend_handle,
                                                              user_data=ANY)
            self.assertEqual(xos_instance.backend_handle, "1234")

    def test_sync_record_create_noexist_with_keys(self):
        fakeconn = MagicMock()
        with patch.object(self.step_class, "connect_openstack_admin") as fake_connect_openstack_admin:
            fake_connect_openstack_admin.return_value = fakeconn

            xos_instance = OpenStackServiceInstance(name="test-instance", slice=self.slice, image=self.image,
                                                    node=self.node, flavor=self.flavor)

            admin_user = User(email="test_user@test.com", public_key="key1")
            self.slice.creator = admin_user

            owning_service = Service(name="test_service", public_key="key2")
            self.slice.service = owning_service

            step = self.step_class()
            fakeconn.compute.servers.return_value = []
            fakeconn.identity.find_project.return_value = MagicMock(id=self.slice.backend_handle)
            fakeconn.identity.find_domain.return_value = MagicMock(id=self.trust_domain.backend_handle)
            fakeconn.compute.find_image.return_value = MagicMock(id=self.image.backend_handle)
            fakeconn.compute.find_flavor.return_value = MagicMock(id=self.flavor.backend_handle)

            os_instance = MagicMock()
            os_instance.id = "1234"
            fakeconn.compute.create_server.return_value = os_instance

            step.sync_record(xos_instance)

            expected_userdata = base64.b64encode('#cloud-config\n\nssh_authorized_keys:\n  - key1\n  - key2\n')

            fakeconn.compute.create_server.assert_called_with(admin_password=ANY,
                                                              availability_zone="nova:test-node",
                                                              config_drive=True,
                                                              flavor_id=self.flavor.backend_handle,
                                                              image_id=self.image.backend_handle,
                                                              name=xos_instance.name,
                                                              networks=[],
                                                              project_domain_id=self.slice.backend_handle,
                                                              user_data=expected_userdata)
            self.assertEqual(xos_instance.backend_handle, "1234")

    def test_sync_record_create_exists(self):
        fakeconn = MagicMock()
        with patch.object(self.step_class, "connect_openstack_admin") as fake_connect_openstack_admin:
            fake_connect_openstack_admin.return_value = fakeconn

            xos_instance = OpenStackServiceInstance(name="test-instance", slice=self.slice, image=self.image,
                                                    node=self.node, flavor=self.flavor)

            os_instance = MagicMock()
            os_instance.id = "1234"

            step = self.step_class()
            fakeconn.identity.find_project.return_value = os_instance
            fakeconn.compute.create_server.return_value = None
            fakeconn.compute.servers.return_value = [os_instance]

            step.sync_record(xos_instance)

            fakeconn.compute.create_server.assert_not_called()
            self.assertEqual(xos_instance.backend_handle, "1234")

    def test_delete_record(self):
        fakeconn = MagicMock()
        with patch.object(self.step_class, "connect_openstack_admin") as fake_connect_openstack_admin:
            fake_connect_openstack_admin.return_value = fakeconn

            xos_instance = OpenStackServiceInstance(name="test-instance", slice=self.slice, image=self.image,
                                                    node=self.node, flavor=self.flavor)

            step = self.step_class()
            os_instance = MagicMock()
            os_instance.id = "1234"
            fakeconn.compute.servers.return_value = [os_instance]
            fakeconn.compute.delete_server.return_value = None

            step.delete_record(xos_instance)
            fakeconn.compute.delete_server.assert_called_with("1234")

if __name__ == '__main__':
    unittest.main()
