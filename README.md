# ResumeRadar

## Overview
**ResumeRadar** is a web application designed to streamline the hiring process by providing tools for recruiters to manage job listings and categorize resumes based on their suitability for specific roles. It also offers applicants an intuitive platform to apply for jobs and upload their resumes.



## Features

### For Recruiters:
- **Job Management**:
  - Add new job listings.
  - View previous job listings.
  - Access uploaded resumes for each job.
- **Resume Categorization**:
  - Automatically classify resumes into "Good Fit," "Maybe Fit," and "Not a Fit" using AI analysis.

### For Applicants:
- **Job Search**:
  - Browse available job listings.
  - View detailed job descriptions.
- **Resume Upload**:
  - Upload resumes directly for specific job applications.

### Authentication:
- Google OAuth integration for seamless login and registration.
- Separate login/registration flows for recruiters and applicants.


## Installation

### Prerequisites
- Python 3.x
- MongoDB
- Virtual environment (optional)
- API keys for Google OAuth and generative AI (e.g., Gemini model).

### Steps
1. Clone the repository:
   ```
   git clone https://github.com/your-repo/resumeradar.git
   cd resumeradar
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add the following keys:
   ```
   API_KEY=
   MONGO_CLIENT=
   SECRET_KEY=
   GOOGLE_CLIENT_ID=
   GOOGLE_CLIENT_SECRET=
   ```

4. Run the application:
   ```
   python main.py
   ```

5. Access the application at `http://127.0.0.1:5000`.

---

## File Structure

### Backend (Python/Flask)
- **main.py**: Contains all routes and core logic for the application.
- **app.py**: Handles AI-related functionalities using generative AI models.

### Frontend (HTML/CSS)
- **templates/**: Contains HTML templates for different pages (e.g., home, login, job details).
- **static/**: Contains CSS files and assets for styling.

### Database (MongoDB)
- **userinfo**: Stores user data (applicants and recruiters).
- **jobsinfo**: Stores job listings and associated data.



## Key Functionalities

### Recruiter Workflow
1. Login/Register via Google or manual credentials.
2. Add new job listings via `/add/job`.
3. View previous job listings on `/rechome`.
4. Access resumes uploaded by applicants via `/rec//files`.
5. Categorize resumes using AI on `/segregate`.

### Applicant Workflow
1. Login/Register via Google or manual credentials.
2. Browse available jobs on `/clienthome`.
3. View detailed job descriptions on `/user/`.
4. Upload resume via `/upload/`.



## Technologies Used

### Backend
- Flask: Web framework for Python.
- MongoDB: NoSQL database for storing user and job data.
- Generative AI Model: Used to analyze resumes and categorize them.

### Frontend
- HTML/CSS: For page structure and styling.
- JavaScript (optional): For dynamic interactions.



## How Resume Categorization Works

1. Resumes are uploaded in various formats (PDF, DOCX, etc.).
2. The content is extracted using libraries like `PyPDF2` or `python-docx`.
3. The extracted text is analyzed using a generative AI model (e.g., Gemini).
4. Resumes are categorized into "Good Fit," "Maybe Fit," or "Not a Fit" based on role, description, and required skills.



## Future Enhancements

1. Add support for more file formats during resume upload.
2. Improve resume categorization accuracy using advanced AI models.
3. Implement notifications for recruiters when new resumes are uploaded.
4. Enhance UI/UX design for better user experience.
