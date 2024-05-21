from flask import render_template, flash, redirect, url_for, session
from boostan import app, db
from boostan.forms import RegisterForm, LoginForm
from MySQLdb import cursors
import hashlib


def hashed_password(password):
    hash = password + app.secret_key
    hash = hashlib.sha1(hash.encode())
    hashed_password = hash.hexdigest()
    return hashed_password


@app.route("/")
@app.route("/home")
def home_page():
    if "loggedin" in session:
        return redirect(url_for("user_detail"))
    return render_template("home.html")


@app.route("/user_detail")
def user_detail():
    if "loggedin" in session:
        return render_template("user_detail.html")
    return redirect(url_for("login_page"))


@app.route("/register", methods=["GET", "POST"])
def signup_page():
    if "loggedin" in session:
        return redirect(url_for("user_detail"))
    form = RegisterForm()
    if form.validate_on_submit():
        password = hashed_password(form.password1.data)
        cur = db.connection.cursor(cursors.DictCursor)
        cur.execute(
            f"INSERT INTO user(first_name, last_name, username, email, password) VALUES('{form.first_name.data}', '{form.last_name.data}', '{form.username.data}', '{form.email_address.data}', '{password}');"
        )
        db.connection.commit()

        cur.execute(f"SELECT ID FROM user WHERE username = '{form.username.data}';")
        id = cur.fetchone()

        cur.close()

        session["loggedin"] = True
        session["ID"] = id
        session["username"] = form.username.data

        flash(
            f"Account created successfully! You are now logged in as {form.username.data}",
            category="success",
        )
        return redirect(url_for("user_detail"))
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(
                f"There was an error with creating a user: {err_msg}", category="danger"
            )

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if "loggedin" in session:
        return redirect(url_for("user_detail"))
    form = LoginForm()
    if form.validate_on_submit():
        password = hashed_password(form.password.data)
        cur = db.connection.cursor(cursors.DictCursor)
        cur.execute(
            f"SELECT * FROM user WHERE username = '{form.username.data}' and password = '{password}';"
        )
        user = cur.fetchone()

        cur.close()
        if user:
            session["loggedin"] = True
            session["ID"] = user["ID"]
            session["username"] = user["username"]
            flash(
                f"Success! You are logged in as: {user['username']}",
                category="success",
            )
            return redirect(url_for("user_detail"))
        else:
            flash(
                "Username and password are not match! Please try again",
                category="danger",
            )

    return render_template("login.html", form=form)


@app.route("/logout")
def logout_page():

    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)

    return redirect(url_for("login_page"))
