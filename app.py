import os
from datetime import datetime, timedelta
import random
import string
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    make_response,
)
from werkzeug.utils import secure_filename
import jwt
from database import db
from controllers.login_authorize import login_authorize
from controllers.recipe_controller import *
from controllers.users_controller import *

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(APP_ROOT, "static/uploaded_images")



# generating random striing
def randstr():
    return "".join(
        random.choice(
            string.ascii_lowercase +
            string.digits) for _ in range(10))



@app.route("/", methods=["GET"])
def home():
    try:
        print("_______________________________", request.host_url)
        login_data = login_authorize(request, db)
        # if login is unsuccessfull redirecting to login page again
        islogin = True if login_data["success"] else False
        response = all_recipe_controller_home(
            {}, db_conn=db, host_url=request.host_url)
        return render_template("index.html", result=response, islogin=islogin)

    except BaseException:

        return render_template("error_handlers/error.html")


@app.route("/shop")
def shop():
    try:
        # checking for user login status  if not  then redirecting to login
        # page
        login_data = login_authorize(request, db)
        if not login_data["success"]:
            return redirect(url_for("login"))
        return render_template("misc/shop.html")
    except BaseException:
        return render_template("error_handlers/error.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    try:
        if request.method == "POST":
            checkbox = (request.form.get("checkbox")
                        if "checkbox" in request.form else "off")

            if checkbox == "off":
                error = "Please select terms & condition and proceed"
                return render_template("users/signup.html", error=error)

            payload = dict(
                email=request.form["email"],
                username=request.form["username"],
                password=request.form["password"],
                creadedOn=datetime.now(),
            )
            response = signup_controller(payload=payload, db_conn=db)
            print("response----------------------------", response)
            if response["success"]:
                return redirect(url_for("login"))
            else:
                error = "User already exists"
                return render_template("users/signup.html", error=error)

        return render_template("users/signup.html")
    except BaseException:
        return render_template("error_handlers/error.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            checkbox = (request.form.get("checkbox")
                        if "checkbox" in request.form else "off")

            if checkbox == "off":
                error = "Please select terms & condition and proceed"
                return render_template("users/login.html", error=error)
            # getting payload from login form
            print(request.form)
            payload = dict(
                email=request.form["email"],
                password=request.form["password"],
            )
            # verifying the user login
            response = login_controller(payload, db)
            print("user login verified", response)
            if response["success"]:
                # creating the JWT token for user session
                print("creating JWT token")
                encode = jwt.encode(
                    {
                        "iat": datetime.now(),
                        "email": payload["email"],
                        "exp": datetime.now() + timedelta(days=3),
                    },
                    "SECRET",
                    algorithm="HS256",
                )
                # print("encode--------------------",encode)
                resp = make_response(redirect(url_for("profile")))
                # token = str(encode).split("'")[1]
                print("token---------------", encode)
                # setting cookie using lofin token
                resp.set_cookie("logintoken", encode)
                return resp
            else:
                error = "Your email or password didn't match"
                return render_template("users/login.html", error=error)

        return render_template("users/login.html")
    except Exception as e:
        print("error ------------------", e)
        return render_template("error_handlers/error.html")


@app.route("/profile")
def profile():
    try:
        login_data = login_authorize(request, db)
        # print(login_data)
        # if login is unsuccessfull redirecting to login page again
        if not login_data["success"]:
            return redirect(url_for("login"))

        payload_filter = {"userId": login_data["_id"]}
        response = all_recipe_controller(
            payload_filter, db_conn=db, host_url=request.host_url)
        print("response---", response)
        return render_template(
            "users/myaccount.html",
            name=login_data["name"],
            result=response)
    except Exception as e:
        print("error----------------------------------", e)


@app.route("/logout")
def logout():
    try:
        # expering token for logout
        resp = make_response(redirect(url_for("login")))
        resp.set_cookie("logintoken", expires=0)
        return resp
    except BaseException:
        return render_template("error_handlers/error.html")


@app.route("/addrecipes", methods=["GET", "POST"])
def add_recipes():
    try:
        print("from add recipes...")
        # validating user before adding recipe
        login_data = login_authorize(request, db)
        print(login_data)
        # if login is unsuccessfull redirecting to login page again
        if not login_data["success"]:
            return redirect(url_for("login"))
        # we user is logged in reading user input from form
        if request.method == "POST":
            # reading the imade file
            image = request.files["imagefile"]
            # reading image url
            imagelink = request.form.get("imageurl")
            # when image filename is available saving the uploaded image file
            # to /static/uploaded_images/ directory
            if len(image.filename) != 0:
                image_file = secure_filename(randstr() + "-" + image.filename)
                image.save(os.path.join(IMAGE_DIR, image_file))
                imagelink = "/static/uploaded_images/" + str(image_file)
            # creating payload dictonary from form to save to database
            payload = dict(
                recipeName=request.form.get("recepiename", None),
                category=request.form.getlist("category", None),
                description=request.form.get("description", None),
                imageUrl=imagelink,
                servings=request.form.get("servings", None),
                preprationTime=request.form.get("preparationtime", None),
                cookingTime=request.form.get("cookingtime", None),
                ingredients=request.form.get("ingredients", None),
                instructions=request.form.get("instructions", None),
                tips=request.form.get("tips", None),
                userId=login_data["_id"],
                createdOn=datetime.now(),
                isFavourate=False,
                ratings=request.form.get("ratings", 0),
            )
            response = add_recipe_controller(payload=payload, db_conn=db)

            # print("response---------", response)
            return redirect(url_for("profile"))

        return render_template("recipes/addrecipes.html")
    except BaseException:
        return render_template("error_handlers/error.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
