# This file is responsible for creating different routes for the laundry blueprint

from datetime import datetime, timedelta
from flask import flash, redirect, render_template, request, session, url_for

from app.showers import forms
from app.booking_utils import generate_time_slot_groups, local_time_to_utc_datetime
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
    time_groups = generate_time_slot_groups(
        lambda item_id, db_time: machine_available(item_id, db_time, "washer"),
        washer_id,
    )

    return render_template(
        "laundry/washer_schedule.html",
        washer_id=washer_id,
        **time_groups,
    )


# Show the schedule for a specific dryer
@laundry_bp.route("/dryer/<int:dryer_id>")
def dryer_schedule(dryer_id):
    time_groups = generate_time_slot_groups(
        lambda item_id, db_time: machine_available(item_id, db_time, "dryer"),
        dryer_id,
    )

    return render_template(
        "laundry/dryer_schedule.html",
        dryer_id=dryer_id,
        **time_groups,
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

        booking_time_utc = local_time_to_utc_datetime(time_slot, time_zone)

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

        booking_time_utc = local_time_to_utc_datetime(time_slot, time_zone)

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
