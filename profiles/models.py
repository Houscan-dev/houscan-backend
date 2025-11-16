from django.db import models
from django.conf import settings
from datetime import datetime, date
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    birth_date = models.CharField(max_length=6)
    gender = models.CharField(max_length=1, choices=[('M', '남성'), ('F', '여성')])
    university = models.BooleanField() 
    graduate = models.BooleanField()
    employed = models.BooleanField()
    job_seeker = models.BooleanField()
    welfare_receipient = models.BooleanField()
    parents_own_house = models.BooleanField()
    disability_in_family = models.BooleanField()
    subscription_account = models.IntegerField()
    total_assets = models.BigIntegerField()
    car_value = models.BigIntegerField()
    income_range = models.CharField(max_length=20, choices=[('100% 이하', '100% 이하'),('50% 이하', '50% 이하')])
    is_eligible = models.BooleanField(null=True, blank=True)
    priority_info = models.JSONField(null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)

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

@receiver(post_save, sender=Profile)
def analyze_eligibility(sender, instance, created, **kwargs):
    from profiles.tasks import analyze_user_eligibility_task
    analyze_user_eligibility_task.apply_async(args=[str(instance.user.id)], queue='profile')
    