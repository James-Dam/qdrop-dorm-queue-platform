# This file is the blueprint initialization for the shower routes

from flask import Blueprint

# Create a Blueprint for routes relating to showers
shower_bp = Blueprint("showers", __name__)

# Importing routes so that they register with the blueprint
from . import forms, routes
