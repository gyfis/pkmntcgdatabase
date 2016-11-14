from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, SubmitField
from wtforms.validators import Regexp, Length, Email


class LoginForm(FlaskForm):
    username = StringField('username', validators=[Regexp(r'^[\w-]+$'), Length(min=4, max=25)])
    password = PasswordField('password', validators=[Length(min=6)])
    remember_me = BooleanField('remember_me', default=False)
    login = SubmitField('login')


class SignupForm(FlaskForm):
    username = StringField('username', validators=[Regexp(r'^[\w-]+$'), Length(min=4, max=25)])
    password = PasswordField('password', validators=[Length(min=6)])
    email = StringField('email',  validators=[Email('This field requires a valid email address')])
    collection_name = StringField('collection', validators=[Regexp(r'^[a-zA-Z\d ]*$')])
    remember_me = BooleanField('remember_me', default=False)
    signup = SubmitField('sign up')
