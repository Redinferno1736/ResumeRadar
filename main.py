from flask import Flask
import google.generativeai as palm
from dotenv import load_dotenv
import os

palm.configure(api_key=os.getenv("API_KEY"))

def generate_response(user_input,name,trait):
    model = palm.GenerativeModel('models/gemini-1.5-pro')
    prompt = f"You are {name}. Respond {trait}:\nUser: {user_input}\n{name}:"
    response = model.generate_content(prompt)

    rresponse = response.text
    print(f"Output from API: {rresponse}")
    return rresponse
