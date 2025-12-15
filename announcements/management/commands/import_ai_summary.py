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

    def normalize_list_field(self, value, field_name="field"):
        """
        JSONField용 리스트 정규화
        - None → []
        - list → 그대로 반환
        - string (JSON 형태) → 파싱 후 list 반환
        - string (일반) → [string]
        - 기타 → [value]
        """
        if value is None:
            return []
        
        # 이미 리스트면 그대로 반환
        if isinstance(value, list):
            return value
        
        # 문자열인 경우
        if isinstance(value, str):
            # 빈 문자열
            if not value.strip():
                return []
            
            # JSON 배열 형태인지 확인 (시작이 [ 인 경우)
            if value.strip().startswith('['):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                    else:
                        # 파싱은 됐지만 리스트가 아닌 경우
                        self.stdout.write(
                            self.style.WARNING(
                                f'{field_name}: JSON 파싱 성공했으나 list가 아님 → 리스트로 변환 ({value[:50]})'
                            )
                        )
                        return [parsed]
                except json.JSONDecodeError:
                    # JSON 파싱 실패 - 일반 문자열로 취급
                    self.stdout.write(
                        self.style.WARNING(
                            f'{field_name}: JSON 파싱 실패 → 리스트로 변환 ({value[:50]})'
                        )
                    )
                    return [value]
            
            # JSON 형태가 아닌 일반 문자열
            return [value]
        
        # 숫자나 기타 타입
        return [value]

    def normalize_boolean(self, value):
        """
        BooleanField용 정규화
        - None/빈 값 → False
        - bool → 그대로
        - string → 파싱
        - int → bool 변환
        """
        if value is None or value == '':
            return False
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 't', 'y')
        
        if isinstance(value, int):
            return bool(value)
        
        return False

    def validate_housing_data(self, hi, index):
        """
        HousingInfo 데이터 검증
        """
        type_list = self.normalize_list_field(hi.get("type"), f"housing[{index}].type")
        house_type_list = self.normalize_list_field(hi.get("house_type"), f"housing[{index}].house_type")
        supply_list = self.normalize_list_field(hi.get("supply_households"), f"housing[{index}].supply_households")
        
        # 배열 길이 일치 검증
        lengths = [len(type_list), len(house_type_list), len(supply_list)]
        
        if len(set(lengths)) > 1:
            self.stdout.write(
                self.style.ERROR(
                    f"housing[{index}] ({hi.get('name')}): 배열 길이 불일치 - "
                    f"type({lengths[0]}), house_type({lengths[1]}), supply_households({lengths[2]})"
                )
            )
            # 최대 길이에 맞춰서 빈 값으로 채우기
            max_len = max(lengths)
            type_list.extend([''] * (max_len - len(type_list)))
            house_type_list.extend([''] * (max_len - len(house_type_list)))
            supply_list.extend([0] * (max_len - len(supply_list)))
        
        return type_list, house_type_list, supply_list

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
        error_count = 0

        for file_path in json_files:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"파일 로드: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"JSON 파싱 실패: {e}"))
                error_count += 1
                continue

            if not isinstance(data, dict):
                self.stdout.write(self.style.ERROR("JSON 형식 오류"))
                error_count += 1
                continue

            announcement_id = data.get("announcement_id")
            if announcement_id is None:
                self.stdout.write(self.style.ERROR(f"'announcement_id'가 없습니다."))
                error_count += 1
                continue

            try:
                announcement = Announcement.objects.get(id=announcement_id)
                self.stdout.write(f"✓ 기존 Announcement({announcement_id}) 업데이트")
            except Announcement.DoesNotExist:
                announcement = Announcement(id=announcement_id)
                self.stdout.write(f"✓ 새 Announcement({announcement_id}) 생성")

            try:
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
                    
                    # 기존 HousingInfo 삭제 (전체 교체 방식)
                    deleted_count = HousingInfo.objects.filter(announcement=announcement).count()
                    HousingInfo.objects.filter(announcement=announcement).delete()
                    self.stdout.write(f"  - 기존 HousingInfo {deleted_count}개 삭제")
                    
                    # HousingInfo 생성
                    housing_list = data.get("housing_info", [])
                    created_count = 0
                    
                    for idx, hi in enumerate(housing_list):
                        # 데이터 정규화 및 검증
                        type_list, house_type_list, supply_list = self.validate_housing_data(hi, idx)
                        
                        HousingInfo.objects.create(
                            announcement=announcement,
                            name=hi.get("name", ""),
                            address=hi.get("address", ""),
                            district=hi.get("district", ""),
                            total_households=hi.get("total_households"),
                            supply_households=supply_list,
                            type=type_list,
                            house_type=house_type_list,
                            elevator=self.normalize_boolean(hi.get("elevator")),
                            parking=hi.get("parking")
                        )
                        created_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(f"  - HousingInfo {created_count}개 생성"))

                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"처리 중 오류: {e}"))
                error_count += 1
                continue

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS(f"✓ 성공: {success_count}개"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"✗ 실패: {error_count}개"))
        self.stdout.write(self.style.SUCCESS(f"총 {success_count}개의 공고가 생성/업데이트되었습니다."))