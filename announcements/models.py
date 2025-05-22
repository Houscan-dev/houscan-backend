from django.db import models

# 리스트
class Announcement(models.Model):
    file_name     = models.CharField(max_length=255, unique=True)
    posted_date   = models.DateField()
    status        = models.CharField(
        max_length=10,
        choices=[('upcoming','모집예정'),
                 ('open','모집중'),
                 ('closed','모집마감')]
    )
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.file_name} · {self.status}"
