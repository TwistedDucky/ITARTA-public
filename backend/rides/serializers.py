from rest_framework import serializers

class FareConfigSerializer(serializers.Serializer):
    base_fare = serializers.DecimalField(max_digits=8,decimal_places=2)
    price_per_km = serializers.DecimalField(max_digits=8,decimal_places=2)

class RideEstimateSerializer(serializers.Serializer):
    pickup_lat = serializers.FloatField()
    pickup_lng = serializers.FloatField()
    destination_lat = serializers.FloatField()
    destination_lng = serializers.FloatField()

class RideRequestSerializer(serializers.Serializer):
    pickup_lat = serializers.FloatField()
    pickup_lng = serializers.FloatField()
    destination_lat = serializers.FloatField()
    destination_lng = serializers.FloatField()
    dropoff_address = serializers.CharField()

class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=4)
    driver_lat = serializers.FloatField()
    driver_lng = serializers.FloatField()

class CompleteRideSerializer(serializers.Serializer):
    driver_lat = serializers.FloatField()
    driver_lng = serializers.FloatField()
