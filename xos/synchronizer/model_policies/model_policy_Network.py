from synchronizers.new_base.modelaccessor import *
from collections import defaultdict

def handle(network):
        print "MODEL POLICY: network", network

        # For simplicity, let's assume that a network gets deployed on all controllers.
        expected_controllers =  Controller.objects.all()

        existing_controllers = []
        for cn in ControllerNetwork.objects.all():
            if cn.network.id == network.id:
                existing_controllers.append(cn.controller)

        existing_controller_ids = [c.id for c in existing_controllers]

        for expected_controller in expected_controllers:
            if expected_controller.id not in existing_controller_ids:
                        lazy_blocked=True

                        # check and see if some instance already exists
                        for networkslice in network.networkslices.all():
                            found = False
                            for instance in networkslice.slice.instances.all():
                               if instance.node.site_deployment.controller.id == expected_controller.id:
                                   found = True
                            if found:
                               print "MODEL_POLICY: network, setting lazy_blocked to false because instance on controller already exists"
                               lazy_blocked=False

			nd = ControllerNetwork(network=network, controller=expected_controller, lazy_blocked=lazy_blocked)
                        print "MODEL POLICY: network", network, "create ControllerNetwork", nd, "lazy_blocked", lazy_blocked
                        if network.subnet:
                            # XXX: Possibly unpredictable behavior if there is
                            # more than one ControllerNetwork and the subnet
                            # is specified.
                            nd.subnet = network.subnet
			nd.save()
