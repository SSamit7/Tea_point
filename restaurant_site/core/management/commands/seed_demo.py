from django.core.management.base import BaseCommand

from core.models import Table, RestaurantSettings


class Command(BaseCommand):
    help = "Create the restaurant settings row and numbered tables without adding demo menu items or prices."

    def add_arguments(self, parser):
        parser.add_argument('--tables', type=int, default=8, help='Number of tables to create (default: 8).')

    def handle(self, *args, **options):
        RestaurantSettings.load()
        count = max(1, options['tables'])
        for number in range(1, count + 1):
            table, created = Table.objects.get_or_create(number=number, defaults={'capacity': 4})
            if created:
                self.stdout.write(f'Created Table {number}')
        self.stdout.write(self.style.SUCCESS(
            f'Ready: tables 1–{count} exist. No sample menu items or prices were created.'
        ))
        self.stdout.write('Add your own categories and menu items from the logged-in admin dashboard.')
