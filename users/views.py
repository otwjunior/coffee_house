# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import UserSerializer
from django.contrib.auth import authenticate, login
from django.http import  HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
# ───── API ─────
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(UserSerializer(request.user).data)

class OnboardingAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data = UserSerializer(request.user).data
        data['onboarding_needed'] = not bool(request.user.full_name.strip())
        return Response(data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "profile saved",
            "user": UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)

# ───── HTML fallback (the one that was missing) ─────
from django.shortcuts import render

def login_view(request):
    if request.method == "POST":
        #Handle login using email/password
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request,username=email, password=password)

        if user is not None:
            login(request,user)
            return redirect(reverse('/')) #redirect to homepage
        else:
            return HttpResponse("invalid credentials", status =400)
    #Get request: Render the login page with login form
    return  render(request, 'users/login.html')