import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from announcements.models import Announcement, HousingInfo

class Command(BaseCommand):
    help = 'AI가 생성한 JSON 파일(단일 JSON) 하나 또는 폴더 전체를 처리하여 Announcement/HousingInfo 생성 및 업데이트'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help="JSON 파일 또는 JSON 폴더 경로")

    def handle(self, *args, **options):
        path = options['path']

        # 폴더인지 파일인지 판별
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

        # 모든 JSON 파일 반복 처리
        for file_path in json_files:
            self.stdout.write(f"파일 로드: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"JSON 파싱 실패: {e}"))
                continue

            if not isinstance(data, dict):
                self.stdout.write(self.style.ERROR("JSON 형식 오류: 단일 객체가 아닙니다."))
                continue

            announcement_id = data.get("announcement_id")
            if announcement_id is None:
                self.stdout.write(self.style.ERROR(f"{file_path}: 'announcement_id'가 없습니다."))
                continue

            # DB 조회 or 생성
            try:
                announcement = Announcement.objects.get(id=announcement_id)
                is_new = False
                self.stdout.write(f"기존 Announcement({announcement_id}) 업데이트...")
            except Announcement.DoesNotExist:
                announcement = Announcement(id=announcement_id)
                is_new = True
                self.stdout.write(f"새 Announcement({announcement_id}) 생성...")

            # 트랜잭션 처리
            with transaction.atomic():
                announcement.application_eligibility = data.get("application_eligibility")
                announcement.residence_period = data.get("residence_period")
                announcement.precautions = data.get("precautions")

                schedule = data.get("application_schedule", {})
                announcement.announcement_date = schedule.get("announcement_date")
                announcement.online_application_period = schedule.get("online_application_period")
                announcement.document_submission_period = schedule.get("document_submission_period")
                announcement.inspection_period = schedule.get("inspection_period")
                announcement.winner_announcement = schedule.get("winner_announcement")
                announcement.contract_period = schedule.get("contract_period")
                announcement.move_in_period = schedule.get("move_in_period")

                announcement.save()

                # HousingInfo 업데이트
                HousingInfo.objects.filter(announcement=announcement).delete()

                for h in data.get("housing_info", []):
                    HousingInfo.objects.create(
                        announcement=announcement,
                        name=h.get("name"),
                        address=h.get("address"),
                        district=h.get("district"),
                        type=h.get("type"),
                        total_households=h.get("total_households"),
                        supply_households=h.get("supply_households"),
                        house_type=h.get("house_type"),
                        parking=h.get("parking"),
                        elevator=h.get("elevator"),
                    )

            success_count += 1

        self.stdout.write(self.style.SUCCESS(f"총 {success_count}개의 공고가 생성/업데이트되었습니다."))
