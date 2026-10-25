from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.core.exceptions import ValidationError
from core.redis_client import get_queue_length
from .models import Stand

def find_nearest_stand_with_a_driver(user_location_point):
    nearest_stands = Stand.objects.filter(
                is_active=True,
            ).distinct() \
             .annotate(distance=Distance('location', user_location_point)) \
             .order_by('distance')[:5]
            
    for stand in nearest_stands:
        length = get_queue_length(stand.id)
        if length:
            return stand
    return None
