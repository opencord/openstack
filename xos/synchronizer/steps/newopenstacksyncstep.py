
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


from distutils.version import LooseVersion
from xossynchronizer.steps.syncstep import SyncStep

class NewOpenStackSyncStep(SyncStep):
    """ XOS Sync step for copying data to OpenStack
    """

    def __init__(self, *args, **kwargs):
        # super() does not work here...
        SyncStep.__init__(self, *args, **kwargs)

    def connect_openstack_admin(self, service, required_version=None):
        import openstack

        if required_version:
            if LooseVersion(openstack.version.__version__) < LooseVersion(required_version):
                raise Exception("Insufficient OpenStack library version",
                                installed_version=openstack.version__version__,
                                required_version=required_version)

        conn = openstack.connect(auth_url=service.auth_url,
                                 project_name="admin",
                                 username=service.admin_user,
                                 password=service.admin_password,
                                 user_domain_name="Default",
                                 project_domain_name="Default")
        return conn

    def connect_openstack_slice(self, slice, required_version=None):
        import openstack

        trust_domain = slice.trust_domain
        service = trust_domain.owner.leaf_model

        if required_version:
            if LooseVersion(openstack.version.__version__) < LooseVersion(required_version):
                raise Exception("Insufficient OpenStack library version",
                                installed_version=openstack.version__version__,
                                required_version=required_version)

        # This is not working yet...

        conn = openstack.connect(auth_url=service.auth_url,
                                 project_name=slice.name,
                                 username=service.admin_user,
                                 password=service.admin_password,
                                 user_domain_name="Default",
                                 project_domain_name=trust_domain.name)
        return conn

    # TODO(smbaker): This should be explained.
    def __call__(self, **args):
        return self.call(**args)
