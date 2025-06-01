from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import os
import re
from django.utils.text import slugify

def get_upload_path(instance, filename):
    """파일 업로드 경로를 생성하는 함수"""
    # 파일 확장자 추출
    ext = os.path.splitext(filename)[1]
    
    # 공고 제목에서 안전한 파일명 생성
    # 1. 한글, 영문, 숫자만 남기고 제거
    safe_title = re.sub(r'[^\w\s가-힣]', '', instance.announcement.title)
    # 2. 공백을 언더스코어로 변경
    safe_title = safe_title.replace(' ', '_')
    # 3. 파일명 길이 제한 (100자)
    safe_title = safe_title[:100]
    
    # 문서 타입을 영문으로 변환
    doc_type_map = {
        'schedule': 'schedule',
        'criteria': 'criteria',
        'housing_info': 'housing_info',
        'precautions': 'precautions',
        'priority_score': 'priority_score',
        'residence_period': 'residence_period'
    }
    doc_type = doc_type_map.get(instance.doc_type, instance.doc_type)
    
    # 새 파일명 생성 (공고ID_안전한제목_문서타입.확장자)
    new_filename = f"{instance.announcement.id}_{safe_title}_{doc_type}{ext}"
    
    # 경로 생성
    return os.path.join('announcements', doc_type, new_filename)

class Announcement(models.Model):
    title       = models.CharField(max_length=255)
    posted_date   = models.DateField()
    status        = models.CharField(
        max_length=10,
        choices=[('upcoming','모집예정'),
                 ('open','모집중'),
                 ('closed','모집마감')]
    )
    updated_at    = models.DateTimeField(auto_now=True)
    pdf_name = models.CharField(max_length=255, null=True, blank=True)
    def __str__(self):
        return f"{self.title} ({self.status})"
    
class AnnouncementDocument(models.Model):
    ANNOUNCE_TYPES = [
        ('schedule','모집 일정'),
        ('criteria','지원 자격'),
        ('housing_info','주택 정보'),
        ('precautions','유의 사항'),
        ('priority_score','가점사항 및 점수'),
        ('residence_period','거주 기간'),
    ]
    announcement = models.ForeignKey(Announcement, related_name='documents', on_delete=models.CASCADE)
    doc_type     = models.CharField(max_length=20, choices=ANNOUNCE_TYPES)
    data_file    = models.FileField(upload_to=get_upload_path)
    uploaded_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('announcement','doc_type')

    def __str__(self):
        return f"{self.announcement_id} – {self.doc_type}"
    

class HousingInfo(models.Model):
    announcement = models.ForeignKey(Announcement, related_name='housing_info_list', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    total_households = models.TextField(null=True, blank=True)
    supply_households = models.TextField(null=True, blank=True)
    type = models.TextField( null=True, blank=True)
    house_type = models.TextField( null=True, blank=True)
    elevator = models.CharField(max_length=100, null=True, blank=True)
    parking = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} – {self.house_type}"

class HousingEligibilityAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='eligibility_analyses')
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='eligibility_analyses')
    is_eligible = models.BooleanField(default=False)
    priority = models.CharField(max_length=100, default="")
    reasons = models.JSONField(default=list)  # 자격 판단 사유 리스트를 저장
    analyzed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'announcement')
        indexes = [
            models.Index(fields=['user', 'announcement']),
            models.Index(fields=['is_eligible']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.announcement.title} ({self.priority})"
