from flask import Flask, request, jsonify
from flask_cors import CORS
from PyPDF2 import PdfReader
import os
import cohere
from dotenv import load_dotenv  # Load .env file
from models import db, init_db, Report , User
# from flask_sqlalchemy import SQLAlchemy
from prompts.medical_prompt import build_medical_prompt  # from folder prompts file medical prompt
from flask import send_from_directory
from flask import request, send_file
from fpdf import FPDF
import io
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import jwt
from functools import wraps
from auth import hash_password, verify_password, create_token, get_current_user, get_admin_user

USE_AI = True   # 🔴 Turn OFF AI for development

# Load environment variables from .env file
if USE_AI:  # Optional: load env only if AI is enabled
    load_dotenv()

COHERE_API_KEY = os.getenv('API_URL')
# UPLOAD_FOLDER = "Backend/uploads"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "..", "static", "logo.png")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Defines the upload path and creates the directory if it doesn't already exist


# Create client ONLY if AI is enabled # COHERE_API_KEY = "COHERE_API_KEY"
co = None
if USE_AI and COHERE_API_KEY:
    co = cohere.Client(COHERE_API_KEY)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
CORS(app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_demo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


init_db(app)

def extract_text_from_pdf(pdf_path):  # Iterates through all PDF pages to extract and combine their text into a single string
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

class PDF(FPDF):
    def footer(self):
        self.set_y(-20)
        self.set_font("Arial", size=9)
        self.cell(0, 10, "© Project-R | AI Generated", align="C")

with app.app_context():   # with app.app_context() is required whenever you use Flask features outside a request, so Flask knows which app is active. eg - models , extentions , etc
    # db.create_all()

    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            name='admin',
            email='admin@example.com',
            password_hash=hash_password('admin123'),
            is_admin=True  # This makes user an admin
        )
        db.session.add(admin)
        db.session.commit()
        print('\n' + '='*50)
        print('DEFAULT ADMIN USER CREATED:')
        print('Email:    admin@example.com')
        print('Password: admin123')
        print('='*50 + '\n')
    else:
        print('\n' + '='*50)
        print('ADMIN LOGIN:')
        print('Email:    admin@example.com')
        print('Password: admin123')
        print('='*50 + '\n')




# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):

#         token = None

#         # 1️⃣ Read Authorization header
#         auth_header = request.headers.get("Authorization")

#         if auth_header and auth_header.startswith("Bearer "):
#             token = auth_header.split(" ")[1]

#         if not token:
#             return jsonify({
#                 "success": False,
#                 "message": "Token is missing"
#             }), 401

#         try:
#             # 2️⃣ Decode token
#             decoded = jwt.decode(
#                 token,
#                 app.config["SECRET_KEY"],
#                 algorithms=["HS256"]
#             )

#             # 3️⃣ Attach user_id to request
#             request.user_id = decoded["user_id"]

#         except jwt.ExpiredSignatureError:
#             return jsonify({
#                 "success": False,
#                 "message": "Token expired"
#             }), 401

#         except jwt.InvalidTokenError:
#             return jsonify({
#                 "success": False,
#                 "message": "Invalid token"
#             }), 401

#         # 4️⃣ Token valid → allow request
#         return f(*args, **kwargs)

#     return decorated


@app.route("/test")
def test():
    sample_pdf = os.path.join(app.config["UPLOAD_FOLDER"], "sample.pdf")

    if not os.path.exists(sample_pdf):
        return jsonify({"error": "sample.pdf not found"}), 404

    text = extract_text_from_pdf(sample_pdf)

    print("===== PDF TEXT PREVIEW =====")
    print(text[:1000])   # first 1000 chars
    print("===== END =====")

    return jsonify({
        "status": "success",
        "preview": text[:1000]
    })

@app.route("/register", methods=["POST"])
def register():
    data = request.json

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    # 1️⃣ Basic validation
    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    # 2️⃣ Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409

    # 3️⃣ Hash password
    password_hash = generate_password_hash(password)

    # 4️⃣ Create user
    new_user = User(
        name=name,
        email=email,
        password_hash=password_hash
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Registration failed"
        }), 500

    # 5️⃣ Success response
    return jsonify({
        "success": True,
        "message": "User registered successfully"
    }), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    if not verify_password(user.password_hash, password):
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401
    
    token = create_token(user.id , user.is_admin)

    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            'id' : user.id,
            'username' : user.name,
            'email': user.email,
            'is_admin' : user.is_admin
        }
    })


@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    # Step 1: Check if user is logged in AND is admin
    current_user, error = get_admin_user()
    print("current user in admin", current_user)
    if error:
        return error  # Returns 401 if not logged in, 403 if not admin
    
    users = User.query.all()

    return jsonify({
        "users": [{
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "is_admin": u.is_admin
        } for u in users]
    })


@app.route("/history/<int:id>", methods=["DELETE"])
# @token_required
def delete_report(id):
    # Step 1: Check if user is logged in AND is admin
    current_user, error = get_current_user()
    print("current user in admin", current_user)
    if error:
        return error  # Returns 401 if not logged in, 403 if not admin
    
    report = Report.query.get(id)

    if report.user_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403

    if not report:
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    # 🔹 Delete PDF file from disk
    if report.pdf_path and os.path.exists(report.pdf_path):
        try:
            os.remove(report.pdf_path)
        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Failed to delete PDF file"
            }), 500

    # 🔹 Delete DB record
    try:
        db.session.delete(report)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Failed to delete report from database"
        }), 500

    return jsonify({
        "success": True,
        "message": "Report deleted successfully"
    })


# @app.route("/history/<int:id>/pdf-name", methods=["PATCH"])
# def edit_pdf_name(id):
#     # 1️⃣ Fetch report
#     report = Report.query.get(id)

#     if not report:
#         return jsonify({
#             "success": False,
#             "message": "Report not found"
#         }), 404

#     # 2️⃣ Read input
#     data = request.json
#     new_name = data.get("pdf_name")

#     # 3️⃣ Validation
#     if not new_name or not new_name.strip():
#         return jsonify({
#             "success": False,
#             "message": "PDF name cannot be empty"
#         }), 400

#     # Force .pdf extension
#     if not new_name.lower().endswith(".pdf"):
#         new_name += ".pdf"

#     # 4️⃣ Update DB
#     report.pdf_name = new_name

#     try:
#         db.session.commit()
#     except Exception:
#         db.session.rollback()
#         return jsonify({
#             "success": False,
#             "message": "Failed to update PDF name"
#         }), 500

#     # 5️⃣ Response
#     return jsonify({
#         "success": True,
#         "message": "PDF name updated successfully",
#         "data": {
#             "id": report.id,
#             "pdf_name": report.pdf_name
#         }
#     })

    
@app.route("/generate-pdf", methods=["POST"])
# @token_required
def generate_pdf():
    # Step 1: Check if user is logged in AND is admin
    current_user, error = get_current_user()
   
    if error:
        return error  # Returns 401 if not logged in, 403 if not admin


    data = request.json
    ai_result = data.get("result", "")

    # pdf = FPDF()
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # LOGO
    pdf.image("backend/static/logo.png", x=10, y=8, w=25)
    # pdf.image(logo_path, x=10, y=8, w=25)

    # TITLE
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "AI Medical Report Summary", ln=True, align="C")

    # SUBTITLE
    pdf.set_font("Arial", size=10)
    pdf.cell(
        0, 8,
        f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
        ln=True,
        align="C"
    )

    pdf.ln(10)

    # CONTENT
    pdf.set_font("Arial", size=12)
    for line in ai_result.split("\n"):
        pdf.multi_cell(0, 8, line)

    # FOOTER
    # pdf.set_y(-20)
    # pdf.set_font("Arial", size=9)
    # pdf.cell(0, 10, "© Project-R | AI Generated", align="C")
    pdf.set_auto_page_break(auto=True, margin=20)


    # SEND PDF
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    pdf_stream = io.BytesIO(pdf_bytes)

    return send_file(
        pdf_stream,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="AI_Summary.pdf"
    )

@app.route("/history", methods=["GET"])
# @token_required
def get_report_history():
    # Step 1: Check if user is logged in AND is admin   
    current_user, error = get_current_user()
    
    if error:
        return error  # Returns 401 if not logged in, 403 if not admin
    
    # reports = Report.query.order_by(Report.created_at.desc()).all()  #gets all data and in new added first format
    reports = Report.query.filter_by(user_id=current_user.id).all()
    print("hello durgesh")
    print("AUTH HEADER:", request.headers.get("Authorization"))

    history_list = []

    for report in reports:
        history_list.append({
            "id": report.id,
            # "pdf_name": report.pdf_path.split("/")[-1],
            "pdf_name": os.path.basename(report.pdf_path),
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M"),
            "has_ai_summary": True if report.ai_summary else False
        })

    return jsonify({
        "success": True,
        "count": len(history_list),
        "data": history_list
    })

@app.route("/history/<int:report_id>", methods=["GET"])
# @token_required
def get_single_report(report_id):
     # Step 1: Check if user is logged in AND is admin
    current_user, error = get_current_user()
   
    if error:
        return error  # Returns 401 if not logged in, 403 if not admin
    
    # report = Report.query.get(report_id)
    report = db.session.get(Report, report_id)

    if report.user_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403

    if not report:
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    return jsonify({
        "success": True,
        "data": {
            "extracted_text": report.extracted_text,
            "ai_summary": report.ai_summary,
            "pdf_name": os.path.basename(report.pdf_path)
        }
    })

@app.route("/download/<path:filename>")
def download_pdf(filename):     #filename comes from URL (route)
    # print("UPLOAD FOLDER:", app.config["UPLOAD_FOLDER"])  #testing
    # print("FILENAME:", filename)
    
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=False  # if true the file automatically downloads 
    )
    

@app.route("/upload-report", methods=["POST"])
# @token_required
def upload_report():
     # Step 1: Check if user is logged in AND is admin
    current_user, error = get_current_user()
    print("/upload-repotr route", current_user.id)
    print("/upload-repotr route", error)
   
    if error:
        return error  # Returns 401 if not logged in, 403 if not admin
    
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF allowed"}), 400

        path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        print(path)
        file.save(path)

        extracted_text = extract_text_from_pdf(path)
        if not extracted_text:
            return jsonify({"error": "No text extracted from PDF"}), 500

        if USE_AI:
            response = co.chat(
                model="c4ai-aya-expanse-32b",
                # message=(
                #     "You are a medical assistant. "
                #     "Explain the following medical report in very simple language.\n\n"
                #     f"{extracted_text}"
                # ),
                message = build_medical_prompt(extracted_text[:6000]),
                temperature=0.3
            )
            ai_output = response.text    # Extracts the plain text answer from the AI's full response object
                                    # response.text -> this response come from the above response = co.chat)...)
        else:
            ai_output = (   
                "🔧 AI is disabled (development mode).\n\n"
                "Extracted PDF text preview:\n\n"
                + extracted_text[:1500]
            )
        # 1. Create the entry for database
        new_report = Report(
            extracted_text=extracted_text,
            pdf_path=path,
            ai_summary=ai_output,
            user_id=current_user.id
        )
        db.session.add(new_report)
        db.session.commit()
            
        return jsonify({
            "status": "success",
            "ai_response": ai_output
        })

    except Exception as e:          # Catches any server-side crashes, logs the error, and alerts the frontend
        print("ERROR:", e)
        print(e)
        return jsonify({"error": "Internal server errorrrrr"}), 500   


if __name__ == "__main__":
    # init_db(app)
    app.run(debug=True)
