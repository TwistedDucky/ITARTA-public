from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import DriverRegistrationSerializer, DriverLoginSerializer
from .services import register_driver
from drf_spectacular.utils import extend_schema
from core.permissions import IsApprovedDriver,IsDriver
from .models import DriverProfile

class RegisterDriverView(APIView):
    """
    POST /api/v1/drivers/register/
    """
    @extend_schema(
        request={'multipart/form-data': DriverRegistrationSerializer},
        responses={201: None, 400: None},
        summary="Register a new driver",
        description="Creates a new driver account with vehicle details and document uploads. If the phone number already exists as a passenger, a driver profile is added to that account. Requires admin approval before the driver can enter a stand queue."
    )
    def post(self, request):
        serializer = DriverRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = register_driver(**serializer.validated_data)
            return Response(
                {
                    "message": "Driver registered successfully. Pending admin approval.", 
                    "phone_number": user.phone_number
                }, 
                status=status.HTTP_201_CREATED
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DriverDetailsView(APIView):

    permission_classes = []

    def get(self,request):

        try:
            driver = DriverProfile.objects.get(user=request.user)
            return Response(
                {"home_stand":driver.home_stand.id,
                "home_stand_name":driver.home_stand.name,
                "driver_name":request.user.get_full_name(),
                "is_approved":driver.is_approved,
                "vehicle_number":driver.vehicle_number,
                "driver_photo":driver.driver_photo.url}, status=status.HTTP_200_OK
            )
        except DriverProfile.DoesNotExist as e:
            return Response({"error":"Driver Profile not found"},status=status.HTTP_404_NOT_FOUND)

class DriverLoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = DriverLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)