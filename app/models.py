# This file is responsible for creating and managing the User model and forms
# for registration/login, changing password, username, school, and dorm

from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError

from .extensions import db


# Define the User model
# This will be used to store user information in the database
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    school = db.Column(db.String(100), nullable=True)
    dorm = db.Column(db.String(100), nullable=True)


# Form for user registration with validation
class RegistrationForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=2, max=20)],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=6, max=20)],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField("Register")

    # Check if the username already exists
    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError("Username already exists!")


# Form for user login with validation
class LoginForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=2, max=20)],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=6, max=20)],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField("Login")


# Form for selecting a school
class SchoolSelectionForm(FlaskForm):
    school = SelectField(
        "Select your school",
        choices=[("University 1", "University 1")],
        validators=[InputRequired()],
    )
    dorm = SelectField(
        "Select your dorm",
        choices=[("Dorm 1", "Dorm 1"), ("Dorm 2", "Dorm 2")],
        validators=[InputRequired()],
    )
    submit = SubmitField("Continue")


# Form for changing password with validation
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        validators=[InputRequired(), Length(min=6, max=20)],
        render_kw={"placeholder": "Current Password"},
    )
    new_password = PasswordField(
        validators=[InputRequired(), Length(min=6, max=20)],
        render_kw={"placeholder": "New Password"},
    )

    submit = SubmitField("Change Password", name="submit_password")


# Form for changing username with validation
class ChangeUsernameForm(FlaskForm):
    current_username = StringField(
        validators=[InputRequired(), Length(min=1, max=20)],
        render_kw={"placeholder": "Current Username"},
    )
    new_username = StringField(
        validators=[InputRequired(), Length(min=1, max=20)],
        render_kw={"placeholder": "New Username"},
    )

    submit = SubmitField("Change Username", name="submit_username")


# Form for changing school
class ChangeSchoolForm(FlaskForm):
    school = SelectField(
        "Select your school",
        choices=[("University 1", "University 1")],
        validators=[InputRequired()],
    )
    submit = SubmitField("Change School", name="submit_school")


# Form for changing dorm
class ChangeDormForm(FlaskForm):
    dorm = SelectField(
        "Select your dorm",
        choices=[("Dorm 1", "Dorm 1"), ("Dorm 2", "Dorm 2")],
        validators=[InputRequired()],
    )
    submit = SubmitField("Change Dorm", name="submit_dorm")
