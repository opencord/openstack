
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

class TestSyncSlice(unittest.TestCase):

    def setUp(self):
        self.unittest_setup = setup_sync_unit_test(os.path.abspath(os.path.dirname(os.path.realpath(__file__))),
                                                   globals(),
                                                   [("openstack", "openstack.xproto")] )

        sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), "../steps"))

        self.model_accessor = self.unittest_setup["model_accessor"]

        from sync_slice import SyncSlice
        self.step_class = SyncSlice

        self.service = OpenStackService()
        self.site = Site(name="test-site")
        self.trust_domain = TrustDomain(owner=self.service, name="test-trust")

    def tearDown(self):
        sys.path = self.unittest_setup["sys_path_save"]

    def test_sync_record_create_noexist(self):
        fakeconn = MagicMock()
        with patch.object(self.step_class, "connect_openstack_admin") as fake_connect_openstack_admin:
            fake_connect_openstack_admin.return_value = fakeconn

            trust_domain_id = 5678

            xos_slice = Slice(name="test-slice", trust_domain=self.trust_domain, site=self.site)

            step = self.step_class(model_accessor=self.model_accessor)
            fakeconn.identity.find_project.return_value = None
            fakeconn.identity.find_domain.return_value = MagicMock(id=trust_domain_id)

            os_slice = MagicMock()
            os_slice.id = "1234"
            fakeconn.identity.create_project.return_value = os_slice

            step.sync_record(xos_slice)

            fakeconn.identity.create_project.assert_called_with(name=xos_slice.name, domain_id=trust_domain_id)
            self.assertEqual(xos_slice.backend_handle, "1234")

    def test_sync_record_create_exists(self):
        fakeconn = MagicMock()
        with patch.object(self.step_class, "connect_openstack_admin") as fake_connect_openstack_admin:
            fake_connect_openstack_admin.return_value = fakeconn

            xos_slice = Slice(name="test-slice", trust_domain=self.trust_domain, site=self.site)

            os_slice = MagicMock()
            os_slice.id = "1234"

            step = self.step_class(model_accessor=self.model_accessor)
            fakeconn.identity.find_project.return_value = os_slice
            fakeconn.identity.create_user.return_value = None

            step.sync_record(xos_slice)

            fakeconn.identity.create_slice.assert_not_called()
            self.assertEqual(xos_slice.backend_handle, "1234")

    def test_delete_record(self):
        fakeconn = MagicMock()
        with patch.object(self.step_class, "connect_openstack_admin") as fake_connect_openstack_admin:
            fake_connect_openstack_admin.return_value = fakeconn

            xos_slice = Slice(name="test-slice", trust_domain=self.trust_domain, site=self.site)

            step = self.step_class(model_accessor=self.model_accessor)
            os_slice = MagicMock()
            os_slice.id = "1234"
            fakeconn.identity.find_project.return_value = os_slice
            fakeconn.identity.delete_project.return_value = None

            step.delete_record(xos_slice)
            fakeconn.identity.delete_project.assert_called_with("1234")

if __name__ == '__main__':
    unittest.main()
