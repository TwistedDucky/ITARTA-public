import os
import logging
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import datetime

logger = logging.getLogger(__name__)

# Initialize Firebase exactly once
if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.join(settings.BASE_DIR, 'serviceAccountKey.json'))
    firebase_admin.initialize_app(cred)
    logger.info("[FCM] Firebase app initialized")


def send_ride_request_notification(driver, ride):
    """
    Sends a silent data push to the driver's device to trigger the 'Incoming Ride' UI.
    """
    logger.info(
        "[FCM] Preparing ride request notification | ride_id=%s | driver_id=%s | driver_phone=%s",
        ride.id, driver.id, driver.phone_number
    )

    if not driver.fcm_token:
        logger.warning(
            "[FCM] No FCM token for driver, skipping | ride_id=%s | driver_id=%s | driver_phone=%s",
            ride.id, driver.id, driver.phone_number
        )
        return False

    message = messaging.Message(
        data={
            'type': 'NEW_RIDE_REQUEST',
            'ride_id': str(ride.id),
        },
        token=driver.fcm_token,
        android=messaging.AndroidConfig(
            priority='high',
            ttl=datetime.timedelta(seconds=30)
        )
    )

    try:
        response = messaging.send(message)
        logger.info(
            "[FCM] Ride request sent successfully | ride_id=%s | driver_id=%s | fcm_response=%s | ttl=30s",
            ride.id, driver.id, response
        )
        return True
    except Exception as e:
        logger.error(
            "[FCM] Failed to send ride request | ride_id=%s | driver_id=%s | error=%s",
            ride.id, driver.id, str(e)
        )
        return False


def send_ride_accepted_notification(passenger, ride):
    """
    Sends a silent data push to the passenger's device to trigger the 'Ride Accepted' UI.
    """
    logger.info(
        "[FCM] Preparing ride accepted notification | ride_id=%s | passenger_id=%s | passenger_phone=%s",
        ride.id, passenger.id, passenger.phone_number
    )

    if not passenger.fcm_token:
        logger.warning(
            "[FCM] No FCM token for passenger, skipping | ride_id=%s | passenger_id=%s",
            ride.id, passenger.id
        )
        return False

    message = messaging.Message(
        data={
            'type': 'RIDE_REQUEST_ACCEPTED',
            'ride_id': str(ride.id),
            'driver_phone': str(ride.driver.phone_number),
        },
        token=passenger.fcm_token,
        android=messaging.AndroidConfig(
            priority='high',
            ttl=datetime.timedelta(seconds=30)
        )
    )

    try:
        response = messaging.send(message)
        logger.info(
            "[FCM] Ride accepted notification sent successfully | ride_id=%s | passenger_id=%s | fcm_response=%s",
            ride.id, passenger.id, response
        )
        return True
    except Exception as e:
        logger.error(
            "[FCM] Failed to send ride accepted notification | ride_id=%s | passenger_id=%s | error=%s",
            ride.id, passenger.id, str(e)
        )
        return False


def send_ride_completed_notification(passenger, ride):
    """
    Sends a silent data push to the passengers's device to trigger the 'Ride completed' UI.
    """
    logger.info(
        "[FCM] Preparing ride completed notification | ride_id=%s | passenger_id=%s",
        ride.id, passenger.id
    )

    if not passenger.fcm_token:
        logger.warning(
            "[FCM] No FCM token for passenger, skipping | ride_id=%s | passenger_id=%s",
            ride.id, passenger.id
        )
        return False

    message = messaging.Message(
        data={
            'type': 'RIDE_COMPLETED',
            'ride_id': str(ride.id),
        },
        token=passenger.fcm_token,
        android=messaging.AndroidConfig(
            priority='high',
            ttl=datetime.timedelta(seconds=30)
        )
    )

    try:
        response = messaging.send(message)
        logger.info(
            "[FCM] Ride completed notification sent successfully | ride_id=%s | passenger_id=%s | fcm_response=%s",
            ride.id, passenger.id, response
        )
        return True
    except Exception as e:
        logger.error(
            "[FCM] Failed to send ride completed notification | ride_id=%s | passenger_id=%s | error=%s",
            ride.id, passenger.id, str(e)
        )
        return False


def send_ride_cancelled_notification(driver, ride):
    """
    Sends a silent data push to the driver's device to trigger the 'Ride cancelled' UI.
    """
    logger.info(
        "[FCM] Preparing ride cancelled notification | ride_id=%s | driver_id=%s",
        ride.id, driver.id
    )

    if not driver.fcm_token:
        logger.warning(
            "[FCM] No FCM token for driver, skipping | ride_id=%s | driver_id=%s",
            ride.id, driver.id
        )
        return False

    message = messaging.Message(
        data={
            'type': 'RIDE_CANCELLED',
            'ride_id': str(ride.id),
        },
        token=driver.fcm_token,
        android=messaging.AndroidConfig(
            priority='high',
            ttl=datetime.timedelta(seconds=30)
        )
    )

    try:
        response = messaging.send(message)
        logger.info(
            "[FCM] Ride cancelled notification sent successfully | ride_id=%s | driver_id=%s | fcm_response=%s",
            ride.id, driver.id, response
        )
        return True
    except Exception as e:
        logger.error(
            "[FCM] Failed to send ride cancelled notification | ride_id=%s | driver_id=%s | error=%s",
            ride.id, driver.id, str(e)
        )
        return False