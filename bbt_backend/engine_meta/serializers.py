from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from engine_meta.models import User, PartnerService
import re


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    terms_accepted = serializers.BooleanField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'mobile', 'password', 'confirm_password',
                  'nationality', 'username', 'terms_accepted']

    def validate_username(self, value):
        if value and not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                'Username can only contain letters, numbers and underscores.')
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already taken.')
        return value

    def validate_mobile(self, value):
        if not re.match(r'^\+?[0-9]{10,15}$', value):
            raise serializers.ValidationError('Invalid mobile number.')
        if User.objects.filter(mobile=value).exists():
            raise serializers.ValidationError('Mobile number already registered.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        if not attrs['terms_accepted']:
            raise serializers.ValidationError({'terms_accepted': 'You must accept the terms.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.pop('terms_accepted')
        if not validated_data.get('username'):
            base = validated_data['email'].split('@')[0]
            username = base
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f'{base}_{counter}'
                counter += 1
            validated_data['username'] = username
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            mobile=validated_data.get('mobile'),
            nationality=validated_data.get('nationality', 'Indian'),
            username=validated_data['username'],
            roles=['customer'],
        )


class PartnerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    terms_accepted = serializers.BooleanField(write_only=True, required=True)
    business_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'mobile', 'password',
                  'confirm_password', 'terms_accepted', 'business_name']

    def validate_mobile(self, value):
        if not re.match(r'^\+?[0-9]{10,15}$', value):
            raise serializers.ValidationError('Invalid mobile number.')
        if User.objects.filter(mobile=value).exists():
            raise serializers.ValidationError('Mobile number already registered.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        if not attrs['terms_accepted']:
            raise serializers.ValidationError({'terms_accepted': 'You must accept the terms.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.pop('terms_accepted')
        business_name = validated_data.pop('business_name')
        base = re.sub(r'[^a-zA-Z0-9]', '_', business_name).lower()
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}_{counter}'
            counter += 1
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            mobile=validated_data.get('mobile'),
            nationality='Indian',
            username=username,
            roles=['partner'],
        )
        from engine_b2b.models import PartnerProfile
        PartnerProfile.objects.create(user=user, business_name=business_name)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    login_context = serializers.ChoiceField(
        choices=['customer', 'partner', 'admin'], default='customer')

    def validate(self, attrs):
        user = authenticate(email=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('Account is deactivated.')
        context = attrs['login_context']
        if context == 'partner' and 'partner' not in user.roles:
            raise serializers.ValidationError('No partner account found.')
        if context == 'admin' and not any(r in user.roles for r in ['admin', 'super_admin']):
            raise serializers.ValidationError('No admin account found.')
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'mobile', 'username',
                  'nationality', 'roles', 'created_at']
        read_only_fields = ['id', 'email', 'roles', 'created_at']


class PartnerServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerService
        fields = ['id', 'service_type', 'status', 'license_document',
                  'created_at', 'verified_at']
        read_only_fields = ['id', 'status', 'created_at', 'verified_at']