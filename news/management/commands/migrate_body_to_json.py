from django.core.management.base import BaseCommand
from news.models import Post


class Command(BaseCommand):
    help = "Convert body text to body_json if empty"

    def handle(self, *args, **options):
        qs = Post.objects.filter(body_json__isnull=True)
        for p in qs:
            text = p.body or ""
            block = {"type": "paragraph", "data": {"text": text}}
            p.body_json = [block]
            p.save(update_fields=["body_json"])
            self.stdout.write(f"Converted post {p.pk}")
