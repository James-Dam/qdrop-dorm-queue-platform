# Setup Guide

## Local development setup

1. Install dependencies:
   ```bash
   py -3 -m pip install -r requirements.txt
   ```

2. Start the app directly for a local demo:
   ```bash
   py -3 run.py
   ```

No `.env` file is required for the demo. The app will automatically use a local SQLite database at `qdrop.db` and will log SMS content instead of sending real messages when Twilio credentials are not configured.

### Optional PostgreSQL / Twilio setup

If you want a full database and SMS backend, create a `.env` file in the repository root with:
- `SECRET_KEY`
- `SQLALCHEMY_DATABASE_URI`
- `ENABLE_SMS` (optional; defaults to `true`)
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `PERSONAL_NUMBER`

When `SQLALCHEMY_DATABASE_URI` is omitted, local SQLite is used. When `ENABLE_SMS=false`, the app logs SMS messages instead of sending them.

4. If you use PostgreSQL, run migrations:
   ```bash
   flask db upgrade
   ```

5. Start the Flask app:
   ```bash
   py -3 run.py
   ```

## Notes

- Use a Twilio trial account only for development, and verify phone numbers if required.
- The sample school and dorm options are hard-coded and intended for demo use.
- The scheduler runs inside Flask via `Flask-APScheduler`, so the app process should remain active.
