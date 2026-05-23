# This file is the blueprint initialization for home page routes

from flask import Blueprint

# Create a Blueprint for routes relating to registration/login page
home_bp = Blueprint("home", __name__)

# Importing routes so that they register with the blueprint
from . import routes
