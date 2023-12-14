import secrets
import string
from datetime import datetime

from app import db, app
from flask_login import UserMixin
import pyotp
from cryptography.fernet import Fernet

import bcrypt

# Generate a secret key for encryption using Fernet.
secret_key = Fernet.generate_key()

class User(db.Model, UserMixin):
    # Define the 'users' table in the database.
    __tablename__ = 'users'

    # Define columns for the 'users' table.
    id = db.Column(db.Integer, primary_key=True)

    # User authentication information.
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    # User information
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(100), nullable=False)
    postcode = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='user')
    pin_key = db.Column(db.String(32), nullable=True, default=pyotp.random_base32())
    registered_on = db.Column(db.DateTime, nullable=False)
    current_login = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    post_key = db.Column(db.BLOB, nullable=False, default=Fernet.generate_key())

    # Define a relationship to the 'draws' table
    draws = db.relationship('Draw')

    def __init__(self, email, firstname, lastname, phone, dob, postcode, password, role):
        # Initialize new user object.
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.phone = phone
        self.dob = dob
        self.postcode = postcode
        # Hash the user's password using bcrypt.
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.role = role
        self.registered_on = datetime.now()
        self.current_login = None
        self.last_login = None

    def get_2fa_uri(self):
        # Generate a provisioning URI for 2FA using pyotp.
        return str(pyotp.totp.TOTP(self.pin_key).provisioning_uri(
            name=self.email,
            issuer_name='CSC2031 Lottery Web App')
        )

    def verify_pin(self, pin):
        # Verify a PIN using pyotp.
        return pyotp.TOTP(self.pin_key).verify(pin)

    def verify_password(self, password):
        # Verify a password using bcrypt.
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

class Draw(db.Model):
    # Define the 'draws' table in the database.
    __tablename__ = 'draws'

    # Define columns for the 'draws' table.
    id = db.Column(db.Integer, primary_key=True)

    # ID of the user who submitted the draw.
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)

    # 6 draw numbers submitted by the user.
    numbers = db.Column(db.String(100), nullable=False)

    # Flag indicating whether the draw has been played.
    been_played = db.Column(db.BOOLEAN, nullable=False, default=False)

    # Flag indicating whether the draw matches with the master draw.
    matches_master = db.Column(db.BOOLEAN, nullable=False, default=False)

    # Flag indicating whether the draw is a master draw created by the admin.
    master_draw = db.Column(db.BOOLEAN, nullable=False)

    # Lottery round that the draw is associated with.
    lottery_round = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, user_id, numbers, master_draw, lottery_round):
        # Initialize a new draw object.
        self.user_id = user_id
        self.numbers = numbers
        self.been_played = False
        self.matches_master = False
        self.master_draw = master_draw
        self.lottery_round = lottery_round

def init_db():
    # Initialize the database with initial data.
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Create an admin user and add it to the database.
        admin = User(email='admin@email.com',
                     password='Admin1!',
                     firstname='Alice',
                     lastname='Jones',
                     phone='0191-123-4567',
                     dob='28/04/1964',
                     postcode='B6 3AL',
                     role='admin')
        db.session.add(admin)
        db.session.commit()

def encrypt(data, post_key):
    # Encrypt data using Fernet encryption.
    return Fernet(post_key).encrypt(bytes(data, 'utf-8'))

def decrypt(data, post_key):
    # Decrypt data using Fernet encryption.
    return Fernet(post_key).decrypt(data).decode('utf-8')
