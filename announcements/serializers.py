from rest_framework import serializers
from .models import Announcement

class AnnListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'posted_date', 'status', 'updated_at']
 