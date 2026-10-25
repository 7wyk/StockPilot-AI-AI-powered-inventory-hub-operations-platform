from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    RegistrationSerializer,
    StockPilotTokenObtainPairSerializer,
    UserIdentitySerializer,
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"user": UserIdentitySerializer(user).data}, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = StockPilotTokenObtainPairSerializer


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        raw_token = request.data.get("refresh")
        if not raw_token:
            return Response({"detail": "A refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(raw_token).blacklist()
        except TokenError:
            return Response({"detail": "The refresh token is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserIdentitySerializer(request.user).data)
