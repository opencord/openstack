import os
import base64
from xos.config import Config
from synchronizers.openstack.openstacksyncstep import OpenStackSyncStep
from xos.logger import observer_logger as logger
from synchronizers.new_base.modelaccessor import *

class SyncImages(OpenStackSyncStep):
    provides=[Image]
    requested_interval=0
    observes=[Image]

    def sync_record(self, role):
        # do nothing
        pass
