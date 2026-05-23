# This file is for importing and initializing Flask extensions
# These extensions are used for db management,
# user authentication, and password hashing


from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Primary database
db = SQLAlchemy()


# Other extensions
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()
