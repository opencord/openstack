#!/usr/bin/env python
import os
import argparse
import sys

sys.path.append('/opt/xos')
from xosconfig import Config

config_file = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + '/openstack_config.yaml')
Config.init(config_file, 'synchronizer-config-schema.yaml')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xos.settings")
from xos.logger import Logger, logging, logger
import time

from synchronizers.new_base.modelaccessor import *
from synchronizers.new_base.backend import Backend
from synchronizers.new_base.event_loop import set_driver

logger = Logger(level=logging.INFO)

# TODO: These two lines are the only difference between this file and
#       new_base/openstack-synchronizer.py. Reconcile these.
# set the driver.
from synchronizers.openstack.driver import OpenStackDriver
set_driver(OpenStackDriver())


def main():
    models_active = False
    wait = False
    while not models_active:
        try:
            _ = Instance.objects.first()
            _ = NetworkTemplate.objects.first()
            models_active = True
        except Exception,e:
            logger.info(str(e))
            logger.info('Waiting for data model to come up before starting...')
            time.sleep(10)
            wait = True

    if (wait):
        time.sleep(60) # Safety factor, seeing that we stumbled waiting for the data model to come up.
    backend = Backend()
    backend.run()    

if __name__ == '__main__':
    
    main() 
