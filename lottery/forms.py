from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import NumberRange, DataRequired


class DrawForm(FlaskForm):
    number1 = IntegerField(id='no1', validators=[DataRequired(message='Enter No. 1'), NumberRange(min=1, max=60, message='Number must be value between 1 and 60')])
    number2 = IntegerField(id='no2', validators=[DataRequired(message='Enter No. 2'), NumberRange(min=1, max=60, message='Number must be value between 1 and 60')])
    number3 = IntegerField(id='no3', validators=[DataRequired(message='Enter No. 3'), NumberRange(min=1, max=60, message='Number must be value between 1 and 60')])
    number4 = IntegerField(id='no4', validators=[DataRequired(message='Enter No. 4'), NumberRange(min=1, max=60, message='Number must be value between 1 and 60')])
    number5 = IntegerField(id='no5', validators=[DataRequired(message='Enter No. 5'), NumberRange(min=1, max=60, message='Number must be value between 1 and 60')])
    number6 = IntegerField(id='no6', validators=[DataRequired(message='Enter No. 6'), NumberRange(min=1, max=60, message='Number must be value between 1 and 60')])
    submit = SubmitField("Submit Draw")
