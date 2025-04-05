from flask import Flask, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
from pymongo import MongoClient

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

@app.route("/host/auth/google")
def hgoogle_login():
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
        print(session["user"]['email'])
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
        print(session["user"]['email'])
        host = hosts.find_one({'username': session["user"]['email']})
        if not host:
            hosts.insert_one({'username': session["user"]['email'],'name':session["user"]['name']})
        session['username'] = session["user"]['email']
        session['host']={
            'name':session["user"]['name'],
            'email':session["user"]['email']
        }
        print("Redirecting to:", url_for('hosthome_page'))
        return redirect('/hosthome')
