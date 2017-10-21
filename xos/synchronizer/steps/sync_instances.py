
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


import os
import base64
import socket
from synchronizers.openstack.openstacksyncstep import OpenStackSyncStep
from synchronizers.new_base.ansible_helper import *
from synchronizers.new_base.syncstep import *
from xos.logger import observer_logger as logger
from synchronizers.new_base.modelaccessor import *

RESTAPI_HOSTNAME = socket.gethostname()
RESTAPI_PORT = "8000"


def escape(s):
    s = s.replace('\n', r'\n').replace('"', r'\"')
    return s


class SyncInstances(OpenStackSyncStep):
    provides = [Instance]
    requested_interval = 0
    observes = Instance
    playbook = 'sync_instances.yaml'

    def fetch_pending(self, deletion=False):
        objs = super(SyncInstances, self).fetch_pending(deletion)
        objs = [x for x in objs if x.isolation == "vm"]
        return objs

    def get_userdata(self, instance, pubkeys):
        userdata = '#cloud-config\n\nopencloud:\n   slicename: "%s"\n   hostname: "%s"\n   restapi_hostname: "%s"\n   restapi_port: "%s"\n' % (
        instance.slice.name, instance.node.name, RESTAPI_HOSTNAME, str(RESTAPI_PORT))
        userdata += 'ssh_authorized_keys:\n'
        for key in pubkeys:
            userdata += '  - %s\n' % key
        return userdata

    def get_nic_for_first_slot(self, nics):
        # Try to find a NIC with "public" visibility
        for nic in nics[:]:
            network = nic.get("network", None)
            if network:
                tem = network.template
                if (tem.visibility == "public"):
                    return nic

        # Otherwise try to find a private network
        for nic in nics[:]:
            network = nic.get("network", None)
            if network:
                tem = network.template
                if (tem.visibility == "private") and (tem.translation == "none") and ("management" not in tem.name):
                    return nic

        raise Exception("Could not find a NIC for first slot")

    def sort_nics(self, nics):
        result = []

        # Enforce VTN's network order requirement for vSG.  The access network must be
        # inserted into the first slot. The management network must be inserted
        # into the second slot.
        #
        # Some VMs may connect to multiple networks that advertise gateways.  In this case, the
        # default gateway is enforced on eth0.  So give priority to "public" networks when 
        # choosing a network for the first slot.

        nic = self.get_nic_for_first_slot(nics)
        result.append(nic)
        nics.remove(nic)

        # move the management network to the second spot
        for nic in nics[:]:
            network = nic.get("network", None)
            if network:
                tem = network.template
                if (tem.visibility == "private") and (tem.translation == "none") and ("management" in tem.name):
                    # MCORD
                    #                    if len(result)!=1:
                    #                        raise Exception("Management network needs to be inserted in slot 1, but there are %d private nics" % len(result))
                    result.append(nic)
                    nics.remove(nic)

        # add everything else. For VTN there probably shouldn't be any more.
        result.extend(nics)

        return result

    def map_sync_inputs(self, instance):

        # sanity check - make sure model_policy for slice has run
        if ((not instance.slice.policed) or (instance.slice.policed < instance.slice.updated)):
            raise DeferredException(
                "Instance %s waiting on Slice %s to execute model policies" % (instance, instance.slice.name))

        # sanity check - make sure model_policy for all slice networks have run
        for network in instance.slice.ownedNetworks.all():
            if ((not network.policed) or (network.policed < network.updated)):
                raise DeferredException(
                    "Instance %s waiting on Network %s to execute model policies" % (instance, network.name))

        inputs = {}
        metadata_update = {}
        if (instance.numberCores):
            metadata_update["cpu_cores"] = str(instance.numberCores)

        # not supported by API... assuming it's not used ... look into enabling later
        #        for tag in instance.slice.tags.all():
        #            if tag.name.startswith("sysctl-"):
        #                metadata_update[tag.name] = tag.value

        slice_memberships = SlicePrivilege.objects.filter(slice_id=instance.slice.id)
        pubkeys = set([sm.user.public_key for sm in slice_memberships if sm.user.public_key])
        if instance.creator.public_key:
            pubkeys.add(instance.creator.public_key)

        if instance.slice.creator.public_key:
            pubkeys.add(instance.slice.creator.public_key)

        if instance.slice.service and instance.slice.service.public_key:
            pubkeys.add(instance.slice.service.public_key)

        nics = []

        # handle ports the were created by the user
        port_ids = []
        for port in Port.objects.filter(instance_id=instance.id):
            if not port.port_id:
                raise DeferredException("Instance %s waiting on port %s" % (instance, port))
            nics.append({"kind": "port", "value": port.port_id, "network": port.network})

        # we want to exclude from 'nics' any network that already has a Port
        existing_port_networks = [port.network for port in Port.objects.filter(instance_id=instance.id)]
        existing_port_network_ids = [x.id for x in existing_port_networks]

        networks = [ns.network for ns in NetworkSlice.objects.filter(slice_id=instance.slice.id) if
                    ns.network.id not in existing_port_network_ids]
        networks_ids = [x.id for x in networks]
        controller_networks = ControllerNetwork.objects.filter(
            controller_id=instance.node.site_deployment.controller.id)
        controller_networks = [x for x in controller_networks if x.network_id in networks_ids]

        for network in networks:
            if not ControllerNetwork.objects.filter(network_id=network.id,
                                                    controller_id=instance.node.site_deployment.controller.id).exists():
                raise DeferredException(
                    "Instance %s Private Network %s lacks ControllerNetwork object" % (instance, network.name))

        for controller_network in controller_networks:
            # Lenient exception - causes slow backoff
            if controller_network.network.template.translation == 'none':
                if not controller_network.net_id:
                    raise DeferredException("Instance %s Private Network %s has no id; Try again later" % (
                    instance, controller_network.network.name))
                nics.append({"kind": "net", "value": controller_network.net_id, "network": controller_network.network})

        # now include network template
        network_templates = [network.template.shared_network_name for network in networks \
                             if network.template.shared_network_name]

        driver = self.driver.admin_driver(tenant='admin', controller=instance.node.site_deployment.controller)
        nets = driver.shell.neutron.list_networks()['networks']
        for net in nets:
            if net['name'] in network_templates:
                nics.append({"kind": "net", "value": net['id'], "network": None})

        if (not nics):
            for net in nets:
                if net['name'] == 'public':
                    nics.append({"kind": "net", "value": net['id'], "network": None})

        nics = self.sort_nics(nics)

        image_name = None
        controller_images = instance.image.controllerimages.all()
        controller_images = [x for x in controller_images if
                             x.controller_id == instance.node.site_deployment.controller.id]
        if controller_images:
            image_name = controller_images[0].image.name
            logger.info("using image from ControllerImage object: " + str(image_name))

        if image_name is None:
            controller_driver = self.driver.admin_driver(controller=instance.node.site_deployment.controller)
            images = controller_driver.shell.glanceclient.images.list()
            for image in images:
                if image.name == instance.image.name or not image_name:
                    image_name = image.name
                    logger.info("using image from glance: " + str(image_name))

        host_filter = instance.node.name.strip()

        availability_zone_filter = 'nova:%s' % host_filter
        instance_name = '%s-%d' % (instance.slice.name, instance.id)
        self.instance_name = instance_name

        userData = self.get_userdata(instance, pubkeys)
        if instance.userData:
            userData += instance.userData

        # make sure nics is pickle-able
        sanitized_nics = [{"kind": nic["kind"], "value": nic["value"]} for nic in nics]

        controller = instance.node.site_deployment.controller
        fields = {'endpoint': controller.auth_url,
                  'endpoint_v3': controller.auth_url_v3,
                  'domain': controller.domain,
                  'admin_user': instance.creator.email,
                  'admin_password': instance.creator.remote_password,
                  'project_name': instance.slice.name,
                  'tenant': instance.slice.name,
                  'tenant_description': instance.slice.description,
                  'name': instance_name,
                  'ansible_tag': instance_name,
                  'availability_zone': availability_zone_filter,
                  'image_name': image_name,
                  'flavor_name': instance.flavor.name,
                  'nics': sanitized_nics,
                  'meta': metadata_update,
                  'user_data': r'%s' % escape(userData)}
        return fields

    def map_sync_outputs(self, instance, res):
        instance_id = res[0]['openstack']['OS-EXT-SRV-ATTR:instance_name']
        instance_uuid = res[0]['id']

        try:
            hostname = res[0]['openstack']['OS-EXT-SRV-ATTR:hypervisor_hostname']
            ip = socket.gethostbyname(hostname)
            instance.ip = ip
        except:
            pass

        instance.instance_id = instance_id
        instance.instance_uuid = instance_uuid
        instance.instance_name = self.instance_name
        instance.save()

    def map_delete_inputs(self, instance):
        controller_register = json.loads(instance.node.site_deployment.controller.backend_register)

        if (controller_register.get('disabled', False)):
            raise InnocuousException('Controller %s is disabled' % instance.node.site_deployment.controller.name)

        instance_name = '%s-%d' % (instance.slice.name, instance.id)
        controller = instance.node.site_deployment.controller
        input = {'endpoint': controller.auth_url,
                 'admin_user': instance.creator.email,
                 'admin_password': instance.creator.remote_password,
                 'project_name': instance.slice.name,
                 'tenant': instance.slice.name,
                 'tenant_description': instance.slice.description,
                 'name': instance_name,
                 'ansible_tag': instance_name,
                 'delete': True}
        return input
