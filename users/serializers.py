from  rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role']
        read_only_fields = ['email', 'date_joined'] #never let frontend change email

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password], style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'role', 'password', 'password2']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        user = authenticate(email=attrs['email'], password=attrs['password'])
        if not user or not user.is_active:
            raise  serializers.ValidationError("Invalid credentials.")
        attrs['user'] = user
        return attrs

class UpdateProfileSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields =  ['full_name', 'role']
    
    def validate_role(self, value):
        allowed = ['customer', 'employee']
        if value not in allowed and getattr(self.instance, 'role', '') !=value:
            raise serializers.ValidationError("You cannot assign this role.")
        return value