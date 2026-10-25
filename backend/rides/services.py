import logging
import redis
import json
from rides.models import FareConfig
from core.exceptions import FareConfigUnavailable, QueueServiceUnavailable, RoutingServiceUnavailable
import requests
from requests.exceptions import RequestException
from core.redis_client import pop_from_queue, is_driver_online, get_queue_length, driver_to_front_of_queue
from backend.utils.fcm import send_ride_request_notification
from users.models import User
from rides.models import DriverRequest
from rides.tasks import driver_timeout_task
from core.exceptions import QueueServiceUnavailable
from django.conf import settings


logger = logging.getLogger(__name__)

r = redis.Redis(host='localhost', port=6379, decode_responses=True)


def get_fare_config():

    """The function returns the latest created FareConfig object which contains the base fare and price per km.
    If the fare was cached it would return it from the cache else it would cache the values and set a expiry for 24 hours."""

    cached = r.get('fare_config')
    if cached :
        return json.loads(cached)
    else:
        config = FareConfig.objects.order_by('-created_at').first()
        if config is None:
            raise FareConfigUnavailable("The fare configuration has not been set up yet!")
        config_dict = {
            "base_fare": str(config.base_fare),
            "price_per_km": str(config.price_per_km)
        }
        jcache = json.dumps(config_dict)
        r.set('fare_config',jcache,ex=86400)
        return config_dict
    
def calculate_fare_and_route(stand, pickup_location, destination_location):
    fare_config = get_fare_config()
    try:
        stand_location = stand.location
        first_leg = requests.get(f"{settings.OSRM_URL}/route/v1/driving/{stand_location.x},{stand_location.y};{pickup_location.x},{pickup_location.y}?overview=full&geometries=geojson",timeout=5)
        second_leg = requests.get(f"{settings.OSRM_URL}/route/v1/driving/{pickup_location.x},{pickup_location.y};{destination_location.x},{destination_location.y}?overview=full&geometries=geojson", timeout=5)
        
        if first_leg.status_code == requests.codes.ok and second_leg.status_code == requests.codes.ok:

            first_leg_data = first_leg.json()
            second_leg_data = second_leg.json()

            if not first_leg_data.get('routes') or not second_leg_data.get('routes'):
                raise RoutingServiceUnavailable("No route found between the given points!")

            first_leg_distance_in_km = first_leg_data['routes'][0]['legs'][0]['distance']/1000
            second_leg_distance_in_km = second_leg_data['routes'][0]['legs'][0]['distance']/1000

            fare = float(fare_config['base_fare']) + (float(fare_config['price_per_km']) * (first_leg_distance_in_km + second_leg_distance_in_km))

            distance = first_leg_distance_in_km + second_leg_distance_in_km
            stand_data = {"stand_id":stand.id,
                           "stand_name":stand.name,
                            "stand_lat":stand_location.y,
                            "stand_lng":stand_location.x, 
                            "stand_distance":first_leg_distance_in_km
                            }
            return {"stand_data":stand_data,'fare': fare, 'geometry': {"leg_1": first_leg_data['routes'][0]['geometry']['coordinates'], "leg_2": second_leg_data['routes'][0]['geometry']['coordinates']}, 'total_distance': distance}
        else:

            raise RoutingServiceUnavailable("The routing service is unavailable at the moment!")
    except RequestException:
        raise RoutingServiceUnavailable("The routing service is unavailable at the moment!")
    
def dispatch_ride(ride):
    logger.info(
        "[DISPATCH] Starting dispatch | ride_id=%s | stand_id=%s",
        ride.id, ride.assigned_stand.id
    )
    try:
        ride.refresh_from_db()
        if ride.status == 'CANCELLED':
            logger.info(
                "[DISPATCH] Ride already cancelled, aborting before queue check | ride_id=%s",
                ride.id
            )
            return

        length = get_queue_length(ride.assigned_stand.id)
        logger.info(
            "[DISPATCH] Queue length at stand | ride_id=%s | stand_id=%s | queue_length=%s",
            ride.id, ride.assigned_stand.id, length
        )

        while(length > 0):
            driver_id = pop_from_queue(ride.assigned_stand.id)
            logger.info(
                "[DISPATCH] Popped driver from queue | ride_id=%s | driver_id=%s | remaining_length=%s",
                ride.id, driver_id, length - 1
            )

            if is_driver_online(driver_id=driver_id):
                logger.info(
                    "[DISPATCH] Driver is online | ride_id=%s | driver_id=%s",
                    ride.id, driver_id
                )
                driver = User.objects.get(id=driver_id)
                driver_request = DriverRequest()
                driver_request.ride = ride
                driver_request.driver = driver
                driver_request.save()
                logger.info(
                    "[DISPATCH] DriverRequest created | driver_request_id=%s | ride_id=%s | driver_id=%s",
                    driver_request.id, ride.id, driver_id
                )

                ride.refresh_from_db()
                if ride.status == 'CANCELLED':
                    logger.info(
                        "[DISPATCH] Ride cancelled after DriverRequest created | ride_id=%s | driver_request_id=%s | marking CN and pushing driver to front of queue",
                        ride.id, driver_request.id
                    )
                    driver_request.status='CN'
                    driver_request.save()
                    driver_to_front_of_queue(stand_id=ride.assigned_stand.id,driver_id=driver_request.driver.id)
                    return
                
                task = driver_timeout_task.apply_async((ride.id, driver_request.id), countdown=30)
                logger.info(
                    "[DISPATCH] Celery timeout task scheduled | task_id=%s | driver_request_id=%s | ride_id=%s | countdown=30s",
                    task.id, driver_request.id, ride.id
                )

                send_ride_request_notification(driver,ride)

                driver_request.celery_task_id = task.id
                driver_request.save()
                logger.info(
                    "[DISPATCH] Dispatch complete for this attempt, waiting on driver response | ride_id=%s | driver_request_id=%s | driver_id=%s",
                    ride.id, driver_request.id, driver_id
                )
                break
            else:
                logger.info(
                    "[DISPATCH] Driver offline, skipping (not re-queued) | ride_id=%s | driver_id=%s",
                    ride.id, driver_id
                )
                length=length - 1
        else:
            logger.warning(
                "[DISPATCH] Queue exhausted, no available drivers | ride_id=%s | stand_id=%s",
                ride.id, ride.assigned_stand.id
            )
            ride.status = 'TIMED_OUT'
            ride.save() 
    except QueueServiceUnavailable:
        logger.error(
            "[DISPATCH] Queue service unavailable, marking ride as timed out | ride_id=%s",
            ride.id
        )
        ride.status = 'TIMED_OUT'
        ride.save()
    except User.DoesNotExist:
        logger.error(
            "[DISPATCH] Driver User object not found (stale queue entry?) | ride_id=%s | driver_id=%s",
            ride.id, driver_id
        )
        pass