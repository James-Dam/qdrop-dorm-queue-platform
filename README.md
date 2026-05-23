# Q-Drop Dorm Queue Platform

## Project overview

Q-Drop is a student dorm queue management platform for shower and laundry booking. It centralizes shared facility reservations, maintains queue positions, and sends SMS notifications to keep dorm residents informed about their scheduled appointments.

## Tech stack

- Python 3.13
- Flask
- Flask-SQLAlchemy / SQLAlchemy
- Flask-Migrate
- PostgreSQL
- Twilio SMS

## Architecture / full-stack flow

Browser / Jinja Templates -> Flask routes / blueprints -> service functions -> SQLAlchemy ORM -> PostgreSQL
APScheduler -> QueueEntry records -> Twilio SMS notifications

### How the flow works

1. Browser requests a route.
2. Flask routes render Jinja templates or handle form submissions.
3. Service functions perform queue logic and database operations.
4. SQLAlchemy persists records in PostgreSQL.
5. Background scheduler jobs send SMS messages using Twilio.

## Key features

- User registration and login
- School and dorm selection
- Dashboard with queue status and upcoming bookings
- Shower, washer, and dryer scheduling workflows
- SMS confirmation, reminder, appointment, and cancellation notifications
- Queue position management and availability checks
- Background scheduler for automated notifications

## User flow

1. Register or log in.
2. Select school and dorm if not already configured.
3. View the dashboard and machine availability.
4. Choose a shower, washer, or dryer.
5. Select an available 30-minute time slot.
6. Submit phone number and receive SMS confirmation.
7. Receive automated reminders and appointment alerts.

## Backend flow

- `app/home_page/routes.py` handles authentication, dashboard views, settings, and cancel actions.
- `app/showers/routes.py` and `app/laundry/routes.py` render schedules and process booking forms.
- `app_queue/services.py` determines availability, manages bookings, and updates queue positions.
- `sms_messaging/services.py` sends confirmation, reminder, appointment, and cancellation SMS.
- `app/__init__.py` initializes Flask, registers blueprints, and starts APScheduler jobs.

## Database models

- `User`: stores username, password hash, school, and dorm.
- `QueueEntry`: stores phone number, event type, booking time, duration, queue position, last reminder time, and display data.

## SMS notification flow

- Confirmation SMS is sent immediately after a booking is created.
- `send_reminder_message` runs regularly to notify users before their booking.
- `send_appointment_message` runs regularly to notify users when their event starts and removes the entry from the queue.

## Known limitations

- Twilio trial accounts may require verified recipient phone numbers.
- The school/dorm dataset is sample data, not a complete U.S. college/dorm dataset.
- Production deployment would require stronger validation, monitoring, and notification-provider setup.

## Running locally

1. Install dependencies:
   ```bash
   py -3 -m pip install -r requirements.txt
   ```
2. Create a PostgreSQL database.
3. Create a `.env` file with the required environment variables.
4. Run Flask migrations with `flask db upgrade` or your preferred migration flow.
5. Start the app:
   ```bash
   py -3 run.py
   ```

## Environment variables

- `SECRET_KEY`
- `SQLALCHEMY_DATABASE_URI`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `PERSONAL_NUMBER`

## Future improvements

- Add form-level and route-level validation for all input fields.
- Move SMS delivery to a dedicated background worker or job queue.
- Add structured logging, metrics, and error monitoring.
- Expand school and dorm data to a normalized dataset.
- Harden authentication, session security, and rate limiting.
## Documentation and screenshots

- Additional documentation is available in the `docs/` directory.
- Example screenshot assets can be stored in the `screenshots/` directory.
