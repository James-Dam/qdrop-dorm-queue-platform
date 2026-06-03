import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from sqlalchemy import func
from twilio.rest import Client

from app.extensions import db
from app_queue.models import QueueEntry

# load environment variables from .env file
load_dotenv()

# .env variables
ENABLE_SMS = os.environ.get("ENABLE_SMS", "true").strip().lower() in ("1", "true", "yes")
ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")
PERSONAL_NUMBER = os.environ.get("PERSONAL_NUMBER")

TWILIO_ENABLED = ENABLE_SMS and ACCOUNT_SID and AUTH_TOKEN and TWILIO_PHONE_NUMBER
client = Client(ACCOUNT_SID, AUTH_TOKEN) if TWILIO_ENABLED else None


def _log_sms_fallback(to_number, body, message_type="SMS", app=None):
    log_message = (
        f"SMS disabled or credentials unavailable. Would send {message_type} to {to_number}: {body}"
    )
    if app is not None:
        app.logger.info(log_message)
    else:
        print(log_message)


def _send_sms(body, to_number, app=None, message_type="SMS"):
    if not TWILIO_ENABLED:
        _log_sms_fallback(to_number, body, message_type, app=app)
        return True
    try:
        client.messages.create(body=body, from_=TWILIO_PHONE_NUMBER, to=to_number)
        return True
    except Exception as e:
        error_message = f"Error occurred sending {message_type} to {to_number}: {e}"
        if app is not None:
            app.logger.error(error_message)
        else:
            print(error_message)
        return False


def send_confirmation_message(phone_number, event, registration_time, duration):
    """
    Notifies user through sms about registration for a queue.

    Args:
        phone_number: Number to receive confirmation message.
        event: (shower, laundry)
        registration_time: Time of start of event.
        duration: duration

    Returns:
        bool: indication of success or failure.
        message = "You have registered to {event} at {registration_time} with a duration of {duration} minutes!"
    """
    body = f"Hello! You have registered to {event} at {registration_time}!"
    return _send_sms(body, phone_number, message_type="registration confirmation")


def send_reminder_message(app):
    """
    Reminders user of upcoming appointment (sent in intervals).
    """
    print(
        f"--- send_reminder_message job triggered at {datetime.now(timezone.utc)} ---"
    )  # Debug print

    with app.app_context():
        REMINDER_30_MINUTES = 30
        # Cooldown for sending reminders
        REMINDER_THRESHOLD_MINUTES = 15
        current_utc_time = datetime.now(timezone.utc)

        # Define the window for upcoming appointments
        reminder_window_start = current_utc_time
        reminder_window_end = current_utc_time + timedelta(minutes=REMINDER_30_MINUTES)

        app.logger.info(
            f"Reminder window: {reminder_window_start} to {reminder_window_end}"
        )

        # Fetch entries that are approaching within the reminder window,
        # and haven't had a reminder sent within the cooldown period
        # or never had a reminder sent
        try:
            entries_for_reminders = (
                QueueEntry.query.filter(
                    QueueEntry.registration_time > reminder_window_start,
                    QueueEntry.registration_time <= reminder_window_end,
                    (QueueEntry.last_reminder_time == None)
                    | (
                        QueueEntry.last_reminder_time
                        < current_utc_time
                        - timedelta(minutes=REMINDER_THRESHOLD_MINUTES)
                    ),
                )
                .order_by(QueueEntry.event_type, QueueEntry.position)
                .all()
            )

            app.logger.info(
                f"Found {len(entries_for_reminders)} entries for reminders."
            )

            if not entries_for_reminders:
                app.logger.info(
                    "No entries found within the reminder window or cooldown period."
                )

            for entry in entries_for_reminders:
                time_difference = entry.registration_time - current_utc_time
                minutes = time_difference.total_seconds() / 60

                if 0 < minutes <= REMINDER_30_MINUTES:
                    body = (
                        f"Reminder: You have registered to {entry.event_type} at {entry.display_time}, "
                        f"{int(minutes)} minutes from now. Your current position is {entry.position}."
                    )
                    if _send_sms(body, entry.phone_number, app=app, message_type="reminder"):
                        entry.last_reminder_time = current_utc_time
                        db.session.add(entry)
                        db.session.commit()
                        app.logger.info(
                            f"Successfully sent reminder message to {entry.phone_number} for {entry.event_type}. Updated last_reminder_time."
                        )
                    else:
                        db.session.rollback()
                else:
                    app.logger.info(
                        f"Entry {entry.id} ({entry.event_type}) did not meet the exact time criteria for sending reminder ({minutes} minutes remaining)."
                    )

        except Exception as e:
            app.logger.error(
                f"Error occurred during send_reminder_message query or processing: {e}"
            )
            db.session.rollback()

    return True


def send_appointment_message(app):
    """
    Notifies user about appointment currently happening.
    """
    print(
        f"--- send_appointment_message job triggered at {datetime.now(timezone.utc)} ---"
    )  # Debug print

    with app.app_context():
        current_utc_time = datetime.now(timezone.utc)

        # Define a small window for time around starting time (e.g., 30 seconds before and after)
        time_window_start = current_utc_time - timedelta(seconds=30)
        time_window_end = current_utc_time + timedelta(seconds=30)

        app.logger.info(f"Appointment window: {time_window_start} to {time_window_end}")

        # Query for those with times between the window to send message
        try:
            appointments_to_process = QueueEntry.query.filter(
                QueueEntry.registration_time >= time_window_start,
                QueueEntry.registration_time <= time_window_end,
            ).all()

            app.logger.info(
                f"Found {len(appointments_to_process)} appointments to process."
            )

            if not appointments_to_process:
                app.logger.info("No appointments found within the current time window.")

            for appointment in appointments_to_process:
                try:
                    body = (
                        f"The {appointment.event_type} you have registered for will be taking place right now! Have Fun!"
                    )
                    send_success = _send_sms(
                        body,
                        appointment.phone_number,
                        app=app,
                        message_type="appointment notification",
                    )

                    event_type_for_update = appointment.event_type
                    position_of_removed = appointment.position

                    # Remove user from database after message
                    db.session.delete(appointment)
                    db.session.commit()
                    app.logger.info(
                        f"Entry {appointment.id} ({appointment.phone_number}) for {appointment.event_type} removed from queue."
                    )

                    # Deincrement all positions by 1 for the same event type and greater positions
                    QueueEntry.query.filter(
                        QueueEntry.event_type == event_type_for_update,
                        QueueEntry.position > position_of_removed,
                    ).update(
                        {QueueEntry.position: QueueEntry.position - 1},
                        synchronize_session="fetch",
                    )

                    db.session.commit()
                    app.logger.info(
                        f"Positions for {event_type_for_update} after position {position_of_removed} decremented."
                    )
                    if send_success:
                        app.logger.info(
                            "Successful sending appointment message and queue update!"
                        )
                    else:
                        app.logger.warning(
                            "Appointment processing completed without SMS delivery."
                        )

                except Exception as e:
                    app.logger.error(
                        f"Error occurred sending appointment message or updating queue for entry {appointment.id}: {e}"
                    )
                    db.session.rollback()
        except Exception as e:
            app.logger.error(
                f"Error occurred during send_appointment_message query: {e}"
            )
            db.session.rollback()

    return True


def send_cancellation_message(phone_number, event, registration_time):
    """
    Notifies user about a cancellation of an event
    """
    body = f"You have cancelled the {event} taking place at {registration_time}!"
    return _send_sms(body, phone_number, message_type="cancellation")
