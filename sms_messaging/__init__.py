from flask import Blueprint

# create blueprint for /sms route
sms_bp = Blueprint("sms", __name__, url_prefix="/sms", template_folder="templates")


# importing all .py files
from . import services
