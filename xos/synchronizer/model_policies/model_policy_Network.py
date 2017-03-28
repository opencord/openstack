from synchronizers.new_base.modelaccessor import *
from collections import defaultdict

def handle(network):
        print "MODEL POLICY: network", network

	# network controllers are not visible to users. We must ensure
	# networks are deployed at all deploymets available to their slices.

        # TODO: should be possible to query only the ControllerSlice objects
        #       associated with network.owner rather than iterating through
        #       all ControllerSlice.

	slice_controllers = ControllerSlice.objects.all()
	slice_deploy_lookup = defaultdict(list)
	for slice_controller in slice_controllers:
		slice_deploy_lookup[slice_controller.slice.id].append(slice_controller.controller)

	network_controllers = ControllerNetwork.objects.all()
	network_deploy_lookup = defaultdict(list)
	for network_controller in network_controllers:
		network_deploy_lookup[network_controller.network.id].append(network_controller.controller.id)

	expected_controllers = slice_deploy_lookup[network.owner.id]
	for expected_controller in expected_controllers:
		if network.id not in network_deploy_lookup or expected_controller.id not in network_deploy_lookup[network.id]:
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
