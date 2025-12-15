# announcements/management/commands/import_ai_summary.py
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from announcements.models import Announcement, HousingInfo

class Command(BaseCommand):
    help = 'AI가 생성한 JSON 파일을 ai_summary_json 필드에 저장하고, HousingInfo는 DB에 생성'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help="JSON 파일 또는 JSON 폴더 경로")

    def handle(self, *args, **options):
        path = options['path']

        if os.path.isdir(path):
            json_files = [
                os.path.join(path, f)
                for f in os.listdir(path)
                if f.endswith(".json")
            ]
            if not json_files:
                self.stdout.write(self.style.ERROR("폴더 안에 JSON 파일이 없습니다."))
                return
            self.stdout.write(f"총 {len(json_files)}개의 JSON 파일 로드를 시작합니다...")
        else:
            json_files = [path]

        success_count = 0

        for file_path in json_files:
            self.stdout.write(f"파일 로드: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"JSON 파싱 실패: {e}"))
                continue

            if not isinstance(data, dict):
                self.stdout.write(self.style.ERROR("JSON 형식 오류"))
                continue

            announcement_id = data.get("announcement_id")
            if announcement_id is None:
                self.stdout.write(self.style.ERROR(f"{file_path}: 'announcement_id'가 없습니다."))
                continue

            try:
                announcement = Announcement.objects.get(id=announcement_id)
                self.stdout.write(f"기존 Announcement({announcement_id}) 업데이트...")
            except Announcement.DoesNotExist:
                announcement = Announcement(id=announcement_id)
                self.stdout.write(f"새 Announcement({announcement_id}) 생성...")

            with transaction.atomic():
                # ai_summary_json에 housing_info 제외하고 저장
                ai_summary_copy = dict(data)
                ai_summary_copy.pop("housing_info", None)
                announcement.ai_summary_json = ai_summary_copy

                # 기본 필드들
                schedule = data.get("application_schedule", {})
                announcement.announcement_date = schedule.get("announcement_date", "")
                announcement.title = data.get("title", "")
                announcement.status = data.get("status", "closed")
                
                announcement.save()
                HousingInfo.objects.filter(announcement=announcement).delete()
                # HousingInfo 생성 (중복 방지)
                housing_list = data.get("housing_info", [])
                for hi in housing_list:
                    if not HousingInfo.objects.filter(announcement=announcement, name=hi.get("name")).exists():
                        HousingInfo.objects.create(
                            announcement=announcement,
                            name=hi.get("name", ""),
                            address=hi.get("address", ""),
                            district=hi.get("district", ""),
                            total_households=hi.get("total_households"),
                            supply_households=hi.get("supply_households"),
                            type=hi.get("type"),
                            house_type=hi.get("house_type"),
                            elevator=hi.get("elevator"),   
                            parking=hi.get("parking")
                        )

            success_count += 1

        self.stdout.write(self.style.SUCCESS(f"총 {success_count}개의 공고가 생성/업데이트되었습니다."))


