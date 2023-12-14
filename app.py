# IMPORTS
import logging
from functools import wraps
# Import necessary modules and libraries for the application.

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_qrcode import QRcode
import os
from dotenv import load_dotenv
from flask_login import LoginManager, current_user
from flask_talisman import Talisman

# Load environment variables from .env file.
load_dotenv()

# Define a custom filter to log only security-related messages.
class SecurityFilter(logging.Filter):
    def filter(self, record):
        return 'SECURITY' in record.getMessage()

# Setup logging to log security-related messages to 'lottery.log'.
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('lottery.log', 'a')
file_handler.setLevel(logging.WARNING)
file_handler.addFilter(SecurityFilter())
formatter = logging.Formatter('%(asctime)s : %(message)s', '%m/%d/%Y %I:%M:%S %p')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# CONFIG
app = Flask(__name__)
# Configure the Flask app with various settings.
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lottery.db'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RECAPTCHA_PUBLIC_KEY'] = os.getenv('RECAPTCHA_PUBLIC_KEY')
app.config['RECAPTCHA_PRIVATE_KEY'] = os.getenv('RECAPTCHA_PRIVATE_KEY')

# Error handlers for different HTTP error codes.
@app.errorhandler(403)
def internal_error(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404

@app.errorhandler(503)
def internal_error(error):
    return render_template('503.html'), 503

# Initialise the database and QR code generation extension.
db = SQLAlchemy(app)
qrcode = QRcode(app)

# Content Security Policy (CSP) configuration for Talisman.
csp = {
    'default-src': [
        '\'self\'',
        'https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css'],
    'frame-src': [
        '\'self\'',
        'https://www.google.com/recaptcha/',
        'https://recaptcha.google.com/recaptcha/'],
    'script-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://www.google.com/recaptcha/',
        'https://www.gstatic.com/recaptcha/']
}
# Configure Talisman middleware with CSP.
talisman = Talisman(app, content_security_policy=csp)

# Decorator function to check user roles before accessing certain routes.
def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                logging.warning('SECURITY - Unauthorised role based access [%s, %s, %s, %s]',
                                current_user.id,
                                current_user.email,
                                current_user.role,
                                request.remote_addr
                                )
                return render_template('403.html')
            return f(*args, **kwargs)
        return wrapped
    return wrapper

# HOME PAGE VIEW
@app.route('/')
def index():
    return render_template('main/index.html')

# Setup Flask-Login.
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.init_app(app)

from models import User
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# BLUEPRINTS
# Import blueprints from other parts of the application.
from users.views import users_blueprint
from admin.views import admin_blueprint
from lottery.views import lottery_blueprint

# Register blueprints with the app.
app.register_blueprint(users_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(lottery_blueprint)

# Run the Flask application.
if __name__ == "__main__":
    app.run(ssl_context=('cert.pem', 'key.pem'))
