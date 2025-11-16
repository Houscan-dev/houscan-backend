from django.contrib import admin
from .models import Announcement, HousingInfo

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('id','title','announcement_date','status','updated_at')
    list_filter  = ('status',)
    search_fields = ('title',)

@admin.register(HousingInfo)
class HousingInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'house_type', 'announcement')
    list_filter = ('announcement',)
    search_fields = ('name',)
