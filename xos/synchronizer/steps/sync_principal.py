
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


from xossynchronizer.modelaccessor import TrustDomain, Principal
from newopenstacksyncstep import NewOpenStackSyncStep

from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))

class SyncPrincipal(NewOpenStackSyncStep):
    provides=[Principal]
    requested_interval=0
    observes=Principal

    def fetch_pending(self, deleted):
        """ Figure out which Principals are interesting to the OpenStack synchronizer. It's necessary to filter as we're
            synchronizing a core model, and we only want to synchronize trust domains that will exist within
            OpenStack.
        """
        objs = super(SyncPrincipal, self).fetch_pending(deleted)
        for obj in objs[:]:
            # If the Principal isn't in a TrustDomain, then the OpenStack synchronizer can't do anything with it
            if not obj.trust_domain:
                objs.remove(obj)
                continue

            # If the TrustDomain isn't part of the OpenStack service, then it's someone else's trust domain
            if "OpenStackService" not in obj.trust_domain.owner.leaf_model.class_names:
                objs.remove(obj)
        return objs

    def sync_record(self, principal):
        service = principal.trust_domain.owner.leaf_model
        conn = self.connect_openstack_admin(service)

        os_domain = conn.identity.find_domain(principal.trust_domain.name)

        os_user = conn.identity.find_user(principal.name, domain_id=os_domain.id)
        if (os_user):
            log.info("Principal already exists in openstack", principal=principal)
        else:
            log.info("Creating Principal", principal=principal)
            os_user = conn.identity.create_user(name=principal.name, domain_id=os_domain.id)

        if os_user.id != principal.backend_handle:
            principal.backend_handle = os_user.id
            principal.save(update_fields=["backend_handle"])

    def delete_record(self, principal):
        service = principal.trust_domain.owner.leaf_model
        conn = self.connect_openstack_admin(service)

        os_domain = conn.identity.find_domain(principal.trust_domain.name)

        os_user = conn.identity.find_user(principal.name, domain_id=os_domain.id)
        if (not os_user):
            log.info("Principal already does not exist in openstack", principal=principal)
        else:
            log.info("Deleting Principal", principal=principal, os_id=os_domain.id)
            conn.identity.delete_user(os_user.id)
