from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DriverProfile
from stands.models import Stand
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class DriverRegistrationSerializer(serializers.Serializer):
    # Base User Fields
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    #stand selection
    home_stand = serializers.PrimaryKeyRelatedField(queryset=Stand.objects.all())
    
    # Driver Profile Fields
    vehicle_number = serializers.CharField(max_length=20)
    license_number = serializers.CharField(max_length=50)
    capacity = serializers.ChoiceField(choices=[3, 5])
    
    # Required Documents
    driver_photo = serializers.ImageField()
    license_photo = serializers.ImageField()
    vehicle_photo = serializers.ImageField()

    def validate_phone_number(self, value):
        try:
            user = User.objects.get(phone_number=value)
            if hasattr(user, 'driver_profile'):
                raise serializers.ValidationError("This phone number is already registered as a driver.")
        except User.DoesNotExist:
            pass
        return value

    def validate_vehicle_number(self, value):
        if DriverProfile.objects.filter(vehicle_number=value).exists():
            raise serializers.ValidationError("This vehicle number is already registered.")
        return value

    def validate_license_number(self, value):
        if DriverProfile.objects.filter(license_number=value).exists():
            raise serializers.ValidationError("This license number is already registered.")
        return value

class DriverLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')

        # 1. Authenticate using Django's built-in security
        request = self.context.get('request')
        user = authenticate(request=request, phone_number=phone_number, password=password)

        if not user:
            raise serializers.ValidationError("Invalid phone number or password.")

        if not hasattr(user, 'driver_profile'):
            raise serializers.ValidationError("No driver account found for this phone number.")

        # 2. Generate the JWT tokens
        refresh = RefreshToken.for_user(user)


        # 4. Package everything up for the Android app
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'phone_number': user.phone_number,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }