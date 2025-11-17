# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Used for profile display, order history, staff list, etc."""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role', 'phone_number',
            'favourite_drink', 'loyalty_points', 'date_joined'
        ]
        read_only_fields = ['email', 'loyalty_points', 'date_joined', 'role']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Confirm password"
    )

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'password2', 'phone_number', 'favourite_drink']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        # New customers always start as 'customer'
        validated_data.setdefault('role', 'customer')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            email=attrs['email'],
            password=attrs['password']
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled.")

        attrs['user'] = user
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Regular users can only update their name, phone, favourite drink"""
    class Meta:
        model = User
        fields = ['full_name', 'phone_number', 'favourite_drink']
        read_only_fields = ['email', 'role', 'loyalty_points']

    def validate_full_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name is too short.")
        return value.strip()


class StaffUpdateSerializer(serializers.ModelSerializer):
    """Only managers/owners can change role"""
    class Meta:
        model = User
        fields = ['full_name', 'role', 'is_active', 'loyalty_points']
        read_only_fields = ['loyalty_points']

    def validate_role(self, value):
        allowed_for_staff = ['customer', 'barista', 'manager', 'admin']
        if value not in [choice[0] for choice in User.ROLE_CHOICES]:
            raise serializers.ValidationError("Invalid role.")
        # Optional: restrict who can make someone an owner
        if value == 'owner' and not self.context['request'].user.is_owner:
            raise serializers.ValidationError("Only the owner can create another owner.")
        return value