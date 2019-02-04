
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
from openstacksyncstep import OpenStackSyncStep
from xossynchronizer.modelaccessor import *
from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))


class SyncControllerSlices(OpenStackSyncStep):
    provides=[Slice]
    requested_interval=0
    observes=ControllerSlice
    playbook='sync_controller_slices.yaml'

    def map_sync_inputs(self, controller_slice):
        log.info("sync'ing slice controller %s" % controller_slice)

        if not controller_slice.controller.admin_user:
            log.info("controller %r has no admin_user, skipping" % controller_slice.controller)
            return

        controller_users = ControllerUser.objects.filter(user_id=controller_slice.slice.creator.id,
                                                             controller_id=controller_slice.controller.id)
        if not controller_users:
            raise Exception("slice createor %s has not accout at controller %s" % (controller_slice.slice.creator, controller_slice.controller.name))
        else:
            controller_user = controller_users[0]
            driver = self.driver.admin_driver(controller=controller_slice.controller)
            roles = [driver.get_admin_role().name]

        max_instances=int(controller_slice.slice.max_instances)
        tenant_fields = {'endpoint':controller_slice.controller.auth_url,
                         'endpoint_v3': controller_slice.controller.auth_url_v3,
                         'domain': controller_slice.controller.domain,
                         'admin_user': controller_slice.controller.admin_user,
                         'admin_password': controller_slice.controller.admin_password,
                         'admin_project': 'admin',
                         'project': controller_slice.slice.name,
                         'project_description': controller_slice.slice.description,
                         'roles':roles,
                         'username':controller_user.user.email,
                         'ansible_tag':'%s@%s'%(controller_slice.slice.name,controller_slice.controller.name),
                         'max_instances':max_instances}

        return tenant_fields

    def map_sync_outputs(self, controller_slice, res):
        tenant_id = res[0]['project']['id']
        if (not controller_slice.tenant_id):
            try:
                driver = self.driver.admin_driver(controller=controller_slice.controller)
                driver.shell.nova.quotas.update(tenant_id=tenant_id, instances=int(controller_slice.slice.max_instances))
            except:
                log.exception('Could not update quota for %s'%controller_slice.slice.name)
                raise Exception('Could not update quota for %s'%controller_slice.slice.name)

            controller_slice.tenant_id = tenant_id
            controller_slice.backend_status = 'OK'
            controller_slice.backend_code = 1
            controller_slice.save()


    def map_delete_inputs(self, controller_slice):
        controller_users = ControllerUser.objects.filter(user_id=controller_slice.slice.creator.id,
                                                              controller_id=controller_slice.controller.id)
        if not controller_users:
            raise Exception("slice createor %s has not accout at controller %s" % (controller_slice.slice.creator, controller_slice.controller.name))
        else:
            controller_user = controller_users[0]

        tenant_fields = {'endpoint':controller_slice.controller.auth_url,
                          'endpoint_v3': controller_slice.controller.auth_url_v3,
                          'domain': controller_slice.controller.domain,
                          'admin_user': controller_slice.controller.admin_user,
                          'admin_password': controller_slice.controller.admin_password,
                          'admin_project': 'admin',
                          'project': controller_slice.slice.name,
                          'project_description': controller_slice.slice.description,
                          'name':controller_user.user.email,
                          'ansible_tag':'%s@%s'%(controller_slice.slice.name,controller_slice.controller.name),
                          'delete': True}
	return tenant_fields
