# Q-Drop Architecture

## Overview

Q-Drop is built as a Flask application with Jinja2-rendered frontend pages and background scheduler jobs for SMS notifications.

## Components

- **Browser / Jinja Templates**: `app/templates` and subfolders contain HTML pages rendered by Flask.
- **Flask routes / blueprints**: `app/home_page/routes.py`, `app/showers/routes.py`, and `app/laundry/routes.py` define request handling.
- **Service functions**: `app_queue/services.py` and `sms_messaging/services.py` contain business logic and Twilio integration.
- **SQLAlchemy ORM**: `app/models.py` and `app_queue/models.py` define persisted models.
- **PostgreSQL**: configured via `SQLALCHEMY_DATABASE_URI` and stores users and queue entries.
- **APScheduler**: configured in `app/__init__.py` to periodically send reminders and appointment notifications.

## Text architecture diagram

Browser / Jinja Templates -> Flask routes / blueprints -> service functions -> SQLAlchemy ORM -> PostgreSQL
APScheduler -> QueueEntry records -> Twilio SMS notifications

## Request flow

1. The browser requests an endpoint.
2. Flask routes parse input, validate forms, and call service functions.
3. Service functions query or write database state through SQLAlchemy.
4. Flask renders a template or redirects the user.

## Background jobs

- `send_reminder_message`: scans upcoming queue entries and sends Twilio reminders.
- `send_appointment_message`: sends appointment notifications for entries within the current time window and removes them from the queue.

## Data flow

- User and queue data are persisted in PostgreSQL.
- The queue model uses a single `QueueEntry` table for showers, washers, and dryers.
- SMS notification records are managed by updating `QueueEntry.last_reminder_time` and deleting entries after appointments.
