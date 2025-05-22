from django.contrib import admin
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('id','title','posted_date','status','updated_at')
    list_filter  = ('status',)
    search_fields = ('title',)
