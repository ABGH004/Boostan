from flask import Flask
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "ABGH004"
app.config["MYSQL_PASSWORD"] = "my$Password"
app.config["MYSQL_DB"] = "boostan"
app.config["SECRET_KEY"] = "65331cf3626c01626d7e7ee2"
db = MySQL(app)
from boostan import view
