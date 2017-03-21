from synchronizers.new_base.modelaccessor import *

def handle_container_on_metal(instance):
        print "MODEL POLICY: instance", instance, "handle container_on_metal"

        if instance.deleted:
            return

        if (instance.isolation in ["container"]) and (instance.slice.network not in ["host", "bridged"]):
            # Our current docker-on-metal network strategy requires that there be some
            # VM on the server that connects to the networks, so that
            # the containers can piggyback off of that configuration.
            if not Instance.objects.filter(slice_id=instance.slice.id, node_id=instance.node.id, isolation="vm").exists():
                flavors = Flavor.objects.filter(name="m1.small")
                if not flavors:
                    raise XOSConfigurationError("No m1.small flavor")

                images = Image.objects.filter(kind="vm")

                companion_instance = Instance(slice = instance.slice,
                                node = instance.node,
                                image = images[0],
                                creator = instance.creator,
                                deployment = instance.node.site_deployment.deployment,
                                flavor = flavors[0])
                companion_instance.save()

                print "MODEL POLICY: instance", instance, "created companion", companion_instance

        # Add the ports for the container
        for network in instance.slice.networks.all():
            # hmmm... The NAT ports never become ready, because sync_ports never
            # instantiates them. Need to think about this.
            print "MODEL POLICY: instance", instance, "handling network", network
            if (network.name.endswith("-nat")):
                continue

            if not Port.objects.filter(network_id=network.id, instance_id=instance.id).exists():
                port = Port(network = network, instance=instance)
                port.save()
                print "MODEL POLICY: instance", instance, "created port", port

def handle(instance):
    networks = [ns.network for ns in NetworkSlice.objects.filter(slice=instance.slice)]
    controller_networks = ControllerNetwork.objects.filter(controller=instance.node.site_deployment.controller)

    # a little clumsy because the API ORM doesn't support __in queries
    network_ids = [x.id for x in networks]
    controller_networks = [x for x in controller_networks if x.network.id in network_ids]

    for cn in controller_networks:
        if (cn.lazy_blocked):
                print "MODEL POLICY: instance", instance, "unblocking network", cn.network
		cn.lazy_blocked=False
		cn.backend_register = '{}'
		cn.save()

    if (instance.isolation in ["container", "container_vm"]):
        handle_container_on_metal(instance)
