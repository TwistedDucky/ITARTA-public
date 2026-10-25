from django.urls import path
from .views import (
    GetFareConfigView,
    RideEstimateView,
    RideRequestView,
    DriverAcceptView,
    DriverDeclineView,
    OTPVerifyView,
    DriverCompleteRideView,
    PassengerRideCancellationView,
    DriverRideGeometryFetchView,
    RequestedDriverRideDetailsFetchView,
    AcceptedDriverRideDetailsFetchView,
    PassengerRideDetailsFetchView,
)

urlpatterns = [
    path('fare-config/', GetFareConfigView.as_view(), name='fare_config'),
    path('estimate/', RideEstimateView.as_view(), name='ride_estimate'),
    path('request/', RideRequestView.as_view(), name='ride_request'),
    path('<int:ride_id>/accept/', DriverAcceptView.as_view(), name='driver_accept'),
    path('<int:ride_id>/decline/', DriverDeclineView.as_view(), name='driver_decline'),
    path('<int:ride_id>/verify-otp/', OTPVerifyView.as_view(), name='verify_otp'),
    path('<int:ride_id>/complete/', DriverCompleteRideView.as_view(), name='complete_ride'),
    path('<int:ride_id>/cancel/', PassengerRideCancellationView.as_view(), name='cancel_ride'),
    path('<int:ride_id>/geometry/', DriverRideGeometryFetchView.as_view(), name='ride_geometry'),
    path('<int:ride_id>/geometry/', DriverRideGeometryFetchView.as_view(), name='ride_geometry'),
    path('<int:ride_id>/requested-details/', RequestedDriverRideDetailsFetchView.as_view(), name='requested_driver_details'),
    path('<int:ride_id>/accepted-details/', AcceptedDriverRideDetailsFetchView.as_view(), name='accepted_driver_details'),
    path('<int:ride_id>/passenger-details/', PassengerRideDetailsFetchView.as_view(), name='passenger_ride_details'),
]