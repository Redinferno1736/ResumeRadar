import google.generativeai as palm
from dotenv import load_dotenv
import os

load_dotenv()
palm.configure(api_key=os.getenv("API_KEY"))

model = palm.GenerativeModel('models/gemini-1.5-pro')
prompt = f"""who are you"""

response = model.generate_content(prompt)
print(response.text)