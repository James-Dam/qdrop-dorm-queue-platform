# This file is responsible for creating different routes for the home blueprint

from datetime import datetime, timedelta

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import bcrypt, db
from app.models import (
    ChangeDormForm,
    ChangePasswordForm,
    ChangeSchoolForm,
    ChangeUsernameForm,
    LoginForm,
    RegistrationForm,
    SchoolSelectionForm,
    User,
)
from app_queue.models import QueueEntry
from app_queue.services import (
    available_count,
    cancel_queue,
    next_available_time,
    upcoming_bookings,
)
from sms_messaging.services import send_cancellation_message

from . import home_bp


@home_bp.route("/")
def home():
    return render_template("home.html")


# login route  - allows users to log in
@home_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        # If user exists and password matches
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)

            # Check if user has chosen a school
            if current_user.school and current_user.dorm:
                return redirect(url_for("home.dashboard"))
            else:
                return redirect(url_for("home.select_school"))
        else:
            # Show error msg for wrong username or password
            return render_template(
                "login.html", form=form, error="Invalid username or password"
            )

    # Show login form again if failed form
    return render_template("login.html", form=form)


# Registration route - allows new users to register
@home_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        # Hash password before storing in db
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )

        # Create new user with hashed password
        new_user = User(username=form.username.data, password=hashed_password)

        # Save to db
        db.session.add(new_user)
        db.session.commit()

        print("REGISTER PW: ", hashed_password)

        # Redirect to login page
        return redirect(url_for("home.login"))

    # Show registration page if form validation fails
    return render_template("register.html", form=form)


# School selection route - users select their school
@home_bp.route("/select-school", methods=["GET", "POST"])
@login_required
def select_school():
    form = SchoolSelectionForm()

    # If submitted form is valid, add school to users db
    if form.validate_on_submit():
        current_user.school = form.school.data
        current_user.dorm = form.dorm.data
        db.session.commit()
        return redirect(url_for("home.dashboard"))

    return render_template("select_school.html", form=form)


# Dashboard route - requires user to be logged in
@home_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    # Get how many showers/washers/dryers are available in given moment
    shower_count = available_count("shower")
    washer_count = available_count("washer")
    dryer_count = available_count("dryer")

    # Getting current queue entries of user
    today = datetime.now().date()
    queue_entries = QueueEntry.query.filter(
        QueueEntry.user_id == current_user.id, QueueEntry.registration_time >= today
    ).all()

    return render_template(
        "dashboard.html",
        queue_entries=queue_entries,
        timedelta=timedelta,
        datetime=datetime,
        shower_count=shower_count,
        washer_count=washer_count,
        dryer_count=dryer_count,
        upcoming_bookings=upcoming_bookings(),
        next_available_time_shower=next_available_time("shower"),
        next_available_time_washer=next_available_time("washer"),
        next_available_time_dryer=next_available_time("dryer"),
    )


# Logout route - allows users to log out (need to be logged in)
@home_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("home.login"))


# Settings route - requires user to be logged in
@home_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """
    Allows user to change settings (username, password), saves to database
    """
    username_form = ChangeUsernameForm()
    password_form = ChangePasswordForm()
    change_school_form = ChangeSchoolForm()
    change_dorm_form = ChangeDormForm()

    # Check whether username or password has been changed
    if username_form.validate_on_submit() and "submit_username" in request.form:
        # Check if current_username matches logged-in user's username
        if username_form.current_username.data != current_user.username:
            print("ERROR: Current username does not match.")
            return render_template(
                "settings.html",
                user=current_user,
                username_form=username_form,
                password_form=password_form,
                change_school_form=change_school_form,
                change_dorm_form=change_dorm_form,
                error="Incorrect username.",
            )
        else:
            # Check if new_username is already taken by another user
            existing_user = User.query.filter_by(
                username=username_form.new_username.data
            ).first()
            if existing_user and existing_user.id != current_user.id:
                print("ERROR: New username is already taken.")
                return render_template(
                    "settings.html",
                    user=current_user,
                    username_form=username_form,
                    password_form=password_form,
                    change_school_form=change_school_form,
                    change_dorm_form=change_dorm_form,
                    error="Username already taken.",
                )
            else:
                # Update username
                current_user.username = username_form.new_username.data
                db.session.commit()
                print("SUCCESS: Username updated successfully.")
                return redirect(url_for("home.settings"))

    # Handle password change form submission
    if password_form.validate_on_submit() and "submit_password" in request.form:
        # Check if current_password matches logged-in user's password
        if not bcrypt.check_password_hash(
            current_user.password, password_form.current_password.data
        ):
            print("ERROR: Current password does not match.")
            return render_template(
                "settings.html",
                user=current_user,
                username_form=username_form,
                password_form=password_form,
                change_school_form=change_school_form,
                change_dorm_form=change_dorm_form,
                error="Incorrect password. Try again.",
            )
        else:
            # Hash and update new password
            hashed_new_password = bcrypt.generate_password_hash(
                password_form.new_password.data
            ).decode("utf-8")
            current_user.password = hashed_new_password
            db.session.commit()
            print("SUCCESS: Password updated successfully.")
            return redirect(url_for("home.settings"))

    # If user changes school
    if change_school_form.validate_on_submit() and "submit_school" in request.form:
        current_user.school = change_school_form.school.data
        db.session.commit()
        return redirect(url_for("home.settings"))

    # If user changes dorm
    if change_dorm_form.validate_on_submit() and "submit_dorm" in request.form:
        current_user.dorm = change_dorm_form.dorm.data
        db.session.commit()
        return redirect(url_for("home.settings"))

    return render_template(
        "settings.html",
        user=current_user,
        username_form=username_form,
        password_form=password_form,
        change_school_form=change_school_form,
        change_dorm_form=change_dorm_form,
    )


# Cancel Booking route - lets a user cancel their booking through the dashboard
@home_bp.route("/cancel-booking/<int:booking_id>", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    # If user has booking then cancel
    cancellation = cancel_queue(booking_id, current_user.id)
    if cancellation[0]:
        flash("Your booking has been cancelled successfully.", "success")
        send_cancellation_message(
            cancellation[1][0], cancellation[1][1], cancellation[1][2]
        )
    else:
        flash("Unable to cancel booking.", "error")

    return redirect(url_for("home.dashboard"))
