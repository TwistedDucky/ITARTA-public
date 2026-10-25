import os
import uuid
from django.db import models
from django.conf import settings
from stands.models import Stand
from core.storage_backends import PublicMediaStorage

# ==========================================
# 1. HELPER FUNCTIONS FOR IMAGES
# ==========================================
def rename_driver_photo(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return os.path.join('drivers/profiles/', f"{instance.user.phone_number}_{uuid.uuid4().hex[:8]}{ext}")

def rename_license_photo(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return os.path.join('drivers/licenses/', f"{instance.user.phone_number}_license_{uuid.uuid4().hex[:8]}{ext}")

def rename_vehicle_photo(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return os.path.join('drivers/vehicles/', f"{instance.user.phone_number}_vehicle_{uuid.uuid4().hex[:8]}{ext}")


# ==========================================
# 2. DRIVER PROFILE MODEL
# ==========================================
class DriverProfile(models.Model):
    """Holds identity and professional fields specific ONLY to drivers."""
    
    # Links directly to our custom User model in the users app
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='driver_profile'
    )

    home_stand = models.ForeignKey(
        Stand, on_delete=models.PROTECT
    )
    
    # Professional Details
    vehicle_number = models.CharField(max_length=20, unique=True)
    license_number = models.CharField(max_length=50, unique=True)
    
    # Auto-rickshaw capacity is usually 3 or 5 passengers
    CAPACITY_CHOICES = [
        (3, 'Three Passengers'),
        (5, 'Five Passengers'),
    ]
    capacity = models.IntegerField(choices=CAPACITY_CHOICES, default=3)
    
    # Required Documents using our custom renaming functions
    driver_photo = models.ImageField(storage=PublicMediaStorage(),
                                     upload_to=rename_driver_photo
                                        )
    license_photo = models.ImageField(upload_to=rename_license_photo)
    vehicle_photo = models.ImageField(upload_to=rename_vehicle_photo)
    
    # Verification status for admins to approve before they can join a stand
    is_approved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Driver: {self.user.phone_number} | Vehicle: {self.vehicle_number}"