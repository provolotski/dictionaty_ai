from django.core.management.base import BaseCommand
from ...services import DictionaryAPIClient

class Command(BaseCommand):
    help = 'Sync dictionaries with external API'

    def handle(self, *args, **options):
        if DictionaryAPIClient.sync_dictionaries():
            self.stdout.write(self.style.SUCCESS('Successfully synced dictionaries'))
        else:
            self.stdout.write(self.style.ERROR('Failed to sync dictionaries'))