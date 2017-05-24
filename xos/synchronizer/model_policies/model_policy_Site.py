from synchronizers.new_base.modelaccessor import *

def handle(site):
    # site = Site.get(site_id)
    # make sure site has a ControllerSite record for each controller
    ctrl_sites = ControllerSite.objects.filter(site_id=site.id)
    existing_controllers = [cs.controller for cs in ctrl_sites]
    existing_controller_ids = [c.id for c in existing_controllers]

    all_controllers = Controller.objects.all()
    for ctrl in all_controllers:
        if ctrl.id not in existing_controller_ids:
            ctrl_site = ControllerSite(controller=ctrl, site=site)
            ctrl_site.save() 
