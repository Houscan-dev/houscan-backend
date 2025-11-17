import json
from django.core.management.base import BaseCommand
from announcements.models import Announcement

class Command(BaseCommand):
    help = "Update announcement titles based on JSON data (matched by pdf_name)."

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, help="Path to the JSON file")

    def handle(self, *args, **kwargs):
        json_path = kwargs["json_path"]

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        updated = 0
        missing = 0

        for item in data:
            pdf = item.get("pdf_name")
            title = item.get("title")

            qs = Announcement.objects.filter(pdf_name=pdf)
            if qs.exists():
                qs.update(title=title)
                updated += 1
            else:
                missing += 1
                self.stdout.write(self.style.WARNING(f"Not found: {pdf}"))

        self.stdout.write(self.style.SUCCESS(f"Updated: {updated} rows."))
        self.stdout.write(self.style.ERROR(f"Missing: {missing} rows."))
