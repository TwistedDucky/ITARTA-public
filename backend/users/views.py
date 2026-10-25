from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import register_passenger
from .serializers import PassengerRegistrationSerializer, LoginSerializer
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes, inline_serializer
from rest_framework import serializers
from core.permissions import IsPassenger


class RegisterPassengerView(APIView):
    """
    POST /api/v1/users/register/passenger/
    """
    @extend_schema(
        request=PassengerRegistrationSerializer,
        responses={201: None, 400: None},
        summary="Register a new passenger"
    )
    def post(self, request):
        serializer = PassengerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = register_passenger(**serializer.validated_data)
            return Response(
                {
                    "message": "Passenger registered successfully", 
                    "phone_number": user.phone_number
                }, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    POST /api/v1/users/login/
    """
    permission_classes = []

    @extend_schema(
        request=LoginSerializer,
        responses={200: None, 401: None},
        summary="Login with phone number and password"
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    
class UpdateFCMTokenView(APIView):
    """ POST /api/v1/users/update-fcm/ """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name='FCMTokenSerializer',
            fields={'fcm_token': serializers.CharField()}
        ),
        responses={200: None, 400: None},
        summary="Update FCM token for push notifications"
    )
    def post(self, request):
        fcm_token = request.data.get('fcm_token')
        if not fcm_token:
            return Response({"error": "FCM token is required"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.fcm_token = fcm_token
        request.user.save(update_fields=['fcm_token'])
        return Response({"message": "FCM token updated successfully"})