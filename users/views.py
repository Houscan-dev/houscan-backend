import jwt
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
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # jwt 토큰 접근
            token = TokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            return Response(
                {
                    "user": serializer.data,
                    "message": "register successs",
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AuthAPIView(APIView):
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
        # 이미 회원가입 된 유저일 때
        if user is not None:
            serializer = SignupSerializer(user)
            # jwt 토큰 접근
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
                },
                status=status.HTTP_200_OK,
            )
        return Response({"message": "이메일 또는 비밀번호가 일치하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
    
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = MySerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        print("PATCH 요청 도착")
        serializer = MySerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PwChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PwChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "비밀번호가 성공적으로 변경되었습니다."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
