from django.contrib import admin
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('file_name','posted_date','status','updated_at')
    list_filter  = ('status','posted_date')
    search_fields = ('file_name',)
