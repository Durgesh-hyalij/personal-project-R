WHAT HAPPENS WHEN USER LOGS IN (FULL FLOW)
User enters email + password
        ↓
Frontend sends POST /login
        ↓
Backend finds user by email
        ↓
Backend checks password hash
        ↓
If correct → generate JWT
        ↓
Send JWT to frontend
        ↓
Frontend stores token
        ↓
User is now "logged in"


🩺 Project-R — AI-Powered Medical Report Analyzer

Project-R is a full-stack web application that allows users to register, login, upload medical PDF reports, analyze them using AI, and securely view their history.

It uses JWT authentication, Flask backend, and a separate frontend (HTML + JS).

🚀 Features Overview
🔐 Authentication

User Registration

User Login

JWT (JSON Web Token) based authentication

Secure logout

Frontend route protection

📄 Report Management

Upload PDF medical reports

Extract text from PDFs

AI-generated medical summary

View report history (user-specific)

View / Download original PDF

Download AI summary as PDF

Delete reports

🔒 Security

Each user sees only their own reports

Protected API routes using JWT

Token expiration handling

Unauthorized access prevention

🧠 Tech Stack
Backend

Python

Flask

Flask-SQLAlchemy

JWT (PyJWT)

FPDF (for PDF generation)

PyPDF2 (PDF text extraction)

Cohere AI (optional / configurable)

Frontend

HTML

CSS

Vanilla JavaScript

Fetch API

Marked.js (Markdown rendering)

Database

SQLite (development)

📁 Project Structure
project-root/
│
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── uploads/
│   └── api_demo.db
│
├── frontend/
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   └── history.html
│
├── static/
│   └── logo.png
│
├── prompts/
│   └── medical_prompt.py
│
├── .env
└── README.md

🔑 Authentication Flow (IMPORTANT)
1️⃣ Register

User registers with name, email, password

Password is hashed before saving

Stored in database securely

2️⃣ Login

User logs in using email + password

Backend verifies credentials

Backend generates JWT token

Token is sent to frontend

3️⃣ Token Storage

Frontend stores token in:

localStorage.setItem("token", token);

4️⃣ Using Token

Token is sent in Authorization header for protected APIs:

Authorization: Bearer <JWT_TOKEN>

5️⃣ Logout

Token removed from localStorage

User redirected to login page

🔐 JWT Explained (Beginner Friendly)

JWT contains:

user_id

email

expiry time

Why JWT?

No server-side session needed

Works well with separate frontend/backend

Stateless and secure

Token Validation

Every protected route uses:

@token_required


This:

Reads token from request header

Verifies token

Extracts user_id

Attaches it to request.user_id

📄 Upload Report Flow

1️⃣ User logs in
2️⃣ Uploads a PDF
3️⃣ Frontend sends file + JWT token
4️⃣ Backend:

Saves PDF

Extracts text

Calls AI (if enabled)

Saves report linked to user_id

new_report = Report(
    extracted_text=extracted_text,
    pdf_path=path,
    ai_summary=ai_output,
    user_id=request.user_id
)

📜 Report History Flow

/history API is protected

Backend filters reports by user_id

Report.query.filter_by(user_id=request.user_id).all()

Result:

User sees only their own reports

No data leakage between users

🖥 Frontend Route Protection

Every protected page starts with:

if (!localStorage.getItem("token")) {
  window.location.href = "login.html";
}


This prevents:

Direct URL access

Unauthorized page loading

📥 API Endpoints
🔓 Public
Method	Route	Description
POST	/register	Register new user
POST	/login	Login user
🔐 Protected (JWT Required)
Method	Route	Description
POST	/upload-report	Upload PDF report
GET	/history	Get user report history
GET	/history/<id>	Get single report
DELETE	/history/<id>	Delete report
GET	/download/<filename>	Download PDF
POST	/generate-pdf	Download AI summary PDF
🧪 Common Issues & Fixes
❌ 401 Unauthorized

Cause: Token not sent
Fix: Add Authorization header

headers: {
  "Authorization": "Bearer " + localStorage.getItem("token")
}

❌ History Empty

Cause: Reports uploaded before login
Fix: Logout → Login → Upload again

❌ DB Column Errors

Cause: Model changed after DB creation
Fix: Delete api_demo.db and restart server

⚙️ Environment Setup
.env file
SECRET_KEY=your_long_secret_key_here
API_URL=your_cohere_api_key

▶️ How to Run Project
Backend
cd backend
python app.py

Frontend

Open HTML files directly

Or use Live Server (VS Code)