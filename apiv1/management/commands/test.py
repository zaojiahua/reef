from django.core.management.commands.test import Command as TestCommand


class Command(TestCommand):
    def handle(self, *test_labels, **options):
        if len(test_labels) == 0:
            test_labels = (
                'apiv1.module.device.tests',
                'apiv1.module.system.tests',
                'apiv1.module.tboard.tests',
                'apiv1.module.rds.tests',
                'apiv1.module.job.tests',
                'apiv1.module.search.tests',
                'apiv1.module.user.tests'
            )
        return super(Command, self).handle(*test_labels, **options)
