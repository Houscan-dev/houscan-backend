from rest_framework import serializers
from .models import Announcement

class AnnListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'file_name', 'posted_date', 'status', 'updated_at']
 
#class AnnDetailSerializer(serializers.ModelSerializer):
#    pass