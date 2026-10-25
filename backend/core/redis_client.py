import redis
import time
import json
from core.exceptions import QueueServiceUnavailable, RideServiceUnavailable
from redis.exceptions import ConnectionError

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def add_to_queue(stand_id, driver_id):
    try:
        r.zadd(f'queue:stand:{stand_id}', {str(driver_id):int(time.time()*1000)})
    except ConnectionError:
        raise QueueServiceUnavailable("Queue service is unavailable")

def pop_from_queue(stand_id):
    try:
        driver = r.zpopmin(f'queue:stand:{stand_id}')
        if driver:
            return driver[0][0]
        else:
            return None
    except ConnectionError:
        raise QueueServiceUnavailable("Queue service is unavailable")
    
def set_heartbeat(driver_id):
    try:
        r.set(name=f"driver:online:{driver_id}",value='online',ex=30)
    except ConnectionError:
        raise QueueServiceUnavailable("Queue service unavailable")

def is_in_queue(stand_id,driver_id):
    try:
        score = r.zscore(f'queue:stand:{stand_id}',str(driver_id))
        if score is None:
            return False
        else:
            return True
    except ConnectionError:
            raise QueueServiceUnavailable("Queue service unavailable")
        

def is_driver_online(driver_id):
    try:
        yes = r.get(f"driver:online:{driver_id}")
        if yes:
            return True
        else:
            return False
    except ConnectionError:
        raise QueueServiceUnavailable("Queue service unavailable")

def remove_from_queue(stand_id, driver_id):
    try:
        driver = r.zrem(f'queue:stand:{stand_id}',f'{driver_id}')
        if driver:
            return True
        else:
            return False
    except ConnectionError:
        raise QueueServiceUnavailable("Queue service unavailable")

def get_queue_length(stand_id):
    try:
        NoOfDrivers = r.zcard(f'queue:stand:{stand_id}')
        return NoOfDrivers
    except ConnectionError:
        raise QueueServiceUnavailable("Queue service unavailable")
    
def cache_routing_data(user_id,routing_data):
    try:
        jcache = json.dumps(routing_data)
        r.set(f"Estimate:{user_id}",jcache,ex=120)
    except ConnectionError:
        raise RideServiceUnavailable("Ride Service Unavailable")

def get_cached_routing_data(user_id):
    try:
        jcache = r.get(f"Estimate:{user_id}")
        if jcache:
            routing_data = json.loads(jcache)
            return routing_data
        else:
            raise RideServiceUnavailable("Estimate data has expired or not present!")
    except ConnectionError:
        raise RideServiceUnavailable("Ride Service Unavailable")
    
def cache_geometry(ride_id, geometry):
    try:
        jcache = json.dumps(geometry)
        r.set(f"geometry:{ride_id}",jcache,ex=600)
    except ConnectionError:
        raise RideServiceUnavailable("Ride Service Unavailable")

def get_cache_geometry(ride_id):
    try:
        jcache = r.get(f"geometry:{ride_id}")
        if jcache:
            geometry = json.loads(jcache)
            return geometry
        else:
            raise RideServiceUnavailable("Estimate data has expired or not present!")
    except ConnectionError:
        raise RideServiceUnavailable("Ride Service Unavailable")

def driver_to_front_of_queue(stand_id, driver_id):
    try:
        result = r.zrange(f"queue:stand:{stand_id}", 0, 0, withscores=True)
        if result:
            lowest_score = int(result[0][1]) - 1000
        else:
            lowest_score = 0
        r.zadd(f'queue:stand:{stand_id}', {str(driver_id): lowest_score})
    except ConnectionError:
        raise QueueServiceUnavailable("Queue Service Unavailable")