from flask import render_template, flash, redirect, url_for, session, request
from boostan import app, db
from boostan.forms import RegisterForm, LoginForm, SubjectInsertForm
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
        return redirect(url_for("admin_user_home"))
    return render_template("home.html")


@app.route("/admin_home")
def admin_user_home():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))
    return render_template("user_home.html")


@app.route("/subject_list")
def subject_list():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))

    cur = db.connection.cursor(cursors.DictCursor)
    cur.execute("SELECT * FROM subject ORDER BY ID")
    subjects = cur.fetchall()
    cur.close()
    return render_template("subject_list.html", subjects=subjects)


@app.route("/subject_detail")
def subject_detail():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))

    id = request.args.get("id")
    if id:
        cur = db.connection.cursor(cursors.DictCursor)
        cur.execute(f"SELECT name FROM subject where ID={id}")
        subject = cur.fetchone()
        cur.close()
        if subject:
            return render_template("subject_detail.html", id=id, subject=subject)
        flash("this subject doesn't exist!", category="danger")
        return redirect(url_for("subject_list"))


@app.route("/user_list")
def user_list():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))


@app.route("/user_detail")
def user_detail():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))


@app.route("/subjects/insert", methods=["POST"])
def subject_insert():
    if request.method == "POST":

        name = request.form["name"]
        cur = db.connection.cursor(cursors.DictCursor)
        cur.execute(f"SELECT * FROM subject WHERE name='{name}'")
        if cur.fetchone():
            cur.close()
            flash("this subject already exist", category="danger")
            return redirect(url_for("admin_user_home"))
        cur.execute(f"INSERT INTO subject (name) VALUES ('{name}')")
        db.connection.commit()
        flash("Data Inserted Successfully", category="success")
        return redirect(url_for("admin_user_home"))


@app.route("/subjects/update", methods=["POST"])
def subject_update():
    if request.method == "POST":
        id = request.form["id"]
        name = request.form["name"]
        cur = db.connection.cursor(cursors.DictCursor)
        cur.execute(f"SELECT * FROM subject WHERE name='{name}'")
        if cur.fetchone():
            cur.close()
            flash("this subject already exist", category="danger")
            return redirect(url_for("admin_user_home"))

        cur.execute(f"UPDATE subject SET name='{name}' WHERE id={id}")
        db.connection.commit()
        flash("Data Updated Successfully", category="success")
        return redirect(url_for("admin_user_home"))


@app.route("/subjects/delete", methods=["GET"])
def subject_delete():
    id = request.args.get("id")
    cur = db.connection.cursor()
    cur.execute(f"DELETE FROM subject WHERE id={id}")
    db.connection.commit()

    flash("Record Has Been Deleted Successfully")
    return redirect(url_for("admin_user_home"))


@app.route("/register", methods=["GET", "POST"])
def signup_page():
    if "loggedin" in session:
        return redirect(url_for("admin_user_home"))
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
        return redirect(url_for("admin_user_home"))
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(
                f"There was an error with creating a user: {err_msg}", category="danger"
            )

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if "loggedin" in session:
        return redirect(url_for("admin_user_home"))
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
            return redirect(url_for("admin_user_home"))
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
