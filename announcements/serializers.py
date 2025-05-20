from rest_framework import serializers
from .models import Announcement

class AnnListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'file_name', 'posted_date', 'status', 'updated_at']
 
class AnnDetailSerializer(serializers.Serializer):
    criteria         = serializers.JSONField()
    schedule         = serializers.JSONField()
    precautions      = serializers.JSONField()
    priority_score   = serializers.JSONField()
    residence_period = serializers.JSONField()
    housing_info     = serializers.JSONField()

