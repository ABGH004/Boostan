from flask import render_template, flash, redirect, url_for
from boostan import app, db
from boostan.forms import RegisterForm


@app.route("/")
@app.route("/home")
def home_page():
    return render_template("home.html")


@app.route("/user_detail")
def user_detail():
    return render_template("user_detail.html")


@app.route("/register", methods=["GET", "POST"])
def sign_in():
    form = RegisterForm()
    if form.validate_on_submit():
        cur = db.connection.cursor()
        cur.execute(
            f"INSERT INTO user(first_name, last_name, username, email, password) VALUES('{form.first_name.data}', '{form.last_name.data}', '{form.username.data}', '{form.email_address.data}', '{form.password1.data}');"
        )
        db.connection.commit()
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
