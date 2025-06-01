from rest_framework import serializers
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ['user', 'created_at','is_eligible', 'priority_info']
    
    def get_age(self, obj):
        return obj.age

    def validate_birth_date(self, value):
        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("생년월일은 6자리 숫자여야 합니다. ex) 920417")
        return value
    
    def validate_total_assets(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError("총 자산은 숫자로 입력해야 합니다.")
        return value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        if request and request.method == 'POST':
            for field in self.fields:
                if field not in self.Meta.read_only_fields + ['age']:
                    self.fields[field].required = True
        else:
            # PATCH - 부분 수정 허용
            for field in self.fields:
                self.fields[field].required = False