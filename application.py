import os, datetime,requests

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():

    # Find the data stored in User name and Password
    uname = request.form.get("inputUserName")
    passw = request.form.get("inputPassword")

    # Field Validation
    if uname=="" or passw=="":
        return render_template("index.html",  errormessage="Enter the credentials")

    # Check if the username is present in the DB
    if db.execute("SELECT * FROM UserDetails WHERE username = :username", {"username": uname}).rowcount == 0:
        return render_template("index.html", errormessage="User Name or Password does not match.")
    userinfo =db.execute("SELECT * FROM UserDetails WHERE username = :username", {"username": uname}).fetchone()

    # Check if the password matches
    if db.execute("SELECT * FROM UserCred WHERE loginid = :loginid and password=:password", {"loginid": userinfo.loginid,"password": passw}).rowcount == 0:
        return render_template("index.html", errormessage="User Name or Password does not match.")

    # Store the values in session
    session["username"] = uname
    session["fname"] = userinfo.firstname

    return render_template("search.html",books=None, username= session["fname"])

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "GET":
       return render_template("registration.html")

    # Post Code
    # Get the form data
    fname = request.form.get("inputFirstName")
    lname = request.form.get("inputLastName")
    email = request.form.get("inputEmail")
    uname = request.form.get("inputUserName")
    passw = request.form.get("inputPassword")
    createddate = datetime.datetime.now()


    # Check if the username exists and update userdetails table
    if db.execute("SELECT * FROM userdetails WHERE username = :username", {"username": uname}).rowcount != 0:
        return render_template("registration.html", errormessage="User Name exists.")
    db.execute("INSERT INTO UserDetails (firstname,lastname,email,username,createddate) VALUES (:fname, :lname, :email, :uname, :createddate)",
            {"fname": fname, "lname": lname, "email": email, "uname": uname, "createddate": createddate})
    db.commit()

    # Check and insert to usercred table
    loginid =db.execute("SELECT loginid FROM UserDetails WHERE username = :username", {"username": uname}).fetchone()[0]
    if db.execute("SELECT * FROM usercred WHERE loginid = :loginid", {"loginid": loginid}).rowcount != 0:
        return render_template("registration.html", errormessage="User Name exists.")
    db.execute("INSERT INTO UserCred (loginid,password,createddate) VALUES (:loginid, :passw, :createddate)",
            {"loginid": loginid, "passw": passw, "createddate": createddate})
    db.commit()

    # After registration proceed to Login page
    return render_template("index.html")

@app.route("/logout")
def logout():
    return render_template("index.html")

# Function to format LIKE query
def formatsqllike(sqlparam):
    if sqlparam is not None and  sqlparam != "":
        return "%"+sqlparam+"%"
    else:
        return ""

@app.route("/search", methods=["GET","POST"])
def search():

    if request.method == "GET":
       return render_template("search.html", username = session["fname"])

    # Fetch the matching books
    books = db.execute("SELECT * FROM bookdetails WHERE title ILIKE  :title or isbn ILIKE  :isbn or author ILIKE  :author",
    {"title": formatsqllike(request.form.get("title")), 
    "isbn": formatsqllike(request.form.get("isbn")), 
    "author": formatsqllike(request.form.get("author"))}
    ).fetchall()

    return render_template("search.html",books = books, username = session["fname"])


@app.route("/search/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    errormessage = None
    username = session["username"]  
    
    if request.method == "POST":
        rating = request.form.get("rating")
        review = request.form.get("review")
        if rating is not None:
            if db.execute("SELECT * FROM bookreviews WHERE username = :username and isbn = :isbn",
                {"username": username, "isbn": isbn}).rowcount != 0:
                errormessage ="Review already exists for user"
            else :
                db.execute("INSERT INTO bookreviews (username, isbn, rating, comments, createddate) VALUES (:username, :isbn, :rating, :review,:createddate)",
            {"username": username, "isbn": isbn, "rating": rating, "review": review, "createddate": datetime.datetime.now()})
                db.commit()
        else:
            errormessage = "Enter the rating for the book"
            
    myRating = db.execute("SELECT * FROM bookreviews WHERE username = :username and isbn = :isbn",
                {"username": username, "isbn": isbn}).fetchone()
    othersRating = db.execute("SELECT * FROM bookreviews WHERE username != :username and isbn = :isbn",
                {"username": username, "isbn": isbn}).fetchall()
    bookRating = db.execute("SELECT round(avg(rating),2) as avg_rating, count(rating) as count_rating FROM bookreviews WHERE isbn = :isbn group by isbn",
                { "isbn": isbn}).fetchone()
    book = db.execute("SELECT * FROM bookdetails WHERE isbn = :isbn",{"isbn": isbn}).fetchone()
    
    goodreadsapi = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "tFWVreMs4KdSkUeopIj3w", "isbns": isbn})
    if goodreadsapi is not None and goodreadsapi.json() is not None:
        goodreadRating = goodreadsapi.json()["books"][0]
  
    return render_template("book.html", 
    book=book, 
    rating=goodreadRating, 
    myrating=myRating, 
    otherratings=othersRating,
    bookRating=bookRating, 
    username=session["fname"],
    errormessage=errormessage)
    



@app.route("/api/<string:isbn>")
def bookdetailsapi(isbn):
    book = db.execute("SELECT * FROM bookdetails WHERE isbn = :isbn",{"isbn": isbn}).fetchone()
    bookRating = db.execute("SELECT round(avg(rating),2) as avg_rating, count(rating) as count_rating FROM bookreviews WHERE isbn = :isbn group by isbn",
                { "isbn": isbn}).fetchone()
    if book is None:
        message = {
            'status': 404,
            'message': 'Book not found',
        }
        return jsonify(message), 404
    return jsonify({
	"title": book.title,
	"author": book.author,
	"year": book.year,
	"isbn": book.isbn,
	"review_count": bookRating.count_rating,
	"average_score": str(bookRating.avg_rating)
	})
