import json
from django.core.management.base import BaseCommand
from announcements.models import Announcement

class Command(BaseCommand):
    help = "Update announcement titles based on JSON data (matched by ID)."

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, help="Path to the JSON file")

    def handle(self, *args, **kwargs):
        json_path = kwargs["json_path"]

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        updated = 0
        missing = 0
        skipped = 0

        for item in data:
            ann_id = item.get("id")
            new_title = item.get("title")
            pdf_name = item.get("pdf_name", "")

            if ann_id is None or new_title is None:
                self.stdout.write(self.style.WARNING(f"Skipping invalid item: {item}"))
                skipped += 1
                continue

            try:
                ann = Announcement.objects.get(id=ann_id)

                # 기존 제목과 다르면 경고 표시 (선택 사항)
                if ann.title != new_title:
                    self.stdout.write(self.style.WARNING(
                        f"ID {ann_id} - title changed from '{ann.title}' to '{new_title}'"
                    ))

                # 업데이트
                ann.title = new_title
                ann.pdf_name = pdf_name
                ann.save()
                updated += 1

            except Announcement.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"ID {ann_id} not found"))
                missing += 1

        self.stdout.write(self.style.SUCCESS(f"Updated: {updated} rows."))
        self.stdout.write(self.style.WARNING(f"Skipped: {skipped} rows."))
        self.stdout.write(self.style.ERROR(f"Missing: {missing} rows."))
