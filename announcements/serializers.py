from rest_framework import serializers
from .models import Announcement, HousingInfo

class AnnListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'posted_date', 'status', 'updated_at','pdf_name']
 
class HousingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingInfo
        fields = [
            'id',  # 공고 내 주택 ID
            'name',
            'address',
            'total_households',
            'supply_households',
            'type',
            'house_type',
            'elevator',
            'parking',
        ]

class AnnouncementDetailSerializer(serializers.ModelSerializer):
    housing_info_list = HousingInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Announcement
        fields = '__all__'

class HousingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingInfo
        fields = '__all__'
        