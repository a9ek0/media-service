from django.core.management.base import BaseCommand
from news.models import ContentItem


class Command(BaseCommand):
    help = "Publishes scheduled content"

    def handle(self, *args, **options):
        count = ContentItem.publish_scheduled()
        if count:
            self.stdout.write(self.style.SUCCESS(f"Successfully published {count} scheduled items"))
        else:
            self.stdout.write("No scheduled items to publish")
