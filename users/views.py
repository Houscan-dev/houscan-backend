import jwt
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer   
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from .serializers import *
from django.conf import settings
SECRET_KEY = settings.SECRET_KEY

# jwt 토근 인증 확인용 뷰셋
# Header - Authorization : Bearer <발급받은토큰>
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = SignupSerializer

class SignupAPIView(APIView):
    renderer_classes = [JSONRenderer]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = TokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            return Response(
                {
                    "user": serializer.data,
                    "message": "회원가입이 성공적으로 완료되었습니다.",
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                }, status=status.HTTP_201_CREATED)
        
        first_field = next(iter(serializer.errors))
        first_error = serializer.errors[first_field][0]
        # raise ValidationError로 던지면 custom_exception_handler가 message 키로 통일
        raise ValidationError(first_error)
        
    
class AuthAPIView(APIView):
    renderer_classes = [JSONRenderer]
    permission_classes = []

    def get_permissions(self):
        if self.request.method == "POST":
            # 로그인 시에는 누구나 접근 가능
            return [AllowAny()]
        # 그 외(GET, DELETE)에는 인증된 사용자만
        return [IsAuthenticated()]
    
    # 유저 정보 확인
    def get(self, request):
        serializer = SignupSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # 로그인
    def post(self, request):
    	# 유저 인증
        user = authenticate(
            username=request.data.get("email"), 
            password=request.data.get("password")
        )
        # 회원가입 안된 유저일 때
        if not user:
            raise ValidationError("이메일 또는 비밀번호가 일치하지 않습니다.")

        serializer = SignupSerializer(user)
        token = TokenObtainPairSerializer.get_token(user)
        refresh_token = str(token)
        access_token = str(token.access_token)
        return Response(
            {
                "user": serializer.data,
                "message": "로그인 성공!",
                "token": {
                    "access": access_token,
                    "refresh": refresh_token,
                },
            }, status=status.HTTP_200_OK
        )
    
    #로그아웃
    def delete(self, request):
        return Response({"message": "로그아웃되었습니다. 토큰을 삭제해주세요."}, status=status.HTTP_202_ACCEPTED)


class DeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        user = request.user
        user.delete()
        return Response({"message": "회원 탈퇴가 완료되었습니다."}, status=status.HTTP_200_OK)


class MyAPIView(APIView):
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = MySerializer(user)
        return Response(serializer.date, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = MySerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        first_key = next(iter(serializer.errors))
        first_err = serializer.errors[first_key][0]
        raise ValidationError(first_err)
    
class PwChangeAPIView(APIView):
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PwChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "비밀번호가 성공적으로 변경되었습니다."}, status=status.HTTP_200_OK)
        
        first_key = next(iter(serializer.errors))
        first_err = serializer.errors[first_key][0]
        raise ValidationError(first_err)