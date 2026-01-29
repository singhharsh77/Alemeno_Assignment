from django.core.management.base import BaseCommand
from core.tasks import ingest_customer_data, ingest_loan_data

class Command(BaseCommand):
    help = 'Trigger ingestion of customer and loan data'

    def handle(self, *args, **options):
        self.stdout.write('Triggering customer ingestion task...')
        ingest_customer_data.delay()
        self.stdout.write('Triggering loan ingestion task...')
        ingest_loan_data.delay()
        self.stdout.write(self.style.SUCCESS('Ingestion tasks triggered successfully'))
