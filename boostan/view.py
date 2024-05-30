from flask import render_template, flash, redirect, url_for, session, request
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
        return redirect(url_for(f"{ session['role'].lower() }_home"))
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def signup_page():
    if "loggedin" in session:
        return redirect(url_for(f"{ session['role'].lower() }_home"))
    form = RegisterForm()
    if form.validate_on_submit():
        password = hashed_password(form.password1.data)
        cur = db.connection.cursor(cursors.DictCursor)
        cur.execute(
            f"""INSERT INTO user(first_name, last_name, age, username, email, role, password)
            VALUES('{form.first_name.data}', 
            '{form.last_name.data}', 
            {form.age.data},
            '{form.username.data}', 
            '{form.email_address.data}', 
            '{form.role.data}',
            '{password}');"""
        )
        cur.execute(
            f"SELECT user_id FROM user WHERE username = '{form.username.data}';"
        )
        user_id = cur.fetchone()
        cur.execute(
            f"INSERT INTO {form.role.data.lower()}(user_id) VALUES({user_id['user_id']})"
        )

        db.connection.commit()

        cur.execute(
            f"SELECT user_id FROM user WHERE username = '{form.username.data}';"
        )
        user_id = cur.fetchone()

        cur.close()

        session["loggedin"] = True
        session["user_id"] = user_id["user_id"]
        session["username"] = form.username.data
        session["role"] = form.role.data

        flash(
            f"Account created successfully! You are now logged in as {form.username.data}",
            category="success",
        )
        return redirect(url_for(f"{ session['role'].lower() }_home"))
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(
                f"There was an error with creating a user: {err_msg}", category="danger"
            )

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if "loggedin" in session:
        return redirect(url_for(f"{ session['role'].lower() }_home"))
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
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(
                f"Success! You are logged in as: {user['username']}",
                category="success",
            )
            return redirect(url_for(f"{ session['role'].lower() }_home"))
        else:
            flash(
                "Username and password are not match! Please try again",
                category="danger",
            )

    return render_template("login.html", form=form)


@app.route("/logout")
def logout_page():

    session.pop("loggedin", None)
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("role", None)

    return redirect(url_for("login_page"))


@app.route("/admin_home")
def admin_home():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))
    if session["role"] == "Student":
        return redirect(url_for("student_home"))
    if session["role"] == "Teacher":
        return redirect(url_for("teacher_home"))
    return render_template("admin_home.html")


@app.route("/teacher_home")
def teacher_home():
    if not "loggedin" in session or session["role"] != "Teacher":
        return redirect(url_for("login_page"))
    if session["role"] == "Student":
        return redirect(url_for("student_home"))
    if session["role"] == "Admin":
        return redirect(url_for("admin_home"))
    return render_template("teacher_home.html")


@app.route("/student_home")
def student_home():
    if not "loggedin" in session or session["role"] != "Student":
        return redirect(url_for("login_page"))
    if session["role"] == "Admin":
        return redirect(url_for("admin_home"))
    if session["role"] == "Teacher":
        return redirect(url_for("teacher_home"))
    return render_template("student_home.html")


@app.route("/subject_list")
def subject_list():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))

    cur = db.connection.cursor(cursors.DictCursor)
    if session["role"] == "Teacher":
        cur.execute(
            f"""         
                        SELECT subject_teacher.subject_id AS subject_id, name 
                        FROM teacher, user, subject_teacher, subject
                        WHERE user.user_id = teacher.user_id 
                        AND teacher.teacher_id=subject_teacher.teacher_id 
                        AND subject.subject_id = subject_teacher.subject_id
                        AND user.user_id={session["user_id"]};
                    """
        )
        subjects = cur.fetchall()
        cur.execute("SELECT * FROM subject ORDER BY subject_id")
        allsubjects = cur.fetchall()
        cur.close()
        return render_template(
            "subject_list.html", subjects=subjects, allsubjects=allsubjects
        )
    elif session["role"] == "Admin":
        cur.execute("SELECT * FROM subject ORDER BY subject_id")
        subjects = cur.fetchall()
        cur.close()
        return render_template("subject_list.html", subjects=subjects)
    elif session["role"] == "Student":
        cur.execute(
            f"""                      
                            WITH studentrec(id) AS (
                                                    SELECT student_id 
                                                    FROM student, user 
                                                    WHERE user.user_id = student.user_id 
                                                    AND student.user_id = {session["user_id"]}
                                                    )
                            SELECT subject_teacher.subject_id AS subject_id, subject.name, first_name, last_name, email, grade
                            FROM subject_teacher, subject, user, teacher, grade, studentrec
                            WHERE subject_teacher.subject_id=subject.subject_id
                            AND user.user_id = teacher.user_id
                            AND teacher.teacher_id=subject_teacher.teacher_id
                            AND grade.subject_id = subject.subject_id
                            AND grade.student_id=studentrec.id;
                    """
        )
        recs = cur.fetchall()
        cur.execute(
            """
                    SELECT subject.subject_id, name, first_name, last_name 
                    FROM subject_teacher 
                    NATURAL JOIN subject 
                    NATURAL JOIN teacher 
                    NATURAL JOIN user;"""
        )
        allsubjects = cur.fetchall()
        cur.close()
        return render_template(
            "subject_list.html",
            subjects=recs,
            allsubjects=allsubjects,
        )


@app.route("/subject_detail")
def subject_detail():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))

    id = request.args.get("id")
    if id:
        cur = db.connection.cursor(cursors.DictCursor)
        cur.execute(f"SELECT name FROM subject where subject_id={id}")
        subject = cur.fetchone()

        if subject:
            cur.execute(
                f"""
                        SELECT subject.subject_id , teacher.teacher_id, name, first_name, last_name, email 
                        FROM teacher, user, subject_teacher, subject
                        WHERE user.user_id = teacher.user_id 
                        AND teacher.teacher_id=subject_teacher.teacher_id
                        AND subject.subject_id = subject_teacher.subject_id 
                        AND subject.name="{subject["name"]}";
                        """
            )
            teacher = cur.fetchone()
            cur.execute(
                f"""
                            SELECT subject.subject_id, student.student_id, name, first_name, last_name, email 
                            FROM subject, user, subject_student, student 
                            WHERE user.user_id = student.user_id 
                            AND student.student_id = subject_student.student_id 
                            AND subject.subject_id = subject_student.subject_id 
                            AND subject.name = "{subject["name"]}";
                        """
            )
            students = cur.fetchall()
            cur.execute(
                f"""
                            SELECT grade 
                            FROM grade 
                            NATURAL JOIN student 
                            WHERE user_id={session['user_id']} 
                            AND subject_id={id};
                        """
            )
            grade = cur.fetchone()
            cur.close()

            return render_template(
                "subject_detail.html",
                id=id,
                subject=subject,
                teacher=teacher,
                students=students,
                grade=grade,
            )
        flash("this subject doesn't exist!", category="danger")
        return redirect(url_for("subject_list"))


@app.route("/user_list")
def user_list():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))
    if session["role"] == "Student":
        return redirect(url_for("student_home"))

    cur = db.connection.cursor(cursors.DictCursor)
    if session["role"] == "Admin":
        cur.execute("SELECT * FROM user ORDER BY user_id")
    elif session["role"] == "Teacher":
        cur.execute(
            f"""
                    WITH teacherid(id, name) AS (
                                                SELECT subject_teacher.subject_id AS id, username 
                                                FROM teacher, user, subject_teacher
                                                WHERE user.user_id = teacher.user_id 
                                                AND teacher.teacher_id=subject_teacher.teacher_id 
                                                AND user.user_id={session['user_id']}
                                                )
                    SELECT subject.name, student.user_id, first_name, last_name, email, grade
                    FROM subject, teacherid, student, grade, user
                    WHERE subject.subject_id = teacherid.id
                    AND student.student_id=grade.student_id
                    AND subject.subject_id=grade.subject_id
                    AND student.user_id=user.user_id;
                    """
        )
    users = cur.fetchall()
    cur.close()
    return render_template("user_list.html", users=users)


@app.route("/user_detail")
def user_detail():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))

    id = request.args.get("id")
    if id:
        cur = db.connection.cursor(cursors.DictCursor)
        cur.execute(f"SELECT * FROM user where user_id={id}")
        user = cur.fetchone()

        if user:
            if session["role"] == "Student" and session["user_id"] != user["user_id"]:
                return redirect(url_for("student_home"))
            if user["role"] == "Student" and session["role"] == "Teacher":
                cur.execute(
                    f"SELECT first_name, last_name, age, email FROM user, student WHERE user.user_id = student.user_id AND user.user_id={id}"
                )
                student = cur.fetchone()

                cur.execute(
                    f"""
                                
                            WITH teachername(id, username) AS (
                                                            SELECT subject_teacher.subject_id as id, username 
                                                            FROM teacher, user, subject_teacher
                                                            WHERE user.user_id = teacher.user_id 
                                                            AND teacher.teacher_id=subject_teacher.teacher_id 
                                                            AND user.user_id={id}
                                                            )
                            SELECT id, name 
                            FROM subject, teachername
                            WHERE subject.subject_id = teachername.id;
                            """
                )
                subjects = cur.fetchall()
                students = ()
                for subject in subjects:
                    cur.execute(
                        f"""
                                WITH studentrec(subject_id, student_id, name, first_name, last_name, age, email) AS ( 
                                                        SELECT subject.subject_id, student.student_id, name, first_name, last_name, age, email 
                                                        FROM subject, user, subject_student, student 
                                                        WHERE user.user_id = student.user_id 
                                                        AND student.student_id = subject_student.student_id 
                                                        AND subject.subject_id = subject_student.subject_id 
                                                        AND subject.name = "{subject["name"]}")
                                SELECT name, first_name, last_name, age, email, grade
                                FROM studentrec, grade
                                WHERE grade.student_id = studentrec.student_id 
                                AND grade.subject_id = studentrec.subject_id;
                                """
                    )
                    students += cur.fetchall()

                cur.close()
                return render_template(
                    "user_detail.html",
                    id=int(id),
                    user=user,
                    subjects=subjects,
                    students=students,
                    student=student,
                )
            if user["role"] == "Teacher":
                cur.execute(
                    f"""
                                
                            WITH teachername(id, username) AS (
                                                            SELECT subject_teacher.subject_id as id, username 
                                                            FROM teacher, user, subject_teacher
                                                            WHERE user.user_id = teacher.user_id AND 
                                                            teacher.teacher_id=subject_teacher.teacher_id AND 
                                                            user.user_id={id})
                            SELECT id, name 
                            FROM subject, teachername
                            WHERE subject.subject_id = teachername.id;
                            """
                )
                subjects = cur.fetchall()
                students = ()
                for subject in subjects:
                    cur.execute(
                        f"""
                                WITH studentrec(subject_id, student_id, name, first_name, last_name, age, email) AS ( 
                                                        SELECT subject.subject_id, student.student_id, name, first_name, last_name, age, email 
                                                        FROM subject, user, subject_student, student 
                                                        WHERE user.user_id = student.user_id 
                                                        AND student.student_id = subject_student.student_id 
                                                        AND subject.subject_id = subject_student.subject_id 
                                                        AND subject.name = "{subject["name"]}")
                                SELECT name, first_name, last_name, age, email, grade
                                FROM studentrec, grade
                                WHERE grade.student_id = studentrec.student_id 
                                AND grade.subject_id = studentrec.subject_id;
                                """
                    )
                    students += cur.fetchall()

                cur.close()
                return render_template(
                    "user_detail.html",
                    id=int(id),
                    user=user,
                    subjects=subjects,
                    students=students,
                )
            if user["role"] == "Student":
                print("hello")

                cur.execute(
                    f"""
                                
                            WITH studentrec(id) AS (SELECT student_id FROM student, user WHERE user.user_id = student.user_id AND student.user_id = {id})
                            select subject_teacher.subject_id AS id, subject.name, first_name, last_name, email, grade
                            FROM subject_teacher, subject, user, teacher, grade, studentrec
                            WHERE subject_teacher.subject_id=subject.subject_id
                            AND user.user_id = teacher.user_id
                            AND teacher.teacher_id=subject_teacher.teacher_id
                            AND grade.subject_id = subject.subject_id
                            AND grade.student_id=studentrec.id;
                    """
                )
                recs = cur.fetchall()
                cur.execute(
                    f"""
                        WITH studentrec(id) AS (SELECT student_id FROM student, user WHERE user.user_id = student.user_id AND student.user_id = {id})
                        SELECT avg(grade) from grade, studentrec where student_id = studentrec.id;
                    """
                )
                avg = cur.fetchone()["avg(grade)"]
                cur.close()
                return render_template(
                    "user_detail.html", id=int(id), user=user, recs=recs, avg=avg
                )
            return render_template("user_detail.html", id=int(id), user=user)

        flash("this subject doesn't exist!", category="danger")
        return redirect(url_for("user_list"))


@app.route("/users/update", methods=["POST"])
def user_update():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))

    if request.method == "POST":
        id = request.form["id"]
        if session["role"] == "Student" and session["user_id"] != id:
            return redirect(url_for("student_home"))

        cur = db.connection.cursor(cursors.DictCursor)
        if session["role"] == "Teacher":
            grade = request.form["grade"]
            name = request.form["name"]
            cur.execute(f"SELECT student_id FROM student WHERE user_id={id}")
            student = cur.fetchone()
            cur.execute(f"SELECT subject_id FROM subject WHERE name='{name}'")
            subject = cur.fetchone()

            cur.execute(
                f"UPDATE grade SET grade={grade} WHERE student_id={student['student_id']} AND subject_id={subject['subject_id']}"
            )
            db.connection.commit()
            cur.close()
            flash("Data Updated Successfully", category="success")
            return redirect(url_for("user_list"))

        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        username = request.form["username"]
        age = request.form["age"]
        email = request.form["email"]
        cur.execute(f"SELECT username, email FROM user WHERE user_id={id}")
        current_user = cur.fetchone()
        cur.execute(f"SELECT username FROM user WHERE username='{username}'")
        edited_user = cur.fetchone()
        cur.execute(f"SELECT email FROM user WHERE email='{email}'")
        edited_email = cur.fetchone()
        if edited_user:
            if edited_user["username"] != current_user["username"]:
                cur.close()
                flash("this user already exist", category="danger")
                return redirect(url_for("user_list"))

        if edited_email:

            if edited_email["email"] != current_user["email"]:
                cur.close()
                flash("this user already exist", category="danger")
                return redirect(url_for("user_list"))

        if session["user_id"] == int(id) and request.form["password"]:
            password = request.form["password"]
            password = hashed_password(password)
            cur.execute(
                f"UPDATE user SET first_name='{first_name}', last_name='{last_name}', age={age}, username ='{username}', email='{email}', password='{password}' WHERE user_id={id}"
            )
        else:
            cur.execute(
                f"UPDATE user SET first_name='{first_name}', last_name='{last_name}', age={age}, username ='{username}', email='{email}' WHERE user_id={id}"
            )
        db.connection.commit()
        cur.close()
        flash("Data Updated Successfully", category="success")
        return redirect(url_for("user_list"))


@app.route("/users/delete", methods=["GET"])
def user_delete():

    if not "loggedin" in session:
        return redirect(url_for("login_page"))
    id = request.args.get("id")
    if (session["role"] == "Student" or session["role"] == "Teacher") and session[
        "user_id"
    ] != id:
        return redirect(url_for(f"{session['role'].lower()}_home"))

    role = request.args.get("role")
    cur = db.connection.cursor()
    if role == "Teacher":
        cur.execute(
            f"""
                    DELETE FROM subject_student WHERE subject_id IN (
                                                                SELECT ssid FROM(
                                                                                SELECT subject_teacher.subject_id AS ssid 
                                                                                FROM subject_student, subject_teacher, user, teacher 
                                                                                WHERE subject_student.subject_id=subject_teacher.subject_id 
                                                                                AND teacher.user_id=user.user_id
                                                                                AND subject_teacher.teacher_id=teacher.teacher_id
                                                                                AND user.user_id={id}) AS ss);
                    """
        )
        cur.execute(
            f"""
                    DELETE FROM grade WHERE subject_id IN (
                                                            SELECT ssid FROM(
                                                                            SELECT subject_teacher.subject_id AS ssid 
                                                                            FROM grade, subject_teacher, user, teacher 
                                                                            WHERE grade.subject_id=subject_teacher.subject_id 
                                                                            AND teacher.user_id=user.user_id
                                                                            AND subject_teacher.teacher_id=teacher.teacher_id
                                                                            AND user.user_id={id}) AS ss);
                    """
        )

    cur.execute(f"DELETE FROM user WHERE user_id={id};")

    cur.execute("ALTER TABLE user AUTO_INCREMENT = 1;")
    cur.execute("ALTER TABLE admin AUTO_INCREMENT = 1;")
    cur.execute("ALTER TABLE student AUTO_INCREMENT = 1;")
    cur.execute("ALTER TABLE teacher AUTO_INCREMENT = 1;")
    db.connection.commit()

    flash("Record Has Been Deleted Successfully", category="success")
    if session["user_id"] == int(id):
        return redirect(url_for("logout_page"))
    return redirect(url_for("user_list"))


@app.route("/subjects/insert", methods=["POST"])
def subject_insert():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))
    if request.method == "POST":
        if session["role"] == "Admin":
            name = request.form["name"]
            cur = db.connection.cursor(cursors.DictCursor)
            cur.execute(f"SELECT * FROM subject WHERE name='{name}'")
            if cur.fetchone():
                cur.close()
                flash("this subject already exist", category="danger")
                return redirect(url_for("subject_list"))
            cur.execute(f"INSERT INTO subject (name) VALUES ('{name}')")
            db.connection.commit()
        elif session["role"] == "Teacher":
            name = request.form["name"]
            cur = db.connection.cursor(cursors.DictCursor)
            cur.execute(f"SELECT subject_id FROM subject WHERE name='{name}'")
            subject = cur.fetchone()
            cur.execute(
                f"SELECT teacher_id FROM teacher WHERE user_id={session['user_id']}"
            )
            teacher = cur.fetchone()
            cur.execute(
                f"SELECT * FROM subject_teacher WHERE subject_id={subject['subject_id']} AND teacher_id={teacher['teacher_id']}"
            )
            existingsubject = cur.fetchone()
            if existingsubject:
                cur.close()
                flash("you already have this subject", category="danger")
                return redirect(url_for("subject_list"))

            cur.execute(
                f"INSERT INTO subject_teacher (subject_id, teacher_id) VALUES ({subject['subject_id']}, {teacher['teacher_id']})"
            )
            db.connection.commit()
        elif session["role"] == "Student":
            name = request.form["name"]
            subject_name = "".join(name.split()[:1])
            cur = db.connection.cursor(cursors.DictCursor)
            cur.execute(f"SELECT subject_id FROM subject WHERE name='{subject_name}'")
            subject = cur.fetchone()
            cur.execute(
                f"SELECT student_id FROM student WHERE user_id={session['user_id']}"
            )
            student = cur.fetchone()
            cur.execute(
                f"SELECT * FROM subject_student WHERE subject_id={subject['subject_id']} AND student_id={student['student_id']}"
            )
            existingsubject = cur.fetchone()
            if existingsubject:
                cur.close()
                flash("you already have this subject", category="danger")
                return redirect(url_for("subject_list"))

            cur.execute(
                f"INSERT INTO subject_student (subject_id, student_id) VALUES ({subject['subject_id']}, {student['student_id']})"
            )

            cur.execute(
                f"INSERT INTO grade (subject_id, student_id) VALUES ({subject['subject_id']}, {student['student_id']})"
            )
            db.connection.commit()
        flash("Data Inserted Successfully", category="success")
        return redirect(url_for("subject_list"))


@app.route("/subjects/update", methods=["POST"])
def subject_update():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))
    if session["role"] == "Student" or session["role"] == "Teacher":
        return redirect(url_for(f"{session['role'].lower()}_home"))
    if request.method == "POST":
        id = request.form["id"]
        name = request.form["name"]
        cur = db.connection.cursor(cursors.DictCursor)
        cur.execute(f"SELECT * FROM subject WHERE name='{name}'")
        if cur.fetchone():
            cur.close()
            flash("this subject already exist", category="danger")
            return redirect(url_for("subject_list"))

        cur.execute(f"UPDATE subject SET name='{name}' WHERE subject_id={id}")
        db.connection.commit()
        flash("Data Updated Successfully", category="success")
        return redirect(url_for("subject_list"))


@app.route("/subjects/delete", methods=["GET"])
def subject_delete():
    if not "loggedin" in session:
        return redirect(url_for("login_page"))
    id = request.args.get("id")
    cur = db.connection.cursor(cursors.DictCursor)
    if session["role"] == "Admin":
        cur.execute(f"DELETE FROM subject WHERE subject_id={id}")
        cur.execute("ALTER TABLE subject AUTO_INCREMENT = 1")

    elif session["role"] == "Teacher":
        cur.execute(
            f"SELECT teacher_id FROM teacher WHERE user_id={session['user_id']}"
        )
        teacher = cur.fetchone()
        cur.execute(
            f"DELETE FROM subject_teacher WHERE subject_id={id} AND teacher_id={teacher['teacher_id']}"
        )
        cur.execute(f"DELETE FROM subject_student WHERE subject_id={id}")
        cur.execute(f"DELETE FROM grade WHERE subject_id={id}")
    elif session["role"] == "Student":
        cur.execute(
            f"SELECT student_id FROM student WHERE user_id={session['user_id']}"
        )
        student = cur.fetchone()
        cur.execute(
            f"DELETE FROM subject_student WHERE subject_id={id} AND student_id={student['student_id']}"
        )
        cur.execute(
            f"DELETE FROM grade WHERE subject_id={id} AND student_id={student['student_id']}"
        )

    db.connection.commit()
    flash("Record Has Been Deleted Successfully", category="success")
    return redirect(url_for("subject_list"))
