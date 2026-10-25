from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from .models import Stand, State, District
from .serializers import NearbyStandSerializer, EnterStandSerializer, ListDistrictsSerializer,ListStandsSerializer,ListStatesSerializer
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from core.permissions import IsApprovedDriver, IsDriver, IsPassenger
from django.contrib.gis.geos import Point
from core.redis_client import add_to_queue, set_heartbeat, remove_from_queue, is_in_queue
from core.exceptions import QueueServiceUnavailable
from stands.services import find_nearest_stand_with_a_driver



class NearbyStandsView(APIView):
    """ GET /api/stands/nearby/?lat=9.9312&lng=76.2673 """
    permission_classes=[IsPassenger]
    
    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if not lat or not lng:
            return Response({"error": "Please provide lat and lng"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_location = Point(float(lng), float(lat), srid=4326)
            stand = find_nearest_stand_with_a_driver(user_location)
            if stand is not None:
                serializer = NearbyStandSerializer(stand)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response("No nearby stands with active drivers",status=status.HTTP_400_BAD_REQUEST)
        
        except ValueError:
            return Response({"error": "Invalid coordinate format"}, status=status.HTTP_400_BAD_REQUEST)
        except QueueServiceUnavailable:
            return Response("Queue service unavailable",status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
# Inside your stands/views.py

class EnterStandView(APIView):

    permission_classes = [IsApprovedDriver]

    def post(self, request):
        serializer = EnterStandSerializer(data=request.data)
        if serializer.is_valid():
            point = Point(x=serializer.validated_data['lng'],y=serializer.validated_data['lat'])
            if request.user.driver_profile.home_stand.area.contains(point):
                try:
                    add_to_queue(stand_id=request.user.driver_profile.home_stand.id, driver_id=request.user.id)
                    set_heartbeat(driver_id=request.user.id)
                except QueueServiceUnavailable:
                    return Response("Queue service unavailable",status=status.HTTP_503_SERVICE_UNAVAILABLE)
                return Response("Added to queue successfully",status=status.HTTP_200_OK)
            else:
                return Response("Not inside the stand!",status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class QueueStatusView(APIView):
    permission_classes = [IsApprovedDriver]

    def get(self, request):
        try:
            in_queue = is_in_queue(
                stand_id=request.user.driver_profile.home_stand.id,
                driver_id=request.user.id
            )

            return Response(
                {"status": in_queue},
                status=status.HTTP_200_OK
            )

        except QueueServiceUnavailable:
            return Response(
                {"error": "Queue service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


    
class LeaveStandView(APIView):
    permission_classes = [IsApprovedDriver]

    def post(self, request):
        try:
            if remove_from_queue(stand_id=request.user.driver_profile.home_stand.id, driver_id=request.user.id):
                return Response(f"Driver{request.user.phone_number} exited stand successfully", status=status.HTTP_200_OK)
            else:
                return Response("Error exiting the stand!",status=status.HTTP_400_BAD_REQUEST)
        except QueueServiceUnavailable:
            return Response("Queue service unavailable", status=status.HTTP_503_SERVICE_UNAVAILABLE)
                

class HeartBeatView(APIView):
    permission_classes = [IsApprovedDriver]

    def post(self, request):
        try:
            set_heartbeat(request.user.id)
            return Response("Heartbeat restored",status=status.HTTP_200_OK)
        except QueueServiceUnavailable:
            return Response("Queue service unavailable",status=status.HTTP_503_SERVICE_UNAVAILABLE)

class ListStatesView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        states = State.objects.all()
        serializer = ListStatesSerializer(states, many=True)
        return Response({"states": serializer.data}, status=status.HTTP_200_OK)


class ListDistrictsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        state_id = request.query_params.get('state_id')
        try:
            state = State.objects.get(id=state_id)
        except State.DoesNotExist:
            return Response({"error": "State not found"}, status=status.HTTP_404_NOT_FOUND)
        districts = District.objects.filter(state=state)
        serializer = ListDistrictsSerializer(districts, many=True)
        return Response({"districts": serializer.data}, status=status.HTTP_200_OK)


class ListStandsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        district_id = request.query_params.get('district_id')
        try:
            district = District.objects.get(id=district_id)
        except District.DoesNotExist:
            return Response({"error": "District not found"}, status=status.HTTP_404_NOT_FOUND)
        stands = Stand.objects.filter(district=district)
        serializer = ListStandsSerializer(stands, many=True)
        return Response({"stands": serializer.data}, status=status.HTTP_200_OK)







