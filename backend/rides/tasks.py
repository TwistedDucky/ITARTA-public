import logging
from celery import shared_task
from rides.models import DriverRequest, Ride
from core.redis_client import add_to_queue

logger = logging.getLogger(__name__)


@shared_task
def driver_timeout_task(ride_id, driver_request_id):
    logger.info(
        "[TIMEOUT TASK] Fired | ride_id=%s | driver_request_id=%s",
        ride_id, driver_request_id
    )

    from rides.services import dispatch_ride

    try:
        driver_request = DriverRequest.objects.get(id=driver_request_id)
    except DriverRequest.DoesNotExist:
        logger.warning(
            "[TIMEOUT TASK] DriverRequest not found, likely already handled | driver_request_id=%s",
            driver_request_id
        )
        return

    logger.info(
        "[TIMEOUT TASK] DriverRequest status before update | driver_request_id=%s | status=%s | driver_id=%s",
        driver_request_id, driver_request.status, driver_request.driver_id
    )

    driver_request.status = 'TD'
    driver_request.save()
    logger.info(
        "[TIMEOUT TASK] DriverRequest marked as timed out (TD) | driver_request_id=%s",
        driver_request_id
    )

    try:
        ride = Ride.objects.get(id=ride_id)
    except Ride.DoesNotExist:
        logger.error(
            "[TIMEOUT TASK] Ride not found | ride_id=%s | driver_request_id=%s",
            ride_id, driver_request_id
        )
        return

    logger.info(
        "[TIMEOUT TASK] Pushing driver back to queue | driver_id=%s | stand_id=%s | ride_id=%s",
        driver_request.driver.id, ride.assigned_stand.id, ride_id
    )
    add_to_queue(ride.assigned_stand.id, driver_request.driver.id)

    logger.info(
        "[TIMEOUT TASK] Re-triggering dispatch | ride_id=%s",
        ride_id
    )
    dispatch_ride(ride=ride)