# This file is for running the Flask application
import os

from dotenv import load_dotenv
from flask import Flask, session
from flask_apscheduler import APScheduler

from sms_messaging.services import send_appointment_message, send_reminder_message

from .extensions import bcrypt, db, login_manager, migrate
from .models import User

# Load environment variables from .env
load_dotenv()


# Get .env variables
SECRET_KEY = os.environ.get("SECRET_KEY")
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")


def create_app():
    """
    Create Flask app
    """
    app = Flask(__name__)

    # App configurations
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SCHEDULER_API_ENABLED"] = True

    # Initialize entensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "home.login"
    migrate.init_app(app, db)

    # Initialize scheduler
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    scheduler.add_job(
        id="send_reminders",
        func=send_reminder_message,
        trigger="interval",
        minutes=1,
        args=[app],
    )
    scheduler.add_job(
        id="send_appointments",
        func=send_appointment_message,
        trigger="interval",
        seconds=30,
        args=[app],
    )

    # Loads user for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize password hashing extension
    bcrypt.init_app(app)

    # Register blueprint for home page routes
    from .home_page import home_bp

    app.register_blueprint(home_bp)

    # Register blueprint for showers routes
    from .showers import shower_bp

    app.register_blueprint(shower_bp)

    # Register blueprint for /sms route
    from sms_messaging import sms_bp

    app.register_blueprint(sms_bp)

    # Register blueprint for laundry routes
    from .laundry import laundry_bp

    app.register_blueprint(laundry_bp)

    return app
