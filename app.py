import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///college.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def homepage():
    return render_template("homepage.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user for an account."""

    # POST
    if request.method == "POST":

        # Validate form submission
        if not request.form.get("username"):
            return apology("missing username")
        elif not request.form.get("password"):
            return apology("missing password")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")
        elif not request.form.get("GPA"):
            return apology("must enter GPA")
        
        username = request.form.get("username")

        # Add user modifcations to the users table
        try:
            db.execute("INSERT INTO users (username, hash, SAT, ACT, GPA) VALUES(?, ?, ?, ?, ?)", username, generate_password_hash(request.form.get("password")), request.form.get("SAT"), request.form.get("ACT"), request.form.get("GPA"))
        except:
            return apology("username taken")
        
        # Log user in
        id = db.execute("SELECT id FROM users WHERE username = ?", username)

        session["user_id"] = id[0]["id"]
        

        # Let user know they're registered
        flash("Registered!")
        return redirect("/")
    # GET
    else:
        return render_template("register.html")

@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    # Get username
    username = request.args.get("username")

    # Check for username
    if not len(username) or db.execute("SELECT 1 FROM users WHERE username = :username", username=username):
        return jsonify(False)
    else:
        return jsonify(True)

@app.route("/profile")
@login_required
def profile():
    # select the information that the user inputed
    data = db.execute("SELECT username, SAT, ACT, GPA from users WHERE id = ?", session["user_id"])[0]

    #return the information so that it can be put on the HTML page using Jinja
    return render_template("profile.html", username=data["username"], act=data["ACT"], sat=data["SAT"], gpa=data["GPA"])


#updates the user's information
@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    if request.method == "POST":

        # Validate form submission
        if not request.form.get("username"):
            return apology("missing username")
        elif not request.form.get("password"):
            return apology("missing password")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")
        elif not request.form.get("GPA"):
            return apology("must enter GPA")

        # create a variable for the session id
        user_id = session["user_id"]

        # update the values that the user inputs into the user tables
        try:
            db.execute("UPDATE users SET username = ?, SAT = ?, ACT = ?, GPA = ? WHERE id = ?", request.form.get("username"), request.form.get("SAT"), request.form.get("ACT"), request.form.get("GPA"), user_id)

        except:
            return apology("unable to update profile")


        # Let user know they have updated their information!
        flash("Updated!")
        return redirect("/")
    # GET
    else:
        return render_template("update.html")



@app.route("/matches")
@login_required
def matches():
    # SQL query to get the GPA the user inputed
    ogpa = db.execute("SELECT GPA from users WHERE id = ?", session["user_id"])[0]["GPA"]
    # SQL query to get the amount of times this GPA shows up in the Harvard data
    gpa = db.execute("SELECT COUNT(*) FROM statistics WHERE gpa = ?",ogpa)[0]["COUNT(*)"]
    # calculation for the percentage 
    gpa = (gpa / 400) * 100

    # SQL query to get the SAT the user inputed
    osat= db.execute("SELECT SAT from users WHERE id = ?", session["user_id"])[0]["SAT"]
    # SQL query to get the amount of times this SAT shows up in the Harvard data
    sat = db.execute("SELECT COUNT(*) FROM statistics WHERE sat = ?",osat)[0]["COUNT(*)"]

    # calculation for the percentage 
    sat = (sat / 400) * 100

    # SQL query to get the ACT the user inputed
    oact = db.execute("SELECT ACT from users WHERE id = ?", session["user_id"])[0]["ACT"]
    # SQL query to get the amount of times this ACT shows up in the Harvard data
    act = db.execute("SELECT COUNT(*) FROM statistics WHERE act = ?",oact)[0]["COUNT(*)"]
    # calculation for the percentage 
    act = (act / 400) * 100

    # return the percentage values to be used in the HTML page using Jinja
    return render_template("matches.html", gpaPercent = gpa, satPercent = sat, actPercent = act)

@app.route("/aboutus")
@login_required
def aboutus():
        return render_template("aboutus.html")

@app.route("/contact")
@login_required
def contact():
        return render_template("contact.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


