from rest_framework.views import APIView
from rides.services import get_fare_config
from rides.serializers import FareConfigSerializer
from rest_framework.response import Response
from rest_framework import status
from core.exceptions import FareConfigUnavailable, RideServiceUnavailable
from rides.services import calculate_fare_and_route, dispatch_ride
from rides.serializers import RideEstimateSerializer, RideRequestSerializer, OTPVerificationSerializer, CompleteRideSerializer
from django.contrib.gis.geos import Point
from stands.services import find_nearest_stand_with_a_driver
from core.exceptions import RoutingServiceUnavailable, FareConfigUnavailable
from core.redis_client import cache_routing_data, get_cached_routing_data, get_queue_length, cache_geometry, add_to_queue, get_cache_geometry
from rides.models import Ride, DriverRequest
from stands.models import Stand
from celery import current_app
from core.permissions import IsApprovedDriver, IsPassenger
from backend.utils.fcm import send_ride_accepted_notification, send_ride_completed_notification, send_ride_cancelled_notification
from django.db import transaction
from datetime import datetime
from django.contrib.gis.db.models.functions import Distance
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers


class GetFareConfigView(APIView):

    @extend_schema(
        responses={200: None, 503: None},
        summary="Get current fare configuration",
        description="Returns the current base fare and price per km used for fare calculation."
    )
    def get(self, request):
        try:
            config = get_fare_config()
            return Response(config, status=status.HTTP_200_OK)
        except FareConfigUnavailable as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class RideEstimateView(APIView):

    @extend_schema(
        request=RideEstimateSerializer,
        responses={200: None, 400: None, 503: None},
        summary="Get ride fare estimate",
        description="Finds the nearest stand with available drivers and returns fare, distance, and route geometry. Result is cached for 120 seconds."
    )
    def post(self, request):
        try:
            serializer = RideEstimateSerializer(data=request.data)
            if serializer.is_valid():
                pickup_location = Point(x=serializer.validated_data['pickup_lng'], y=serializer.validated_data['pickup_lat'],srid=4326)
                destination_location = Point(x=serializer.validated_data['destination_lng'], y=serializer.validated_data['destination_lat'],srid=4326)
                stand = find_nearest_stand_with_a_driver(pickup_location)

                if stand is None:
                    return Response({"error": "No nearby stands with active drivers"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                else:
                    routing_data = calculate_fare_and_route(stand=stand, pickup_location=pickup_location, destination_location=destination_location)
                    cache_routing_data(user_id=request.user.id, routing_data=routing_data)
                    return Response(routing_data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except RoutingServiceUnavailable:
            return Response({"error": "The Routing service is Unavailable at the moment!"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except FareConfigUnavailable:
            return Response({"error": "Fare Calculation service Unavailable at the moment!"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except RideServiceUnavailable as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class RideRequestView(APIView):

    @extend_schema(
        request=RideRequestSerializer,
        responses={201: None, 400: None, 404: None, 503: None},
        summary="Confirm ride request",
        description="Confirms the ride using the cached estimate. Creates a Ride, generates OTP, caches geometry, and triggers driver dispatch."
    )
    def post(self, request):
        try:
            serializer = RideRequestSerializer(data=request.data)
            if serializer.is_valid():
                pickup_location = Point(x=serializer.validated_data['pickup_lng'], y=serializer.validated_data['pickup_lat'])
                destination_location = Point(x=serializer.validated_data['destination_lng'], y=serializer.validated_data['destination_lat'])

                routing_data = get_cached_routing_data(request.user.id)
                drivers_available = get_queue_length(routing_data["stand_data"]["stand_id"])
                if drivers_available:
                    ride = Ride()
                    ride.passenger = request.user
                    ride.assigned_stand = Stand.objects.get(id=routing_data["stand_data"]["stand_id"])
                    ride.pickup_location = pickup_location
                    ride.dropoff_location = destination_location
                    ride.dropoff_address = serializer.validated_data['dropoff_address']
                    ride.est_fare = routing_data["fare"]
                    ride.save()
                    ride.generate_otp()
                    cache_geometry(ride_id=ride.id, geometry=routing_data['geometry'])
                    dispatch_ride(ride=ride)
                    return Response({"message": "Ride request created successfully!", "ride_id": ride.id}, status=status.HTTP_201_CREATED)
                else:
                    return Response({"error": "No active drivers in stand, Try again later."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except RideServiceUnavailable as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Stand.DoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class DriverAcceptView(APIView):
    # POST /api/v1/rides/<ride_id>/accept/
    permission_classes = [IsApprovedDriver]

    @extend_schema(
        responses={202: None, 400: None, 409: None},
        summary="Driver accepts a ride request",
        description="Atomically accepts the ride, revokes the Celery timeout task, and notifies the passenger."
    )
    def post(self, request, ride_id):
        try:
            with transaction.atomic():
                ride = Ride.objects.select_for_update().get(id=ride_id)
                if ride.status == 'ACCEPTED':
                    return Response({"error": "Ride already accepted"}, status=status.HTTP_409_CONFLICT)
                ride.status = 'ACCEPTED'
                ride.driver = request.user
                driver_request = DriverRequest.objects.get(ride=ride)
                driver_request.status = 'AD'
                driver_request.responded_at = datetime.now()
                current_app.control.revoke(driver_request.celery_task_id, terminate=True)
                ride.save()
                driver_request.save()
                send_ride_accepted_notification(ride.passenger, ride)
                return Response({
                    "pickup_lng": ride.pickup_location.x,
                    "pickup_lat": ride.pickup_location.y,
                    "dropoff_lng": ride.dropoff_location.x,
                    'dropoff_lat': ride.dropoff_location.y,
                    'dropoff_address': ride.dropoff_address,
                    'phone_no': ride.passenger.phone_number
                }, status=status.HTTP_202_ACCEPTED)
        except Ride.DoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except DriverRequest.DoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DriverDeclineView(APIView):
    permission_classes = [IsApprovedDriver]

    @extend_schema(
        responses={200: None, 400: None},
        summary="Driver declines a ride request",
        description="Driver declines the ride. They are pushed to the back of the queue as a penalty and dispatch continues to the next driver."
    )
    def post(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id)
            driver_request = DriverRequest.objects.get(driver=request.user, ride=ride)
            driver_request.status = 'DN'
            current_app.control.revoke(driver_request.celery_task_id, terminate=True)
            driver_request.save()
            add_to_queue(ride.assigned_stand.id, request.user.id)
            dispatch_ride(ride=ride)
            return Response({"message": "Ride declined successfully. Now you are at the back of the queue as a penalty."}, status=status.HTTP_200_OK)
        except Ride.DoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except DriverRequest.DoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OTPVerifyView(APIView):
    # POST /api/v1/rides/<ride_id>/verify-otp/
    permission_classes = [IsApprovedDriver]

    @extend_schema(
        request=OTPVerificationSerializer,
        responses={200: None, 400: None, 401: None},
        summary="Verify OTP at pickup",
        description="Driver submits OTP and current GPS coordinates. Backend verifies proximity (200m) and OTP match before setting ride to IN_PROGRESS."
    )
    def post(self, request, ride_id):
        try:
            serializer = OTPVerificationSerializer(data=request.data)
            if serializer.is_valid():
                driver_location = Point(x=serializer.validated_data['driver_lng'], y=serializer.validated_data['driver_lat'])
                ride = Ride.objects.annotate(
                    driver_distance=Distance('pickup_location', driver_location)
                ).get(id=ride_id)
                if ride.driver_distance.m <= 200:
                    if serializer.validated_data['otp'] == ride.pickup_otp:
                        ride.status = 'IN_PROGRESS'
                        ride.save()
                        return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
                    else:
                        return Response({"message": "The OTP entered is incorrect!"}, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    return Response({"message": "You are not near the pickup point!"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Ride.DoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DriverCompleteRideView(APIView):
    # POST /api/v1/rides/<ride_id>/complete/
    permission_classes = [IsApprovedDriver]

    @extend_schema(
        request=CompleteRideSerializer,
        responses={200: None, 400: None, 401: None},
        summary="Driver marks ride as complete",
        description="Driver submits current GPS coordinates. Backend verifies proximity to dropoff (100m) and sets ride to COMPLETED. Passenger is notified via FCM."
    )
    def post(self, request, ride_id):
        try:
            serializer = CompleteRideSerializer(data=request.data)
            if serializer.is_valid():
                driver_location = Point(x=serializer.validated_data['driver_lng'], y=serializer.validated_data['driver_lat'])
                ride = Ride.objects.annotate(
                    driver_destination_displacement=Distance('dropoff_location', driver_location)
                ).get(id=ride_id)
                if request.user == ride.driver:
                    if ride.driver_destination_displacement.m < 100:
                        if ride.status == 'IN_PROGRESS':
                            ride.status = 'COMPLETED'
                            ride.final_fare = ride.est_fare
                            ride.save()
                            send_ride_completed_notification(ride.passenger, ride=ride)
                            return Response({"message": f"Ride<{ride.id}> completed successfully!"}, status=status.HTTP_200_OK)
                        else:
                            return Response({"message": "Passenger was not picked up and otp was not verified"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({"message": "You are not near enough to the destination"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": "Unauthorized use!"}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Ride.DoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PassengerRideCancellationView(APIView):
    # POST /api/v1/rides/<ride_id>/cancel/
    permission_classes = [IsPassenger]

    @extend_schema(
        responses={200: None, 400: None, 401: None, 404: None},
        summary="Passenger cancels a ride",
        description="Passenger can only cancel during REQUESTED status. Cancellation is blocked once a driver has accepted. Revokes active Celery task and notifies driver if one was being dispatched."
    )
    def post(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id)
            if ride.passenger == request.user:
                if ride.status == "REQUESTED":
                    ride.status = "CANCELLED"
                    ride.save()
                    try:
                        driver_request = DriverRequest.objects.filter(ride=ride, status="RD").latest('created_at')
                        current_app.control.revoke(driver_request.celery_task_id, terminate=True)
                        driver_request.status = 'CN'
                        driver_request.save()
                        send_ride_cancelled_notification(driver_request.driver, ride=ride)
                    except DriverRequest.DoesNotExist:
                        pass
                    return Response({"message": f"The ride {ride.id} was cancelled successfully!"}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "The request was already accepted by the driver"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "You are unauthorised to cancel this ride!"}, status=status.HTTP_401_UNAUTHORIZED)
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)


class DriverRideGeometryFetchView(APIView):
    permission_classes = [IsApprovedDriver]

    @extend_schema(
        responses={200: None, 401: None, 404: None, 503: None},
        summary="Fetch ride route geometry",
        description="Returns the cached GeoJSON route geometry for a ride. Only accessible by the assigned driver. Geometry expires after 600 seconds."
    )
    def get(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id)
            if DriverRequest.objects.filter(ride=ride, driver=request.user).exists():
                geometry = get_cache_geometry(ride_id)
                return Response({"geometry": geometry}, status=status.HTTP_200_OK)
            return Response({"error": "You are not authorized to view this data!"}, status=status.HTTP_401_UNAUTHORIZED)
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)
        except RideServiceUnavailable as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class RequestedDriverRideDetailsFetchView(APIView):
    permission_classes = [IsApprovedDriver]

    @extend_schema(
        responses={200: None, 401: None, 404: None},
        summary="Get ride details for driver (before accepting)",
        description="Returns pickup/dropoff coordinates, address, and estimated fare. Only accessible by a driver with an active DriverRequest for this ride."
    )
    def get(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id)
            if DriverRequest.objects.filter(ride=ride, driver=request.user).exists():
                return Response({
                    "pickup_lat": ride.pickup_location.y,
                    "pickup_lng": ride.pickup_location.x,
                    "dropoff_lat": ride.dropoff_location.y,
                    "dropoff_lng": ride.dropoff_location.x,
                    "dropoff_address": ride.dropoff_address,
                    "est_fare": ride.est_fare,
                }, status=status.HTTP_200_OK)
            return Response({"error": "You are not authorized to view this data!"}, status=status.HTTP_401_UNAUTHORIZED)
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)


class AcceptedDriverRideDetailsFetchView(APIView):
    permission_classes = [IsApprovedDriver]

    @extend_schema(
        responses={200: None, 401: None, 404: None},
        summary="Get ride details for driver (after accepting)",
        description="Returns pickup/dropoff coordinates, address, estimated fare, and passenger contact details. Only accessible by the assigned driver."
    )
    def get(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id)
            if ride.driver == request.user:
                return Response({
                    "pickup_lat": ride.pickup_location.y,
                    "pickup_lng": ride.pickup_location.x,
                    "dropoff_lat": ride.dropoff_location.y,
                    "dropoff_lng": ride.dropoff_location.x,
                    "dropoff_address": ride.dropoff_address,
                    "est_fare": ride.est_fare,
                    "passenger_name": ride.passenger.first_name,
                    "passenger_phone": ride.passenger.phone_number,
                }, status=status.HTTP_200_OK)
            return Response({"error": "You are not authorized to view this data!"}, status=status.HTTP_401_UNAUTHORIZED)
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)


class PassengerRideDetailsFetchView(APIView):
    permission_classes = [IsPassenger]

    @extend_schema(
        responses={200: None, 401: None, 404: None},
        summary="Get ride details for passenger",
        description="Returns ride status, OTP, fare, and driver details. Driver details are null if no driver has been assigned yet."
    )
    def get(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id)
            if ride.passenger == request.user:
                if ride.driver is None:
                    return Response({
                        "status": ride.status,
                        "driver_name": None,
                        "driver_phone": None,
                        "vehicle_number": None,
                        "est_fare": ride.est_fare,
                        "otp": ride.pickup_otp,
                    }, status=status.HTTP_200_OK)
                return Response({
                    "status": ride.status,
                    "driver_name": ride.driver.first_name,
                    "driver_phone": ride.driver.phone_number,
                    "vehicle_number": ride.driver.driver_profile.vehicle_number,
                    "est_fare": ride.est_fare,
                    "otp": ride.pickup_otp,
                }, status=status.HTTP_200_OK)
            return Response({"error": "You are not authorized to view this data!"}, status=status.HTTP_401_UNAUTHORIZED)
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)