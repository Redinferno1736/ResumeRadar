from flask import Flask, redirect,render_template, flash,request,session
import google.generativeai as palm
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo.errors import DuplicateKeyError


palm.configure(api_key=os.getenv("API_KEY"))

def generate_response(name,job_title,description):
    model = palm.GenerativeModel('models/gemini-1.5-pro')
    prompt = f"You are the recruiter and the user's resume is {name}. Categorize based on these stuffs.\n 1.{job_title} \n 2.{description} 3.Skills \n 4.Projects \n 5.Education \n 6.Certifications" 
    response = model.generate_content(prompt)

    rresponse = response.text
    print(f"Output from API: {rresponse}")
    return rresponse

load_dotenv() 

client = MongoClient(os.getenv("MONGO_CLIENT"))
db = client['userinfo']
collection = db['users']
recruiter=db['recruiters']
collection.create_index("username", unique=True)
recruiter.create_index("username", unique=True)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login",methods=["GET","POST"])
def login_page():
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        user = collection.find_one({'username': username})

        if check_password_hash(user["hash"], password):  
            session['username'] = username
            session['client'] = {
                'name': user.get('name'),
            }
            return redirect('/clienthome')
        else:
            flash("Invalid username or password!")
            return render_template("login.html")
    else:
        return render_template("login.html")

@app.route("/register",methods=["GET","POST"])
def register_page():
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        confirm=request.form.get("confirm")
        print(username,password,confirm)
        if password != confirm:
            flash("Passwords do not match!")
            return render_template("register.html")

        hash = generate_password_hash(password)
        try:
            collection.insert_one({'username': username, 'hash': hash})
            return redirect('/login')
        except DuplicateKeyError:
            flash("Username has already been registered!")
            return render_template("register.html")
    else:
        return render_template("register.html")

@app.route("/regrec",methods=["GET","POST"])
def regrec_page():
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        confirm=request.form.get("confirm")
        compname=request.form.get("compname")
        if password != confirm:
            flash("Passwords do not match!")
            return render_template("regrec.html")

        hash = generate_password_hash(password)
        try:
            recruiter.insert_one({'username': username, 'hash': hash, 'companyname':compname})
            return redirect('/logrec')
        except DuplicateKeyError:
            flash("Username has already been registered!")
            return render_template("regrec.html")
    else:
        return render_template("regrec.html")

@app.route("/logrec",methods=["GET","POST"])
def logrec_page():
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")

        rec = recruiter.find_one({'username': username})

        if check_password_hash(rec["hash"], password): 
            session['username'] = username
            session['recruiter'] = {
                'name': rec.get('name'),
                'companyname': rec.get('companyname')
            }
            return redirect('/rechome')
        else:
            flash("Invalid username or password!")
            return render_template("logrec.html")
    else:
        return render_template("logrec.html") 

if __name__ == "__main__":
    app.run(debug=False)