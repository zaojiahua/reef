from django.apps import AppConfig


class Apiv1Config(AppConfig):
    name = 'apiv1'

    def ready(self):
        # signals are imported, so that they are defined and can be used
        import apiv1.module.rds.signal
        import apiv1.module.tboard.signal
        import apiv1.module.device.signal
        import apiv1.module.job.signal
        import apiv1.module.system.signal
        import apiv1.module.resource.signal
        import apiv1.module.abnormity.signal
