
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
import random
import string

from xossynchronizer.modelaccessor import OpenStackServiceInstance, Node, NetworkSlice, Flavor
from newopenstacksyncstep import NewOpenStackSyncStep

from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))

class SyncOpenStackServiceInstance(NewOpenStackSyncStep):
    provides=[OpenStackServiceInstance]
    requested_interval=0
    observes=OpenStackServiceInstance

    def get_connected_networks(self, instance):
        xos_networks = [ns.network for ns in NetworkSlice.objects.filter(slice_id=instance.slice.id)]
        return xos_networks

    def get_user_data(self, instance):
        pubkeys=[]

        if instance.slice.creator and instance.slice.creator.public_key:
            pubkeys.append(instance.slice.creator.public_key)

        if instance.slice.service and instance.slice.service.public_key:
            pubkeys.append(instance.slice.service.public_key)

        userdata = '#cloud-config\n\n'
#        userdata += 'opencloud:\n   slicename: "%s"\n   hostname: "%s"\n   restapi_hostname: "%s"\n   restapi_port: "%s"\n' % (
#        instance.slice.name, instance.node.name, RESTAPI_HOSTNAME, str(RESTAPI_PORT))
        userdata += 'ssh_authorized_keys:\n'
        for key in pubkeys:
            userdata += '  - %s\n' % key

        log.info("generated userdata", userdata=userdata)

        return userdata

    def get_network_for_first_slot(self, networks):
        # Try to find a NIC with "public" visibility
        for network in networks:
            if (network.template.visibility == "public"):
                return network

        # Otherwise try to find a private network
        for network in networks:
            if (network.template.visibility == "private") and (network.template.translation == "none") and \
                    ("management" not in network.template.name):
                return network

        return None

    def get_network_for_second_slot(self, networks):
        for network in networks:
            if (network.template.visibility == "private") and (network.template.translation == "none") and \
                    ("management" in network.template.name):
                return network

        return None

    def sort_networks(self, networks):
        """ Implement our historic idiosyncratic network selection process.

            1) Try to put a public network in the first slot. If you don't find a public network, then put a private
               non-management network in the first slot.

            2) Try to put the management network in the second slot.

            3) Add all remaining networks that were now selected for #1 or #2.
        """

        networks = networks[:]
        result = []

        first_network = self.get_network_for_first_slot(networks)
        if (first_network):
            result.append(first_network)
            networks.remove(first_network)

        second_network = self.get_network_for_second_slot(networks)
        if (second_network):
            result.append(second_network)
            networks.remove(second_network)

        result.extend(networks)

        return result

    def sync_record(self, instance):
        slice = instance.slice
        if not slice.trust_domain:
            raise Exception("Instance's slice has no trust domain")

        service = instance.slice.trust_domain.owner.leaf_model
        #conn = self.connect_openstack_slice(slice)
        conn = self.connect_openstack_admin(service)

        os_domain = conn.identity.find_domain(slice.trust_domain.name)
        os_project = conn.identity.find_project(slice.name, domain_id=os_domain.id)

        os_instances = list(conn.compute.servers(name=instance.name, project_id=os_project.id))
        if os_instances:
            os_instance=os_instances[0]
            log.info("Instance already exists in openstack", instance=instance)
        else:
            image_name = instance.image.name
            image_id = conn.compute.find_image(image_name).id

            if instance.flavor:
                flavor_name = instance.flavor.name
            else:
                # pick a sensible default
                flavor_name = "m1.small"
            flavor_id = conn.compute.find_flavor(flavor_name).id

            xos_networks = self.get_connected_networks(instance)
            xos_networks = self.sort_networks(xos_networks)
            networks = []
            for xos_network in xos_networks:
                networks.append({"uuid": conn.network.find_network(xos_network.name).id})

            # TODO(smbaker): No ssh keys specified

            if not instance.node:
                availability_zone = "nova"
            else:
                availability_zone="nova:%s" % instance.node.name

            log.info("Creating Instance", instance=instance, image_id=image_id, flavor_id=flavor_id,
                     availability_zone=availability_zone,
                     networks=networks)

            if not instance.admin_password:
                instance.admin_password = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
                instance.save(update_fields=["admin_password"])

            user_data = self.get_user_data(instance)

            os_instance = conn.compute.create_server(name=instance.name,
                                                     image_id=image_id,
                                                     flavor_id=flavor_id,
                                                     project_domain_id=os_project.id,
                                                     availability_zone=availability_zone,
                                                     networks=networks,
                                                     config_drive=True,
                                                     user_data=base64.b64encode(user_data),
                                                     admin_password=instance.admin_password)

        if os_instance.id != instance.backend_handle:
            instance.backend_handle = os_instance.id
            instance.save(update_fields=["backend_handle"])

    def delete_record(self, instance):
        slice = instance.slice
        if not slice.trust_domain:
            raise Exception("Instance's slice has no trust domain")

        service = slice.trust_domain.owner.leaf_model
        conn = self.connect_openstack_admin(service)

        os_domain = conn.identity.find_domain(slice.trust_domain.name)
        os_project = conn.identity.find_project(slice.name, domain_id=os_domain.id)

        os_instances = list(conn.compute.servers(name=instance.name, project_id=os_project.id))
        if (not os_instances):
            log.info("Instance already does not exist in openstack", instance=instance)
        else:
            os_instance=os_instances[0]
            log.info("Deleting Instance", instance=instance, os_id=os_instance.id)
            conn.compute.delete_server(os_instance.id)
