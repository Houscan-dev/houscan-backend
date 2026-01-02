from rest_framework import serializers
from .models import User
import re
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.conf import settings
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str



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
    
# 비밀번호 재설정
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("해당 이메일로 가입된 계정이 없습니다.")
        return value

    def save(self):
        user = User.objects.get(email=self.validated_data["email"])
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        reset_link = (
            f"https://houscan.kr/reset-password?"
            f"uid={uid}&token={token}"
        )

        send_mail(
            subject="[Houscan] 비밀번호 재설정 안내",
            message=(
                "안녕하세요, Houscan입니다.\n\n"
                "아래 링크를 클릭해 비밀번호를 재설정해주세요.\n\n"
                f"{reset_link}\n\n"
                "본인이 요청하지 않았다면 이 메일을 무시해주세요."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, data):
        try:
            uid = force_str(urlsafe_base64_decode(data["uid"]))
            user = User.objects.get(pk=uid)
        except:
            raise serializers.ValidationError("유효하지 않은 사용자입니다.")

        token = data["token"]
        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError("토큰이 만료되었거나 유효하지 않습니다.")

        pwd = data["new_password"]

        if len(pwd) < 8:
            raise serializers.ValidationError("비밀번호는 8자리 이상이어야 합니다.")
        if not re.search(r"[A-Za-z]", pwd):
            raise serializers.ValidationError("영문자가 포함되어야 합니다.")
        if not re.search(r"\d", pwd):
            raise serializers.ValidationError("숫자가 포함되어야 합니다.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
            raise serializers.ValidationError("특수문자가 포함되어야 합니다.")

        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()