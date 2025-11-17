# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.middleware.csrf import get_token

from .models import User
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    StaffUpdateSerializer,
)


# ====================== API VIEWS (Mobile + Web App) ======================
class MeView(APIView):
    """GET /api/auth/me/ → current logged-in user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)


class RegisterAPI(APIView):
    """POST /api/auth/register/ → create account (customers only)"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "csrf_token": get_token(request),  # for session fallback
        }, status=status.HTTP_201_CREATED)


class LoginAPI(APIView):
    """POST /api/auth/login/ → JWT + session login"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        login(request, user)  # keeps session for DRF browsable API
        refresh = RefreshToken.for_user(user)

        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "csrf_token": get_token(request),
        })


class ProfileUpdateAPI(APIView):
    """PATCH /api/auth/profile/ → update name, phone, favourite drink"""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class StaffManagementAPI(APIView):
    """PATCH /api/auth/staff/<id>/ → only managers/owners can update role"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.is_manager and not request.user.is_owner:
            return Response({"detail": "Permission denied."}, status=403)

        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        serializer = StaffUpdateSerializer(
            target_user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserSerializer(target_user).data)


class LogoutAPI(APIView):
    """POST /api/auth/logout/ → blacklist token (optional) + clear session"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except:
            pass
        request.user.auth_token.delete()  # if using TokenAuth too
        from django.contrib.auth import logout
        logout(request)
        return Response({"detail": "Logged out successfully."})