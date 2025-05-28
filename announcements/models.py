from django.db import models

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
    data_file    = models.FileField(upload_to='announcements/%(doc_type)s/')
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
    total_households = models.CharField(max_length=100, null=True, blank=True)
    supply_households = models.CharField(max_length=100, null=True, blank=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    house_type = models.CharField(max_length=100, null=True, blank=True)
    elevator = models.CharField(max_length=100, null=True, blank=True)
    parking = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} – {self.house_type}"
