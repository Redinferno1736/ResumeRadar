from flask import Flask, redirect,render_template, flash,request,session,url_for,send_file,jsonify
import google.generativeai as palm
from dotenv import load_dotenv
import os
import io
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo.errors import DuplicateKeyError
from datetime import datetime,timezone
from bson.objectid import ObjectId
from slugify import slugify
from authlib.integrations.flask_client import OAuth
from gridfs import GridFSBucket
from PyPDF2 import PdfReader

load_dotenv() 

palm.configure(api_key=os.getenv("API_KEY"))

flag=False

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

oauth = OAuth(app)  

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    userinfo_endpoint="https://www.googleapis.com/oauth2/v3/userinfo",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)

@app.route("/client/auth/google")
def google_login():
    global flag
    flag=False
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/rec/auth/google")
def rgoogle_login():
    global flag
    flag=True
    redirect_uri = url_for("google_callback" ,_external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/google/callback")
def google_callback():
    global flag
    if flag==False:
        token = google.authorize_access_token()
        user_info = google.get("https://www.googleapis.com/oauth2/v2/userinfo").json()
        session["user"] = user_info
        user = collection.find_one({'username': session["user"]['email']})
        if not user:
            collection.insert_one({'username': session["user"]['email'],'name':session["user"]['name']})
        session['username'] = session["user"]['email']
        session['client']={
            'name': session["user"]['name'],
            'email':session["user"]['email']
        }
        return redirect('/clienthome') 
     
    else:
        token = google.authorize_access_token()
        user_info = google.get("https://www.googleapis.com/oauth2/v2/userinfo").json()
        session["user"] = user_info
        host = recruiter.find_one({'username': session["user"]['email']})
        if not host:
            recruiter.insert_one({'username': session["user"]['email'],'name':session["user"]['name']})
        session['username'] = session["user"]['email']
        session['recruiter']={
            'name':session["user"]['name'],
            'email':session["user"]['email']
        }
        return redirect('/rechome')

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
                'role': job['role']
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
                'role': job['role']
            }
            for job in jobsopp
        ]
        return render_template("clienthome.html", user=user, jobs=jobs)
    return redirect('/login')

@app.route("/add/job", methods=["POST", "GET"])
def addjob():
    if request.method == 'POST':
        compname = request.form.get("compname")
        role = request.form.get("role")
        description = request.form.get("description")
        skills = request.form.get("skills")
        mode = request.form.get("mode")
        ldate = request.form.get("ldate")
        username = session['recruiter']['name']
        print(compname,username,ldate)
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
    add = client[slugify(job_det['compname'])]
    helper = add[slugify(job_det['role'])]
    job_det['_id'] = str(job_det['_id'])
    return render_template("recjobdetails.html", job_det=job_det)

@app.route("/user/<job_id>", methods=["POST", "GET"])
def job_details(job_id):
    job_det = hic.find_one({'_id': ObjectId(job_id)})
    if not job_det:
        flash("Job not found!")
        return redirect('/clienthome')
    add = client[slugify(job_det['compname'])]
    helper = add[slugify(job_det['role'])]
    job_det['_id'] = str(job_det['_id'])
    return render_template("jobdetails.html", job_det=job_det)

@app.route("/upload/<job_id>", methods=["POST", "GET"])
def upload_file(job_id):
    if request.method == "POST":
        job_det = hic.find_one({'_id': ObjectId(job_id)})
        if not job_det:
            flash("Job not found!")
            return redirect('/clienthome')

        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        
        add = client[slugify(job_det['compname'])]
        # helper = add[slugify(job_det['role'])]
        # add = client[slugify(hack['title'])] 
        bucket = GridFSBucket(add, bucket_name=slugify(job_det['role']))  # Use collection as bucket name

        # Save file to GridFSBucket
        file_id = bucket.upload_from_stream(file.filename, file)

        flash(f"File '{file.filename}' uploaded successfully!")
        return redirect('/clienthome')
    else:
        job_det = hic.find_one({'_id': ObjectId(job_id)})
        return render_template('upload.html',job_det=job_det)

@app.route("/<job_id>/files", methods=["POST", "GET"])
def list_files(job_id):
    job_det = hic.find_one({'_id': ObjectId(job_id)})
    if not job_det:
        flash("Job not found!")
        return redirect('/rechome')

    add = client[slugify(job_det['compname'])]
    # Get all team collections under the database
    comp_names = [col.replace(".files", "") for col in add.list_collection_names() if col.endswith(".files")]
    comp_files = {}
    for comp in comp_names:
        bucket = GridFSBucket(add, bucket_name=slugify(job_det['role']))
        files = add[f"{comp}.files"].find()
        comp_files[comp] = [{"filename": f["filename"], "id": str(f["_id"])} for f in files]
    return render_template("joblist.html", job_det=job_det, comp_files=comp_files)

@app.route("/<job_id>/<file_id>")
def serve_file(job_id,file_id):
    job_det = hic.find_one({'_id': ObjectId(job_id)})
    if not job_det:
        flash("Job not found!")
        return redirect('/rechome')

    add = client[slugify(job_det['compname'])]
    bucket = GridFSBucket(add, bucket_name=slugify(job_det['role']))

    file = bucket.open_download_stream(ObjectId(file_id))
    return send_file(
        io.BytesIO(file.read()),
        mimetype=file.content_type if hasattr(file, 'content_type') else 'application/octet-stream',
        download_name=file.filename
    )

# def generate_response(content, job_role, description, skills):
#     model = palm.GenerativeModel('models/gemini-1.5-pro')
#     prompt = f"Analyze resume content:/n{content}/nCategorize based on:/n1. Role: {job_role}/n2. Description: {description}/n3. Required Skills: {skills}/nOutput format:/nFirst line: [Good Fit|Maybe Fit|Not a Fit]/nSubsequent lines: Summary of why they were put in that category"
    
#     response = model.generate_content(prompt)
#     print(response.text)
#     return response.text

def generate_response(content, job_role, description, skills):
    print("DEBUG: content:", content[:100])  # print first 100 chars
    print("DEBUG: job_role:", job_role)
    print("DEBUG: description:", description)
    print("DEBUG: skills:", skills)

    model = palm.GenerativeModel('gemini-pro')  # Consider changing this too

    prompt = f"""Analyze resume content:\n{content}
Categorize based on:
1. Role: {job_role}
2. Description: {description}
3. Required Skills: {skills}
Output format:
First line: [Good Fit|Maybe Fit|Not a Fit]
Subsequent lines: Summary of why they were put in that category"""
    
    print("DEBUG: prompt formed:\n", prompt)

    response = model.generate_content(prompt)
    if not response:
        print("ERROR: Gemini returned None")
        return "Gemini returned no response"
    return response.text


@app.route("/<job_id>/segregate")
def segregate(job_id):
    job_det = hic.find_one({'_id': ObjectId(job_id)})
    add = client[slugify(job_det['compname'])]
    bucket = GridFSBucket(add, bucket_name=slugify(job_det['role']))
    
    files = add.fs.files.find()
    categorized = {"Good Fit": [], "Maybe Fit": [], "Not a Fit": []}

    for file in files:
        try:
            # Get file content as bytes
            file_data = bucket.open_download_stream(file['_id']).read()
            
            # Convert to text (add PDF/text file handling)
            if file.filename.endswith('.pdf'):
                from PyPDF2 import PdfReader
                pdf = PdfReader(io.BytesIO(file_data))
                content = "\n".join([page.extract_text() for page in pdf.pages])
            elif file.filename.endswith(('.docx', '.doc')):
                from docx import Document
                doc = Document(io.BytesIO(file_data))
                content = "\n".join([para.text for para in doc.paragraphs])
            else:  # Assume text file
                content = file_data.decode('utf-8')
            
            # Process with Gemini
            response = generate_response(
                content,
                job_det['role'],
                job_det['description'],
                job_det['skills']
            )
            category = response.split('\n')[0].strip()
            categorized[category].append(file['filename'])
            
        except Exception as e:
            print(f"Error processing {file['filename']}: {str(e)}")
            continue

    return render_template("segregate.html", categorized=categorized)


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/') 

if __name__ == "__main__":
    app.run(debug=False)