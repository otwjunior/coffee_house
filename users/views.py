# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseBadRequest

from .serializers import UserSerializer, LoginSerializer, RegisterSerializer


# ───── API VIEWS ─────

class MeView(APIView):
    """GET /api/auth/me/ → current user profile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class OnboardingAPI(APIView):
    """GET /api/auth/onboarding/ → profile + onboarding flag
       PATCH /api/auth/onboarding/ → update full_name, role"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = UserSerializer(request.user).data
        data['onboarding_needed'] = not bool(request.user.full_name.strip())
        return Response(data)

    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "profile saved",
            "user": UserSerializer(request.user).data
        })


class RegisterAPI(APIView):
    """POST /api/auth/register/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = Token.objects.create(user=user)
        return Response({
            "token": token.key,
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginAPI(APIView):
    """POST /api/auth/login/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)  # for session fallback
        return Response({
            "token": token.key,
            "user": UserSerializer(user).data
        })


# ───── HTML FALLBACK VIEWS (Optional) ─────

def login_view(request):
    """
    GET  → show login.html
    POST → authenticate via email/password → redirect or error
    """
    if request.method == "GET":
        return render(request, 'users/login.html')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            return HttpResponseBadRequest("Email and password required.")

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            return render(request, 'users/login.html', {
                'error': 'Invalid email or password.'
            }, status=400)    

    return HttpResponseBadRequest("Method not allowed.")
    next_url = request.GET.get('next', '/')
    return redirect(next_url)
# Logout
def logout_view(request):
    logout(request)
    return redirect('users:login-page')  # or homepage