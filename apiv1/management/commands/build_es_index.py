from django.core.management import CommandParser
from django_elasticsearch_dsl.management.commands.search_index import Command as ES_Command
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Index


class Command(ES_Command):
    """
    扩展原有command，方便部署
    documents可以registry多个index，此command create只能传一个index，如需多个分多次即可
    """
    def add_arguments(self, parser: CommandParser):
        parser.add_argument('-c', '--create',
                            help='创建索引，如果存在则不创建',
                            default='rds_logs')
        parser.add_argument('-f', '--force',
                            help='强制创建, 注意: 使用此选项如果索引存在会删除再重建',
                            action='store_true',
                            default=False)

    def handle(self, *args, **options):
        index_name = 'rds_logs' if 'create' not in options \
            else options.get('create')
        force = options.get('force')

        models = self._get_models('')

        document_index = [index._name for index in registry.get_indices(models)]
        if index_name not in document_index:
            self.stdout.write(f'Input undefined index {index_name}')

        if not Index(index_name).exists():
            for index in registry.get_indices(models):
                if index_name == index._name:
                    self.stdout.write(f'Creating index {index_name}')
                    index.create()
            return

        else:
            if not force:
                self.stdout.write(f'Index {index_name} already exist')
                return

            response = input(
                f"Are you sure you want to delete "
                f"the {index_name} index and recreate ? [y/N]: ")
            if response.lower() != 'y':
                self.stdout.write('Aborted')
                return False

            for index in registry.get_indices(models):
                if index_name == index._name:
                    self.stdout.write(f'Deleting index {index_name}')
                    index.delete(ignore=404)

            for index in registry.get_indices(models):
                if index_name == index._name:
                    self.stdout.write(f'Creating index {index_name}')
                    index.create()

        return
