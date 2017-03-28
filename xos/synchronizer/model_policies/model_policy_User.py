from synchronizers.new_base.modelaccessor import *

def handle(user):
    controller_users = ControllerUser.objects.filter(user_id=user.id)
    existing_controllers = [cu.controller for cu in controller_users]
    existing_controller_ids = [c.id for c in existing_controllers]
    all_controllers = Controller.objects.all()
    for controller in all_controllers:
        if controller.id not in existing_controller_ids:
            ctrl_user = ControllerUser(controller=controller, user=user)
            ctrl_user.save()  

