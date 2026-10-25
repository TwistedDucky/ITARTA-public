from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class PassengerRegistrationSerializer(serializers.Serializer):
    """Validates the incoming JSON data from the Android app."""
    
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=15)
    # write_only ensures the password never accidentally gets sent back in a response
    password = serializers.CharField(write_only=True) 
    age = serializers.IntegerField(required=False, allow_null=True)
    sex = serializers.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False)
    profile_photo = serializers.ImageField(required=False)

    def validate_phone_number(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value
    
class LoginSerializer(serializers.Serializer):
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

        if not hasattr(user, 'passenger_profile'):
            raise serializers.ValidationError("No passenger account found for this phone number.")

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