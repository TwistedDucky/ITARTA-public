from django.db import transaction
from django.contrib.auth import get_user_model
from .models import PassengerProfile

# Safely gets our custom User model
User = get_user_model() 

def register_passenger(phone_number, password,first_name, last_name='', age=None, sex='', profile_photo=None):
    """
    Creates a base User and a PassengerProfile simultaneously.
    If one fails, both are rolled back.
    """
    with transaction.atomic():
        # 1. Create the core authentication user
        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # 2. Create the linked identity profile
        PassengerProfile.objects.create(
            user=user,
            age=age,
            sex=sex,
            profile_photo=profile_photo
        )
        
    return user