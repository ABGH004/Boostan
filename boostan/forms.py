from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError
from boostan import db


class RegisterForm(FlaskForm):
    def validate_username(self, username_to_check):
        cur = db.connection.cursor()
        cur.execute(f"SELECT * FROM user WHERE username = '{username_to_check.data}';")
        user = cur.fetchall()
        cur.close()
        if user:
            raise ValidationError(
                "Username already exists! Please try a different username"
            )

    def validate_email_address(self, email_address_to_check):
        cur = db.connection.cursor()
        cur.execute(
            f"SELECT * FROM user WHERE email = '{email_address_to_check.data}';"
        )
        email_address = cur.fetchall()
        cur.close()
        if email_address:
            raise ValidationError(
                "Email Address already exists! Please try a different email address"
            )

    first_name = StringField(
        label="First Name:", validators=[Length(min=2, max=25), DataRequired()]
    )
    last_name = StringField(
        label="Last Name:", validators=[Length(min=2, max=35), DataRequired()]
    )
    username = StringField(
        label="User Name:", validators=[Length(min=2, max=25), DataRequired()]
    )
    email_address = StringField(
        label="Email Address:", validators=[Email(), DataRequired()]
    )
    password1 = PasswordField(
        label="Password:", validators=[Length(min=6), DataRequired()]
    )
    password2 = PasswordField(
        label="Confirm Password:", validators=[EqualTo("password1"), DataRequired()]
    )
    submit = SubmitField(label="Create Account")
