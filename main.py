from flask import Flask, redirect,render_template, flash,request,session
import google.generativeai as palm
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo.errors import DuplicateKeyError
from datetime import datetime,timezone
from bson.objectid import ObjectId
from slugify import slugify

palm.configure(api_key=os.getenv("API_KEY"))

def generate_response(name,job_title,description):
    model = palm.GenerativeModel('models/gemini-1.5-pro')
    prompt = f"You are the recruiter and the user's resume is {name}. Categorize based on these stuffs.\n 1.{job_title} \n 2.{description} 3.Skills \n 4.Projects \n 5.Education \n 6.Certifications\n give output with first line as either one of 'Good Fit' or 'Maybe Fit' or 'Not a Fit' and from second line give a summary on why that person was categoried into the category returned in line 1" 
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
hi = client['jobsinfo']
hic = hi['jobinfo']

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") 

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
                'name': user.get('username'),
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
        if password != confirm:
            flash("Passwords do not match!")
            return render_template("regrec.html")

        hash = generate_password_hash(password)
        try:
            recruiter.insert_one({'username': username, 'hash': hash})
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
                'name': rec.get('username')
            }
            return redirect('/rechome')
        else:
            flash("Invalid username or password!")
            return render_template("logrec.html")
    else:
        return render_template("logrec.html") 

@app.route("/rechome",methods=["GET","POST"])
def rechome_page():
    recruiter = session.get('recruiter')
    if recruiter:
        rec = hic.find({'username': recruiter['name']})
        jobs = [
            {
                'id': str(job['_id']),  
                'compname': job['compname'],
                'title': job['title']
            }
            for job in rec
        ]
        return render_template("rechome.html", rec=rec, jobs=jobs)
    return redirect('/logrec')

@app.route("/clienthome", methods=["GET", "POST"])
def clienthome_page():
    user = session.get('client')
    if user:
        today = datetime.now(timezone.utc)
        jobsopp = hic.find({'ldate': {'$gte': today}})

        jobs = [
           {
                'id': str(job['_id']),  
                'compname': job['compname'],
                'title': job['title']
            }
            for job in jobsopp
        ]
        return render_template("clienthome.html", user=user, jobs=jobs)
    return redirect('/login')

@app.route("/add/hack", methods=["POST", "GET"])
def addhack():
    if request.method == 'POST':
        compname = request.form.get("compname")
        role = request.form.get("role")
        description = request.form.get("description")
        skills = request.form.get("skills")
        mode = request.form.get("mode")
        ldate = request.form.get("ldate")
        username = session['recruiter']['name']

        hic.insert_one({
            'username':username,
            'compname': compname, 
            'role': role,
            'description': description,
            'skills': skills,
            'mode': mode,
            'ldate': datetime.strptime(ldate, '%Y-%m-%d')
        })
        return redirect('/rechome')
    else:
        return render_template("newjob.html")

@app.route("/rec/<job_id>", methods=["POST", "GET"])
def recjob_details(job_id):
    job_det = hic.find_one({'_id': ObjectId(job_id)})
    if not job_det:
        flash("Job not found!")
        return redirect('/rechome')
    add = client[slugify(job_det['title'])]
    helper = add['jobinfo']
    job_det['_id'] = str(job_det['_id'])
    return render_template("recjobdetails.html", job_det=job_det)

@app.route("/<job_id>", methods=["POST", "GET"])
def job_details(job_id):
    job_det = hic.find_one({'_id': ObjectId(job_id)})
    if not job_det:
        flash("Job not found!")
        return redirect('/clienthome')
    add = client[slugify(job_det['title'])]
    helper = add['jobinfo']
    job_det['_id'] = str(job_det['_id'])
    return render_template("jobdetails.html", job_det=job_det)

# def upload_file(job_id):
#     if request.method == "POST":
#         job = jobs.find_one({'_id': ObjectId(job_id)})
#         if not job:
#             flash("Job not found!")
#             return redirect('/clienthome')

#         if "file" not in request.files:
#             flash("No file part")
#             return redirect(request.url)
        
#         file = request.files["file"]
#         if file.filename == "":
#             flash("No selected file")
#             return redirect(request.url)
        
#         add = client[slugify(hack['title'])]  # Database
#         bucket = GridFSBucket(add, bucket_name=slugify(teamname))  # Use collection as bucket name

#         # Save file to GridFSBucket
#         file_id = bucket.upload_from_stream(file.filename, file)

#         flash(f"File '{file.filename}' uploaded successfully!")
#         return redirect(url_for("list_files", hack_id=hack_id, teamname=teamname))
#     else:
#         hack = hic.find_one({'_id': ObjectId(hack_id)})
#         return render_template("upload.html", hack=hack)


# @app.route("/segregate",methods=["GET","POST"])
# def seperate():

#     response=generate_response(name,job_title,description)

@app.route("/logout")
def logout():
    session.clear()
    return redirect('/') 

if __name__ == "__main__":
    app.run(debug=False)