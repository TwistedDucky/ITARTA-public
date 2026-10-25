from rest_framework import permissions

class IsApprovedDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            IsDriver = hasattr(request.user, 'driver_profile')
            if IsDriver:
                return request.user.driver_profile.is_approved
        return False

class IsDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return hasattr(request.user, 'driver_profile')
        return False
        
class IsPassenger(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return hasattr(request.user, 'passenger_profile')
        return False