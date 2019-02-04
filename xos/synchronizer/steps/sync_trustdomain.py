
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


from xossynchronizer.modelaccessor import TrustDomain
from newopenstacksyncstep import NewOpenStackSyncStep

from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))

class SyncTrustDomain(NewOpenStackSyncStep):
    provides=[TrustDomain]
    requested_interval=0
    observes=TrustDomain

    def fetch_pending(self, deleted):
        """ Figure out which TrustDomains are interesting to the OpenStack synchronizer. It's necessary to filter as
            we're synchronizing a core model, and we only want to synchronize trust domains that will exist within
            OpenStack.
        """
        objs = super(SyncTrustDomain, self).fetch_pending(deleted)
        for obj in objs[:]:
            # If the TrustDomain isn't part of the OpenStack service, then it's someone else's trust domain
            if "OpenStackService" not in obj.owner.leaf_model.class_names:
                objs.remove(obj)
        return objs

    def sync_record(self, trust_domain):
        service = trust_domain.owner.leaf_model
        conn = self.connect_openstack_admin(service)

        os_domain = conn.identity.find_domain(trust_domain.name)
        if (os_domain):
            log.info("Trust Domain already exists in openstack", trust_domain=trust_domain)
        else:
            log.info("Creating Trust Domain", trust_domain=trust_domain)
            os_domain = conn.identity.create_domain(name=trust_domain.name)

        if os_domain.id != trust_domain.backend_handle:
            trust_domain.backend_handle = os_domain.id
            trust_domain.save(update_fields=["backend_handle"])

    def delete_record(self, trust_domain):
        service = trust_domain.owner.leaf_model
        conn = self.connect_openstack_admin(service)

        os_domain = conn.identity.find_domain(trust_domain.name)
        if (not os_domain):
            log.info("Trust Domain already does not exist in openstack", trust_domain=trust_domain)
        else:
            if os_domain.is_enabled:
                log.info("Disabling Trust Domain", trust_domain=trust_domain, os_id=os_domain.id)
                os_domain=conn.identity.update_domain(os_domain.id, enabled=False)
            log.info("Deleting Trust Domain", trust_domain=trust_domain, os_id=os_domain.id)
            conn.identity.delete_domain(os_domain.id)
