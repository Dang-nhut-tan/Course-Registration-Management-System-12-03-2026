import os
import sys

from flask import render_template
from app import app


@app.route("/")
def login():
    return render_template("login.html")

@app.route("/forgot-password")
def forgot_password():
    return render_template("forgot-password.html")

if __name__ == "__main__":
    app.run(debug=True)
