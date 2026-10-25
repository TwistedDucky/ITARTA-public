from rest_framework import serializers
from .models import Stand, State, District

class NearbyStandSerializer(serializers.ModelSerializer):
    district = serializers.CharField(source='district.name', read_only=True)
    lat = serializers.FloatField(source='location.y', read_only=True)
    lng = serializers.FloatField(source='location.x', read_only=True)
    distance_meters = serializers.SerializerMethodField()
    
    # NEW: Tell the passenger app exactly how many drivers are waiting
    available_drivers = serializers.SerializerMethodField() 

    class Meta:
        model = Stand
        fields = ['stand_code', 'name', 'place', 'district', 'distance_meters', 'lat', 'lng', 'available_drivers']

    def get_distance_meters(self, obj):
        if hasattr(obj, 'distance'):
            return round(obj.distance.m)
        return None

    def get_available_drivers(self, obj):
        from core.redis_client import get_queue_length
        return get_queue_length(obj.id)

class EnterStandSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()

class ListStatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "name"]

class ListDistrictsSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]

class ListStandsSerializer(serializers.ModelSerializer):

    lat = serializers.FloatField(source='location.y', read_only=True)
    lng = serializers.FloatField(source='location.x', read_only=True)

    class Meta:
        model = Stand
        fields = ["id", "name", "lat", "lng"]