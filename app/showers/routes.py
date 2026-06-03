# This file is responsible for creating different routes for the shower blueprint

from datetime import datetime, timedelta
from flask import flash, redirect, render_template, request, session, url_for

from app_queue.models import QueueEntry
from app_queue.services import add_to_queue, shower_available
from app.booking_utils import generate_time_slot_groups, local_time_to_utc_datetime
from sms_messaging import services

from . import forms, shower_bp


@shower_bp.route("/showers")
def shower_list():
    return render_template("showers/showers.html")


# Show the schedule for a specific shower
@shower_bp.route("/showers/<int:shower_id>")
def shower_schedule(shower_id):
    time_groups = generate_time_slot_groups(shower_available, shower_id)

    return render_template(
        "showers/shower_schedule.html",
        shower_id=shower_id,
        **time_groups,
    )


# Book a specific shower
@shower_bp.route("/showers/<int:shower_id>/book", methods=["GET", "POST"])
def book_shower(shower_id):
    form = forms.EventRegistrationForm()
    if request.method == "POST" and "time_slot" in request.form:
        # Get time slot to put into db
        time_slot = request.form.get("time_slot")
        time_slot_display = request.form.get("time_slot_display")
        print(f"TIME SLOT: {time_slot}")
        print(f"TIME SLOT DISPLAY {time_slot_display}")

        session["booking"] = {
            "shower_id": shower_id,
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
        event = "shower"
        duration = 30

        booking_time_utc = local_time_to_utc_datetime(time_slot, time_zone)

        # Place info into db
        try:
            print(
                "Calling adding to queue",
                phone_number,
                event,
                shower_id,
                booking_time_utc,
                duration,
            )
            add_to_queue(
                phone_number,
                event,
                shower_id,
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
                "showers/register_event.html", form=form, error=e, shower_id=shower_id
            )
            print(e)

    return render_template(
        "showers/register_event.html", form=form, shower_id=shower_id
    )
