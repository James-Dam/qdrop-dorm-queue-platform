# This file is responsible for creating different routes for the laundry blueprint

from datetime import datetime, timedelta

import pytz
from flask import flash, redirect, render_template, request, session, url_for

from app.showers import forms
from app_queue.models import QueueEntry
from app_queue.services import add_to_queue, machine_available
from sms_messaging import services

from . import laundry_bp


@laundry_bp.route("/laundry")
def laundry_list():
    return render_template("laundry/machines.html")


# Show the schedule for a specific washer
@laundry_bp.route("/washer/<int:washer_id>")
def washer_schedule(washer_id):
    # Need to make all the possible times for booking | displays in regular 12-hour format
    early_morning = []
    morning = []
    afternoon = []
    evening = []
    for hour in range(24):
        for minute in [0, 30]:
            time_obj = datetime.strptime(f"{hour:02}:{minute:02}", "%H:%M")

            # We have to store the time differently for db vs. display

            db_time = time_obj.strftime("%H:%M")  # Use military time for db

            # Display time (1:00 PM - 1:30 PM)
            start_time = time_obj.strftime("%I:%M %p")
            end_time = (time_obj + timedelta(minutes=30)).strftime("%I:%M %p")

            # Dictionary to hold both formats
            time_slot_dict = {
                "db_value": db_time,
                "display_value": f"{start_time} - {end_time}",
                "available": machine_available(washer_id, db_time, "washer"),
            }

            # Times are determined by the hour
            if hour < 6:
                early_morning.append(time_slot_dict)
            elif hour < 12:
                morning.append(time_slot_dict)
            elif hour < 18:
                afternoon.append(time_slot_dict)
            else:
                evening.append(time_slot_dict)

    # Shows the details of a specific shower and pass in the time slots
    return render_template(
        "laundry/washer_schedule.html",
        washer_id=washer_id,
        early_morning=early_morning,
        morning=morning,
        afternoon=afternoon,
        evening=evening,
    )


# Show the schedule for a specific dryer
@laundry_bp.route("/dryer/<int:dryer_id>")
def dryer_schedule(dryer_id):
    # Need to make all the possible times for booking | displays in regular 12-hour format
    early_morning = []
    morning = []
    afternoon = []
    evening = []
    for hour in range(24):
        for minute in [0, 30]:
            time_obj = datetime.strptime(f"{hour:02}:{minute:02}", "%H:%M")

            # We have to store the time differently for db vs. display

            db_time = time_obj.strftime("%H:%M")  # Use military time for db

            # Display time (1:00 PM - 1:30 PM)
            start_time = time_obj.strftime("%I:%M %p")
            end_time = (time_obj + timedelta(minutes=30)).strftime("%I:%M %p")

            # Dictionary to hold both formats
            time_slot_dict = {
                "db_value": db_time,
                "display_value": f"{start_time} - {end_time}",
                "available": machine_available(dryer_id, db_time, "dryer"),
            }

            # Times are determined by the hour
            if hour < 6:
                early_morning.append(time_slot_dict)
            elif hour < 12:
                morning.append(time_slot_dict)
            elif hour < 18:
                afternoon.append(time_slot_dict)
            else:
                evening.append(time_slot_dict)

    # Shows the details of a specific dryer and pass in the time slots
    return render_template(
        "laundry/dryer_schedule.html",
        dryer_id=dryer_id,
        early_morning=early_morning,
        morning=morning,
        afternoon=afternoon,
        evening=evening,
    )


# Book a specific washer
@laundry_bp.route("/washer/<int:washer_id>/book", methods=["GET", "POST"])
def book_washer(washer_id):
    form = forms.EventRegistrationForm()
    if request.method == "POST" and "time_slot" in request.form:
        # Get time slot to put into db
        time_slot = request.form.get("time_slot")
        time_slot_display = request.form.get("time_slot_display")
        print(f"TIME SLOT: {time_slot}")
        print(f"TIME SLOT DISPLAY {time_slot_display}")

        session["booking"] = {
            "washer_id": washer_id,
            "time_slot": time_slot,
            "time_slot_display": time_slot_display,
        }

    if form.validate_on_submit():
        # Retrieve data from POST request
        booking_data = session.get("booking")

        time_slot = booking_data["time_slot"]
        time_slot_display = booking_data["time_slot_display"]
        phone_number = form.phone_number.data
        time_zone = form.time_zone.data
        event = "washer"
        duration = 30

        # CONVERT TIME AND TIME ZONE TO MATCH UTC TIME
        user_tz = pytz.timezone(time_zone)
        today_in_user_tz = datetime.now(user_tz).date()
        parsed_time = datetime.strptime(time_slot, "%H:%M").time()
        naive_datetime = datetime.combine(today_in_user_tz, parsed_time)
        localized_datetime = user_tz.localize(naive_datetime)
        booking_time_utc = localized_datetime.astimezone(pytz.utc)
        booking_time_utc = booking_time_utc.strftime("%H:%M:%S")

        # Place info into db
        try:
            print(
                "Calling adding to queue",
                phone_number,
                event,
                washer_id,
                booking_time_utc,
                duration,
            )
            add_to_queue(
                phone_number,
                event,
                washer_id,
                booking_time_utc,
                duration,
                time_slot,
                time_slot_display,
            )
            print("Added to queue successfully!")
            services.send_confirmation_message(
                phone_number, event, booking_time_utc, duration
            )
            flash(
                f"You have successfully registered to {event} at {time_slot_display}!",
                "success",
            )
            return redirect(url_for("home.dashboard"))
        except Exception as e:
            return render_template(
                "laundry/register_washer_event.html",
                form=form,
                error=e,
                washer_id=washer_id,
            )
            print(e)

    return render_template(
        "laundry/register_washer_event.html", form=form, washer_id=washer_id
    )


# Book a specific dryer
@laundry_bp.route("/dryer/<int:dryer_id>/book", methods=["GET", "POST"])
def book_dryer(dryer_id):
    form = forms.EventRegistrationForm()
    if request.method == "POST" and "time_slot" in request.form:
        # Get time slot to put into db
        time_slot = request.form.get("time_slot")
        time_slot_display = request.form.get("time_slot_display")
        print(f"TIME SLOT: {time_slot}")
        print(f"TIME SLOT DISPLAY {time_slot_display}")

        session["booking"] = {
            "dryer_id": dryer_id,
            "time_slot": time_slot,
            "time_slot_display": time_slot_display,
        }

    if form.validate_on_submit():
        # Retrieve data from POST request
        booking_data = session.get("booking")

        time_slot = booking_data["time_slot"]
        time_slot_display = booking_data["time_slot_display"]
        phone_number = form.phone_number.data
        time_zone = form.time_zone.data
        event = "dryer"
        duration = 30

        # CONVERT TIME AND TIME ZONE TO MATCH UTC TIME
        user_tz = pytz.timezone(time_zone)
        today_in_user_tz = datetime.now(user_tz).date()
        parsed_time = datetime.strptime(time_slot, "%H:%M").time()
        naive_datetime = datetime.combine(today_in_user_tz, parsed_time)
        localized_datetime = user_tz.localize(naive_datetime)
        booking_time_utc = localized_datetime.astimezone(pytz.utc)
        booking_time_utc = booking_time_utc.strftime("%H:%M:%S")

        # Place info into db
        try:
            print(
                "Calling adding to queue",
                phone_number,
                event,
                dryer_id,
                booking_time_utc,
                duration,
            )
            add_to_queue(
                phone_number,
                event,
                dryer_id,
                booking_time_utc,
                duration,
                time_slot,
                time_slot_display,
            )
            print("Added to queue successfully!")
            saved_entry = (
                QueueEntry.query.filter_by(phone_number=phone_number, event_type=event)
                .order_by(QueueEntry.id.desc())
                .first()
            )
            services.send_confirmation_message(
                phone_number, event, saved_entry.display_time, duration
            )
            flash(
                f"You have successfully registered to {event} at {time_slot_display}!",
                "success",
            )
            return redirect(url_for("home.dashboard"))
        except Exception as e:
            return render_template(
                "laundry/register_dryer_event.html",
                form=form,
                error=e,
                dryer_id=dryer_id,
            )
            print(e)

    return render_template(
        "laundry/register_dryer_event.html", form=form, dryer_id=dryer_id
    )
