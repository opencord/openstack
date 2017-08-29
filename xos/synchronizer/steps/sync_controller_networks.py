
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
import struct
import socket
from netaddr import IPAddress, IPNetwork
from synchronizers.openstack.openstacksyncstep import OpenStackSyncStep
from synchronizers.new_base.syncstep import *
from xos.logger import observer_logger as logger
from synchronizers.new_base.ansible_helper import *
from synchronizers.new_base.modelaccessor import *

class SyncControllerNetworks(OpenStackSyncStep):
    requested_interval = 0
    provides=[Network]
    observes=ControllerNetwork	
    playbook='sync_controller_networks.yaml'

    def alloc_subnet(self, uuid):
        # 16 bits only
        uuid_masked = uuid & 0xffff
        a = 10
        b = uuid_masked >> 8
        c = uuid_masked & 0xff
        d = 0

        cidr = '%d.%d.%d.%d/24'%(a,b,c,d)
        return cidr

    def alloc_gateway(self, subnet):
        # given a CIDR, allocate a default gateway using the .1 address within
        # the subnet.
        #    10.123.0.0/24 --> 10.123.0.1
        #    207.141.192.128/28 --> 207.141.192.129
        (network, bits) = subnet.split("/")
        network=network.strip()
        bits=int(bits.strip())
        netmask = (~(pow(2,32-bits)-1) & 0xFFFFFFFF)
        ip = struct.unpack("!L", socket.inet_aton(network))[0]
        ip = ip & netmask | 1
        return socket.inet_ntoa(struct.pack("!L", ip))

    def get_segmentation_id(self, controller_network):
        driver = self.driver.admin_driver(controller = controller_network.controller)
        neutron_network = driver.shell.neutron.list_networks(controller_network.network_id)["networks"][0]
        if "provider:segmentation_id" in neutron_network:
            return neutron_network["provider:segmentation_id"]
        else:
            return None

    def save_controller_network(self, controller_network):
        network_name = controller_network.network.name
        subnet_name = '%s-%d'%(network_name,controller_network.pk)
        if controller_network.subnet and controller_network.subnet.strip():
            # If a subnet is already specified (pass in by the creator), then
            # use that rather than auto-generating one.
            cidr = controller_network.subnet.strip()
            print "CIDR_MS", cidr
        else:
            cidr = self.alloc_subnet(controller_network.pk)
            print "CIDR_AMS", cidr

        if controller_network.network.start_ip and controller_network.network.start_ip.strip():
            start_ip = controller_network.network.start_ip.strip()
        else:
            start_ip = None

        if controller_network.network.end_ip and controller_network.network.end_ip.strip():
            end_ip = controller_network.network.end_ip.strip()
        else:
            end_ip = None

        self.cidr=cidr
        slice = controller_network.network.owner

        controller_network.gateway = self.alloc_gateway(cidr)

        network_fields = {'endpoint':controller_network.controller.auth_url,
                    'endpoint_v3': controller_network.controller.auth_url_v3,
                    'admin_user':slice.creator.email,
                    'admin_password':slice.creator.remote_password,
                    'admin_project':slice.name,
                    'domain': controller_network.controller.domain,
                    'name':network_name,
                    'subnet_name':subnet_name,
                    'ansible_tag':'%s-%s@%s'%(network_name,slice.slicename,controller_network.controller.name),
                    'cidr':cidr,
                    'gateway': controller_network.gateway,
                    'start_ip':start_ip,
                    'end_ip':end_ip,
                    'use_vtn':True,
                    'delete':False
                    }
        return network_fields

    def map_sync_outputs(self, controller_network,res):
        network_id = res[0]['network']['id']
        subnet_id = res[1]['subnet']['id']
        controller_network.net_id = network_id
        controller_network.subnet = self.cidr
        controller_network.subnet_id = subnet_id
	controller_network.backend_status = 'OK'
	controller_network.backend_code = 1
        if not controller_network.segmentation_id:
            controller_network.segmentation_id = str(self.get_segmentation_id(controller_network))
        controller_network.save()


    def map_sync_inputs(self, controller_network):
        # make sure to not sync a shared network
        if (controller_network.network.template.shared_network_name or controller_network.network.template.shared_network_id):
            return SyncStep.SYNC_WITHOUT_RUNNING

        if not controller_network.controller.admin_user:
            logger.info("controller %r has no admin_user, skipping" % controller_network.controller)
            return

        if controller_network.network.owner and controller_network.network.owner.creator:
	    return self.save_controller_network(controller_network)
        else:
            raise Exception('Could not save network controller %s'%controller_network)

    def map_delete_inputs(self, controller_network):
        # make sure to not delete a shared network
        if (controller_network.network.template.shared_network_name or controller_network.network.template.shared_network_id):
            return

	try:
        	slice = controller_network.network.owner # XXX: FIXME!!
        except:
                raise Exception('Could not get slice for Network %s'%controller_network.network.name)

	network_name = controller_network.network.name
        subnet_name = '%s-%d'%(network_name,controller_network.pk)
	cidr = controller_network.subnet
	network_fields = {'endpoint':controller_network.controller.auth_url,
                    'admin_user':slice.creator.email, # XXX: FIXME
                    'admin_project':slice.name, # XXX: FIXME
                    'admin_password':slice.creator.remote_password,
                    'name':network_name,
                    'subnet_name':subnet_name,
                    'ansible_tag':'%s-%s@%s'%(network_name,slice.slicename,controller_network.controller.name),
                    'cidr':cidr,
		    'delete':True	
                    }

        return network_fields

