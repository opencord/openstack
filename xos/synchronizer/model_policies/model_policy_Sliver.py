from synchronizers.new_base.modelaccessor import *

def handle(instance):
    networks = [ns.network for ns in NetworkSlice.objects.filter(slice_id=instance.slice.id)]
    network_ids = [x.id for x in networks]
    controller_networks = ControllerNetwork.objects.filter(controller_id=instance.node.site_deployment.controller.id)
    controller_networks = [x for x in controller_networks if x.network_id in network_ids]

    for cn in controller_networks:
        if (cn.lazy_blocked):	
		cn.lazy_blocked=False
		cn.backend_register = '{}'
		cn.save()
