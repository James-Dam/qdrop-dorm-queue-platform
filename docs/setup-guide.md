# Setup Guide

## Local development setup

1. Install dependencies:
   ```bash
   py -3 -m pip install -r requirements.txt
   ```

2. Create a PostgreSQL database and user.

3. Create a `.env` file in the repository root with the following variables:
   - `SECRET_KEY`
   - `SQLALCHEMY_DATABASE_URI`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`
   - `PERSONAL_NUMBER`

4. Run migrations:
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
