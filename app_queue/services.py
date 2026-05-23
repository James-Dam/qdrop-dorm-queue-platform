# This file is responsible for services involving the queue db, like adding to queue,
# checking if a machine is available, cancelling a booking, and getting
# upcoming bookings

from datetime import datetime

from flask_login import current_user
from sqlalchemy import asc, func

from app import db
from app_queue.models import QueueEntry


def add_to_queue(
    phone_number: str,
    event: str,
    shower_id: int,
    registration_time: str,
    duration: int,
    clicked_time,
    display_time,
):
    """
    Adds user to queue db with position and id
    """

    # Convert registratoin time back into a from that the db would accept
    today = datetime.now().strftime("%Y-%m-%d")
    registration_time = datetime.strptime(
        f"{today} {registration_time}", "%Y-%m-%d %H:%M:%S"
    )

    # Scan for highest position and increment
    max_position = (
        db.session.query(func.max(QueueEntry.position))
        .filter_by(event_type=event)
        .scalar()
    )
    new_position = (max_position or 0) + 1

    # Check for existing phone number for certain event
    existing_entry = QueueEntry.query.filter_by(
        phone_number=phone_number, event_type=event
    ).first()
    if existing_entry:
        raise Exception(
            f"Phone number {phone_number} is already in the queue for {event} "
            f"at position {existing_entry.position}."
        )

    new_queue_entry = QueueEntry(
        phone_number=phone_number,
        event_type=event,
        registration_time=registration_time,
        duration=duration,
        position=new_position,
        clicked_time=clicked_time,
        display_time=display_time,
        shower_id=shower_id,
        user_id=current_user.id,
    )

    # Save to db
    db.session.add(new_queue_entry)
    db.session.commit()
    print(
        f"{phone_number} has registered to {event} at shower {shower_id} "
        f"at time {registration_time} with duration {duration}."
    )
    print(new_queue_entry)


def shower_available(shower_id, time_slot):

    today = datetime.now().date()

    # Check if shower is booked at a certain time
    booking = QueueEntry.query.filter(
        QueueEntry.shower_id == shower_id,
        QueueEntry.clicked_time == time_slot,
        QueueEntry.event_type == "shower",
        func.date(QueueEntry.registration_time) == today,
    ).first()

    if booking:
        return False
    else:
        return True


def machine_available(machine_id, time_slot, event_type):

    today = datetime.now().date()

    # Check if machine is booked at a certain time
    booking = QueueEntry.query.filter(
        QueueEntry.shower_id == machine_id,
        QueueEntry.clicked_time == time_slot,
        QueueEntry.event_type == event_type,
        func.date(QueueEntry.registration_time) == today,
    ).first()

    if booking:
        return False
    else:
        return True


def cancel_queue(queue_id, user_id):

    # Check if booking exists
    booking = QueueEntry.query.filter_by(id=queue_id, user_id=user_id).first()

    if booking:
        phone_number = booking.phone_number
        event = booking.event_type
        time = booking.display_time

        db.session.delete(booking)
        db.session.commit()
        return (True, [phone_number, event, time])
    else:
        return False


# Gets how many shower/washer/dryer are currently at the moment
def available_count(event_type):

    today = datetime.now().date()

    # Creating a 30 minute time window to check for bookings
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute

    # if its 10:15, it would check the 10:30 and 11:00 time
    if current_minute < 30:
        slot1 = f"{current_hour:02d}:30"
        next_hour = (current_hour + 1) % 24
        slot2 = f"{next_hour:02d}:00"
    else:
        # if its 10:45, it would check the 11:00 and 11:30 time
        next_hour = (current_hour + 1) % 24
        slot1 = f"{next_hour:02d}:00"
        slot2 = f"{next_hour:02d}:30"

    # Get all bookings for the 00:30 and 01:00
    slot1_booked = QueueEntry.query.filter(
        QueueEntry.event_type == event_type,
        QueueEntry.clicked_time == slot1,
        func.date(QueueEntry.registration_time) == today,
    ).all()

    # Get all bookings for the 01:00 and 01:30
    slot2_booked = QueueEntry.query.filter(
        QueueEntry.event_type == event_type,
        QueueEntry.clicked_time == slot2,
        func.date(QueueEntry.registration_time) == today,
    ).all()

    # Whichever slot has less available machines, return that number
    return min(4 - len(slot1_booked), 4 - len(slot2_booked))


def upcoming_bookings():
    today = datetime.now().date()

    # Creating a 30 minute time window to check for bookings
    current_hour = datetime.now().hour
    current_minute = 30 if datetime.now().minute > 30 else 0
    current_time_slot = f"{current_hour:02d}:{current_minute:02d}"

    # Get the next 3 bookings
    upcoming_bookings = (
        QueueEntry.query.filter(
            func.date(QueueEntry.registration_time) == today,
            QueueEntry.clicked_time >= current_time_slot,
        )
        .order_by(QueueEntry.clicked_time)
        .limit(3)
        .all()
    )

    return upcoming_bookings


def next_available_time(event_type):
    today = datetime.now().date()

    current_hour = datetime.now().hour
    current_time = datetime.now().strftime("%H:%M")

    # Make list of all possible times for the day
    time_slots = []
    for hour in range(current_hour, 24):
        for minute in [0, 30]:
            time = f"{hour:02d}:{minute:02d}"
            # Add time to list only if its after the current time were checking
            if time >= current_time:
                time_slots.append(time)

    # Now check each time to see which is next available
    for time_slot in time_slots:
        # Get the available machine id for the time slot
        machine_id = get_machine_id(event_type, time_slot)
        if machine_id:
            return {
                "time_slot": datetime.strptime(time_slot, "%H:%M").strftime("%I:%M %p"),
                "machine_id": machine_id,
            }

    # If no time slots are available, return None
    return None


# Helper function to get the machine id for a given time slot
def get_machine_id(event_type, time_slot):
    today = datetime.now().date()

    # Get all bookings for this time slot
    booked = QueueEntry.query.filter(
        QueueEntry.event_type == event_type,
        QueueEntry.clicked_time == time_slot,
        func.date(QueueEntry.registration_time) == today,
    ).all()

    # Get all the i'ds of the booked machines
    booked_machine_ids = [booking.shower_id for booking in booked]

    # Find the first available machine id
    for machine_id in range(1, 5):
        # If the machine ID is not in booked, we know its available
        if machine_id not in booked_machine_ids:
            return machine_id

    return None
