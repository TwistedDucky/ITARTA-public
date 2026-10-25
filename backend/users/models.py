import os
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from core.storage_backends import PublicMediaStorage

# ==========================================
# 1. HELPER FUNCTIONS
# ==========================================
def rename_passenger_photo(instance, filename):
    """
    Renames the uploaded file to: passengers/photos/<phone_number>_<random_string>.<ext>
    """
    ext = os.path.splitext(filename)[1].lower()
    random_id = uuid.uuid4().hex[:8]
    new_filename = f"{instance.user.phone_number}_{random_id}{ext}"
    return os.path.join('passengers/photos/', new_filename)


# ==========================================
# 2. CUSTOM USER MANAGER
# ==========================================
class UserManager(BaseUserManager):
    """Custom manager that uses phone_number instead of username for authentication."""
    
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number must be set')
        
        # Create and save the user
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Creates an Admin user."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(phone_number, password, **extra_fields)


# ==========================================
# 3. BASE USER MODEL
# ==========================================
class User(AbstractUser):
    """The core authentication and authorization model."""

    # Remove the default username field
    username = None 
    
    # Make phone_number the unique identifier for logging in
    phone_number = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)
    fcm_token = models.CharField(max_length=255, blank=True, null=True, help_text="Firebase Cloud Messaging token for push notifications")

    USERNAME_FIELD = 'phone_number'
    
    # Fields required when using `createsuperuser` in the terminal
    REQUIRED_FIELDS = [] 

    # Link the custom manager
    objects = UserManager()

    def __str__(self):
        return f"{self.phone_number}"


# ==========================================
# 4. PASSENGER PROFILE MODEL
# ==========================================
class PassengerProfile(models.Model):
    """Holds identity fields specific ONLY to passengers."""
    
    # Links directly to the base User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='passenger_profile')
    
    age = models.PositiveIntegerField(null=True, blank=True)
    sex = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True)
    
    # Uses our custom function to rename the photo securely
    profile_photo = models.ImageField(
    storage=PublicMediaStorage(),
    upload_to=rename_passenger_photo,
    null=True,
    blank=True
)

    def __str__(self):
        return f"Passenger Profile: {self.user.phone_number}"