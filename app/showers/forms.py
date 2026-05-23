# This file is responsible for creating the forms for the shower blueprint,
# like registering for a shower

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import InputRequired, Length, NumberRange, ValidationError

COMMON_TIMEZONES = [
    ("America/Los_Angeles", "PST (Pacific Standard Time)"),
    ("America/Denver", "MST (Mountain Standard Time)"),
    ("America/Chicago", "CST (Central Standard Time)"),
    ("America/New_York", "EST (Eastern Standard Time)"),
    ("America/Phoenix", "MST (Arizona - No DST)"),  # Special case for Arizona
]


# Form for event registration with validation
class EventRegistrationForm(FlaskForm):
    phone_number = StringField(
        validators=[InputRequired(), Length(min=2, max=20)],
        render_kw={"placeholder": "Phone Number (e.g. +12223334444)"},
    )
    time_zone = SelectField(
        "Your Time Zone",
        choices=COMMON_TIMEZONES,
        validators=[InputRequired()],
        default="America/Los_Angeles",
    )
    submit = SubmitField("Register")
