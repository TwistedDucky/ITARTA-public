from django.urls import path
from .views import RegisterPassengerView, LoginView,UpdateFCMTokenView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/passenger/', RegisterPassengerView.as_view(), name='register_passenger'),
    path('login/', LoginView.as_view(), name='login'),
    path('update-fcm/', UpdateFCMTokenView.as_view(), name='update-fcm-token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]