from synchronizers.new_base.modelaccessor import *
from synchronizers.new_base.policy import Policy

class ImagePolicy(Policy):
    model_name = "Image"

    def handle_create(self, image):
        return self.handle_update(image)

    def handle_update(self, image):
        if (image.kind == "container"):
            # container images do not get instantiated
            return

        controller_images = ControllerImages.objects.filter(image_id=image.id)
        existing_controllers = [cs.controller for cs in controller_images]
        existing_controller_ids = [c.id for c in existing_controllers]

        all_controllers = Controller.objects.all()
        for controller in all_controllers:
            if controller.id not in existing_controller_ids:
                sd = ControllerImages(image=image, controller=controller)
                sd.save()

