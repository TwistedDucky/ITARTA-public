from django.db import transaction
from django.contrib.auth import get_user_model
from .models import DriverProfile

User = get_user_model()

def register_driver(
    phone_number, password, first_name, last_name, 
    vehicle_number, license_number, capacity,
    driver_photo, license_photo, vehicle_photo, home_stand
):
    with transaction.atomic():
        # Check if user already exists (passenger registering as driver)
        try:
            user = User.objects.get(phone_number=phone_number)
            # User exists — they're a passenger, just add driver profile
        except User.DoesNotExist:
            # Fresh registration — create new user
            user = User.objects.create_user(
                phone_number=phone_number,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
        
        # 2. Create the linked DriverProfile
        DriverProfile.objects.create(
            user=user,
            home_stand = home_stand,
            vehicle_number=vehicle_number,
            license_number=license_number,
            capacity=capacity,
            driver_photo=driver_photo,
            license_photo=license_photo,
            vehicle_photo=vehicle_photo,
            is_approved=False  # Must be approved by an admin later
        )
        
    return user