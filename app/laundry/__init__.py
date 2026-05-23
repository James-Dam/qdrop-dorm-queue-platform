# This file is the blueprint initialization for the washer/dryer routes

from flask import Blueprint

# Create a Blueprint for routes relating to showers
laundry_bp = Blueprint("laundry", __name__)

# Importing routes so that they register with the blueprint
from . import routes
