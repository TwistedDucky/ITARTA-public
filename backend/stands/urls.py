from django.urls import path
from .views import (
    NearbyStandsView,
    EnterStandView,
    LeaveStandView,
    HeartBeatView,
    ListStatesView,
    ListDistrictsView,
    ListStandsView,
    QueueStatusView
)

urlpatterns = [
    path('nearby/', NearbyStandsView.as_view(), name='nearby_stands'),
    path('enter/', EnterStandView.as_view(), name='enter_stand'),
    path('leave/', LeaveStandView.as_view(), name='leave_stand'),
    path('heartbeat/', HeartBeatView.as_view(), name='heartbeat'),
    path('states/', ListStatesView.as_view(), name='list-states'),
    path('districts/', ListDistrictsView.as_view(), name='list-districts'),
    path('stands/', ListStandsView.as_view(), name='list-stands'),
    path('driver-status/', QueueStatusView.as_view(), name='queue_status'),
]