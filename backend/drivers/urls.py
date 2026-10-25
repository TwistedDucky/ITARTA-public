from django.urls import path
from .views import RegisterDriverView, DriverDetailsView, DriverLoginView

urlpatterns = [
    path('register/', RegisterDriverView.as_view(), name='register_driver'),
    path('details/', DriverDetailsView.as_view(), name='driver_detail'),
    path('login/', DriverLoginView.as_view(), name='driver-login'),
]