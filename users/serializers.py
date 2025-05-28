from rest_framework import serializers
from .models import User
import re


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['nickname', 'email', 'password', 'password2']  

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value
    
    # 비밀번호 복잡도 검사 + password2 일치 확인
    def validate(self, data):
        password = data.get('password')
        password2 = data.get('password2')

        if password != password2:
            raise serializers.ValidationError({"password2": "비밀번호가 일치하지 않습니다."})

        # 비밀번호 복잡도 검사
        if len(password) < 8:
            raise serializers.ValidationError({"password": "비밀번호는 8자리 이상이어야 합니다."})
        if not re.search(r"[A-Za-z]", password):
            raise serializers.ValidationError({"password": "영문자가 포함되어야 합니다."})
        if not re.search(r"\d", password):
            raise serializers.ValidationError({"password": "숫자가 포함되어야 합니다."})
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise serializers.ValidationError({"password": "특수문자가 포함되어야 합니다."})

        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            nickname=validated_data['nickname'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    
class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

class MySerializer(serializers.ModelSerializer): #정보확인
    class Meta:
        model = User
        fields = ['id','nickname', 'email']
        read_only_fields = ['email'] #아이디변경불가

class PwChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("현재 비밀번호가 일치하지 않습니다.")
        return value
    def validate(self, data):
        pwd = data.get('new_password')

        if len(pwd) < 8:
            raise serializers.ValidationError({"password": "비밀번호는 8자리 이상이어야 합니다."})
        if not re.search(r"[A-Za-z]", pwd):
            raise serializers.ValidationError({"password": "영문자가 포함되어야 합니다."})
        if not re.search(r"\d", pwd):
            raise serializers.ValidationError({"password": "숫자가 포함되어야 합니다."})
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
            raise serializers.ValidationError({"password": "특수문자가 포함되어야 합니다."})

        return data
