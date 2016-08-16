#!/bin/bash

export XOS_DIR=/opt/xos
python $XOS_DIR/synchronizers/openstack/xos-synchronizer.py -C $XOS_DIR/synchronizers/openstack/openstack_synchronizer_config
