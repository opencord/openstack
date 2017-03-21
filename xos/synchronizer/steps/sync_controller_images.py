import os
import base64
from xos.config import Config
from synchronizers.openstack.openstacksyncstep import OpenStackSyncStep
from synchronizers.new_base.syncstep import *
from xos.logger import observer_logger as logger
from synchronizers.new_base.ansible_helper import *
from synchronizers.new_base.modelaccessor import *

class SyncControllerImages(OpenStackSyncStep):
    provides=[ControllerImages]
    observes = ControllerImages
    requested_interval=0
    playbook='sync_controller_images.yaml'

    def fetch_pending(self, deleted):
        if (deleted):
            return []

        return super(SyncControllerImages, self).fetch_pending(deleted)

    def map_sync_inputs(self, controller_image):
        image_fields = {'endpoint':controller_image.controller.auth_url,
                        'endpoint_v3': controller_image.controller.auth_url_v3,
                        'admin_user':controller_image.controller.admin_user,
                        'admin_password':controller_image.controller.admin_password,
                        'domain': controller_image.controller.domain,
                        'name':controller_image.image.name,
                        'filepath':controller_image.image.path,
                        'ansible_tag': '%s@%s'%(controller_image.image.name,controller_image.controller.name), # name of ansible playbook
                        }

	return image_fields

    def map_sync_outputs(self, controller_image, res):
        image_id = res[0]['id']
        controller_image.glance_image_id = image_id
	controller_image.backend_status = '1 - OK'
        controller_image.save()
