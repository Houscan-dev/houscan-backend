from django.db import models
from django.conf import settings
from datetime import datetime, date
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    birth_date = models.CharField(max_length=6)
    gender = models.CharField(max_length=1, choices=[('M', '남성'), ('F', '여성')])
    university = models.BooleanField() 
    graduate = models.BooleanField()
    employed = models.BooleanField()
    job_seeker = models.BooleanField()
    is_married = models.BooleanField(null=True, blank=True)
    residence = models.CharField(max_length=4, null=True, blank=True)
    welfare_receipient = models.BooleanField()
    parents_own_house = models.BooleanField()
    disability_in_family = models.BooleanField()
    subscription_account = models.IntegerField()
    total_assets = models.BigIntegerField()
    car_value = models.BigIntegerField()
    income_range = models.CharField(max_length=20, choices=[('100% 이하', '100% 이하'),('50% 이하', '50% 이하')])
    is_eligible = models.BooleanField(null=True, blank=True)
    priority_info = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    eligibility_status = models.CharField(
        max_length=20,
        choices=[
            ('idle', '대기'),
            ('running', '분석중'),
            ('done', '완료'),
            ('error', '실패'),
        ],
        default='idle'
    )
    eligibility_result = models.JSONField(
        null=True,
        blank=True
    )
    @property
    def age(self):
        try:
            birth = datetime.strptime(self.birth_date, "%y%m%d").date()
            today = date.today()
            return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except:
            return None

    def __str__(self):
        return f"{self.user.email}'s profile"