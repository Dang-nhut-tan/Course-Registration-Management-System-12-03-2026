import os
import sys

from flask import render_template

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from app import app
else:
    from app import app

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/forgot-password")
def forgot_password():
    return render_template("forgot-password.html")

if __name__ == "__main__":
    app.run(debug=True)
