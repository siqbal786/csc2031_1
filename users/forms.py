from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import email, Length, DataRequired, EqualTo
from wtforms.validators import ValidationError
from wtforms.validators import NoneOf
import re

# Custom validator for checking disallowed characters
def character_check(form, field):
    excluded_chars = "*?!'^+%&/()=}][{$#@<>"
    for char in field.data:
        if char in excluded_chars:
            raise ValidationError(f"Character {char} is not allowed.")

# Custom validator for validating phone number format
def variable_data(form, data_field):
    p = re.compile(r'^\d{4}-\d{3}-\d{4}$')
    if not p.match(data_field.data):
        raise ValidationError("Phone number must only contain digits and dashes (-)")

# Custom validator for validating date of birth format
def variable_datadob(form, data_field1):
    p = re.compile(r'^\d{2}/\d{2}/\d{4}$')
    if not p.match(data_field1.data):
        raise ValidationError("DOB must only contain digits and slashes (/)")

# Custom validator for validating postcode format
def variable_datapostcode(form, field2):
    p1 = re.compile(r'^(([A-Z][0-9]{1,2})|(([A-Z][A-HJ-Y][0-9]{1,2})|(([A-Z][0-9][A-Z])|([A-Z][A-HJ-Y][0-9]?[A-Z])))) [0-9][A-Z]{2}$')
    # p2 = re.compile(r'^[A-Z]\d{2}\s[A-Z]{2}\d{2}$')
    # p3 = re.compile(r'^[A-Z]{2}\d\s[A-Z]{2}\d{2}$')
    # (r'^[A-Z]{2}\d[A-Z]{2}\d[A-Z]{2}\d[A-Z]{2}\d[A-Z]{2}\d[A-Z]{2}\d[A-Z]{2}\d')
    if not p1.match(field2.data):
        raise ValidationError("Postcode must be a String containing only uppercase letters (X) and digits (Y) of the following forms: XY YXX, XYY YXX, XXY YXX")
    # if not p2.match(field.data):
    #     raise ValidationError("Postcode must be a String containing only uppercase letters (X) and digits (Y) of the following forms: XY YXX, XYY YXX, XXY YXX")
    # if not p3.match(field.data):
    #     raise ValidationError("Postcode must be a String containing only uppercase letters (X) and digits (Y) of the following forms: XY YXX, XYY YXX, XXY YXX")

# Custom validator for validating password format
def validate_password(form, field):
    p = re.compile(r'^(?=.*\d)(?=.*[A-Z])(?=.*[-])')
    if not p.match(field.data):
        raise ValidationError('Password must contain at least 1 digit, 1 lowercase and 1 uppercase character, it must also contain at least one special character')

# Form for user registration
class RegisterForm(FlaskForm):
    email = StringField(validators=[email()])
    firstname = StringField(validators=[character_check])
    lastname = StringField(validators=[character_check])
    phone = StringField(validators=[variable_data])
    dob = StringField(validators=[variable_datadob])
    postcode = StringField(validators=[variable_datapostcode])
    password = PasswordField(validators=[DataRequired(), validate_password])
    confirm_password = PasswordField(
        validators=[DataRequired(), EqualTo('password', message='Passwords must match!'), Length(min=6, max=12)])
    submit = SubmitField()

# Form for user login
class LoginForm(FlaskForm):
    email = StringField(validators=[email()])
    password = PasswordField(validators=[DataRequired()])
    pin = StringField(validators=[DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField()

# Form for new password
class PasswordForm(FlaskForm):
    current_password = PasswordField(id='password', validators=[DataRequired()])
    show_password = BooleanField('Show password', id='check')
    new_password = PasswordField(validators=[DataRequired(), Length(min=6, max=12, message="Must be between 6 and 12 characters in length"), validate_password])
    confirm_new_password = PasswordField(validators=[DataRequired(), EqualTo('new_password', message='Both new password fields must be equal')])
    submit = SubmitField('Change Password')


