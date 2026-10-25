from django.contrib.gis.db import models
from django.conf import settings
from stands.models import Stand
import random

class FareConfig(models.Model):
     base_fare = models.DecimalField(max_digits=8, decimal_places=2)
     price_per_km = models.DecimalField(max_digits=8, decimal_places=2)
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)

class Ride(models.Model):
    """Tracks the complete lifecycle of an auto-rickshaw trip."""
    
    #Maybe the status could add something like OTP verified. Maybe we could give a start ride option when the driver reaches the pickup point.
    
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('ACCEPTED', 'Accepted'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('TIMED_OUT', 'Timed Out')
    ]

    # --- 1. The People ---
    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='rides_requested'
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='rides_driven'
    )
    
    # --- 2. The Stand Information ---
    # Which stand was this driver dispatched from? 
    # (This is assigned by the server when the passenger requests the ride)
    assigned_stand = models.ForeignKey(
        Stand, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='dispatched_rides',
        help_text="The stand where the assigned driver was waiting"
    )

    # --- 3. Pickup Details (Where the passenger is right now) ---
    pickup_location = models.PointField(
        srid=4326, 
        help_text="Exact GPS coordinates of the passenger"
    )

    # --- 4. Drop-off Details (Where they are going) ---
    dropoff_location = models.PointField(
        srid=4326, 
        help_text="GPS coordinates of the destination"
    )

    dropoff_address = models.CharField(max_length=200, blank=False, null=False)

    pickup_otp = models.CharField(
        max_length=4, 
        blank=True, 
        null=True,
        help_text="4-digit OTP generated when ride is requested. Verified by driver to start the trip."
    )
    # --- 5. Trip Status & Fare ---
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    est_fare = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    final_fare = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # --- 6. Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)     

    def __str__(self):
        return f"Ride #{self.id} | Passenger: {self.passenger.phone_number} | Status: {self.status}"
    
    def generate_otp(self):
        """Generates a random 4-digit OTP."""
        self.pickup_otp = f"{random.randint(1000, 9999)}"
        self.save(update_fields=['pickup_otp'])

class DriverRequest(models.Model):

    class DriverRequestChoices(models.TextChoices):
        REQUESTED = "RD" ,"Requested"
        ACCEPTED = "AD" ,"Accepted"
        DECLINED = "DN" ,"Declined"
        TIMEDOUT = "TD" ,"Timed Out"
        CANCELLED = "CN", "Cancelled"

    ride = models.ForeignKey(Ride,
                             on_delete=models.PROTECT,)
    
    driver = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                               on_delete=models.PROTECT,
                               null=False)
    
    status = models.CharField(max_length=2, choices=DriverRequestChoices, default=DriverRequestChoices.REQUESTED)
    celery_task_id = models.CharField(max_length=36,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True,null=True)

