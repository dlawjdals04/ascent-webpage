from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class SignupForm(FlaskForm):
    username = StringField('아이디', validators=[DataRequired(), Length(min=2)])
    email    = StringField('이메일', validators=[DataRequired(), Email()])
    password = PasswordField('비밀번호', validators=[DataRequired(), Length(min=8)])
    submit   = SubmitField('가입하기')

class LoginForm(FlaskForm):
    username = StringField('아이디', validators=[DataRequired(), Length(min=2)])
    password = PasswordField('비밀번호', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('로그인')