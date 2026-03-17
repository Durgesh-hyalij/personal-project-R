from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from flask_cors import CORS
from PyPDF2 import PdfReader
import os
import uuid
import cohere
from dotenv import load_dotenv  # Load .env file
from models import db, init_db, Report, User, SharedAccess, LabApplication, Lab
from prompts.medical_prompt import build_medical_prompt  # from folder prompts file medical prompt
from fpdf import FPDF #for download ai pdf
import io
from datetime import datetime, timedelta, UTC, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
from auth import hash_password, verify_password, create_token, get_current_user, get_admin_user
import secrets
import re
from seed import create_default_admin
from werkzeug.utils import secure_filename
from flask_migrate import Migrate

USE_AI = True   # 🔴 Turn OFF AI for development

# Load environment variables from .env file
if USE_AI:  # Optional: load env only if AI is enabled
    load_dotenv()

COHERE_API_KEY = os.getenv('API_URL')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # SEE README.md file
logo_path = os.path.join(BASE_DIR, "static", "logo.png")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

FRONTEND_PATH = os.path.join(BASE_DIR, "..", "frontend")

# Create client ONLY if AI is enabled # COHERE_API_KEY = "COHERE_API_KEY"
co = None
if USE_AI and COHERE_API_KEY:
    co = cohere.Client(COHERE_API_KEY)

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
CORS(app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER     
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


init_db(app)
migrate = Migrate(app, db)

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
    create_default_admin()


# --- HTML PAGE ROUTES ---
@app.route('/')
def home():
    return send_from_directory(FRONTEND_PATH, 'welcome.html')

@app.route('/dashboard') # Changed from /index to be more descriptive
def index():
    return send_from_directory(FRONTEND_PATH, 'index.html')

@app.route('/login-page') # Added '-page' to avoid conflict with /login API
def login_page():
    return send_from_directory(FRONTEND_PATH, 'login.html')

@app.route('/register-page')
def register_page():
    return send_from_directory(FRONTEND_PATH, 'register.html')

@app.route('/admin-page')
def admin_page():
    return send_from_directory(FRONTEND_PATH, 'admin.html')

@app.route('/history-page') # IMPORTANT: Different name than the API /history
def history_page():
    return send_from_directory(FRONTEND_PATH, 'history.html')

@app.route('/doctor_vieww')
def doctor_vieww():
    return send_from_directory(FRONTEND_PATH, 'doctor_view.html')

@app.route("/test")
def test():
    return "test route and all running successfullyyyyyyyyyy"

@app.route('/lab-apply-page')
def lab_apply_page():
    return send_from_directory(FRONTEND_PATH, 'apply_lab.html')

@app.route('/uploads/<path:filename>')
def get_uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

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

@app.route("/lab/apply", methods=["POST"])
def apply_lab():

    try:

        lab_name = request.form.get("lab_name")
        owner_name = request.form.get("owner_name")
        email = request.form.get("email")
        phone = request.form.get("phone")

        city = request.form.get("city")
        address = request.form.get("address")

        license_number = request.form.get("license_number")

        working_hours = request.form.get("working_hours")

        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        services = request.form.get("services")

        file = request.files.get("document")

        doc_path = None
        filename = None
        if file:
            upload_folder = app.config["UPLOAD_FOLDER"]

            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)

            file_path = os.path.join(upload_folder, filename)

            file.save(file_path)

        new_application = LabApplication(
            lab_name=lab_name,
            owner_name=owner_name,
            email=email,
            phone=phone,
            city=city,
            address=address,
            license_number=license_number,
            documents_path=filename,
            services=services,
            working_hours=working_hours,
            latitude=latitude,
            longitude=longitude
        )

        db.session.add(new_application)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Application submitted. Waiting for admin approval."
        })

    except Exception as e:

        print(e)

        return jsonify({
            "success": False,
            "message": "Failed to submit application"
        }), 500
    

@app.route("/admin/lab-applications", methods=["GET"])
def get_lab_applications():

    current_user, error = get_admin_user()

    if error:
        return error

    applications = LabApplication.query.filter_by(status="pending").all()

    data = []

    for app in applications:
        data.append({
            "id": app.id,
            "lab_name": app.lab_name,
            "owner_name": app.owner_name,
            "email": app.email,
            "city": app.city,
            "license_number": app.license_number,
            "document": app.documents_path
        })

    return jsonify(data)

@app.route("/admin/approve-lab/<int:id>", methods=["POST"])
def approve_lab(id):

    current_user, error = get_admin_user()

    if error:
        return error

    application = LabApplication.query.get(id)

    if not application:
        return jsonify({"error": "Application not found"}), 404

    password = secrets.token_hex(4)

    password_hash = generate_password_hash(password)

    new_lab = Lab(
        lab_name=application.lab_name,
        owner_name=application.owner_name,
        email=application.email,
        phone=application.phone,
        city=application.city,
        address=application.address,
        license_number=application.license_number,
        services=application.services,
        working_hours=application.working_hours,
        latitude=application.latitude,
        longitude=application.longitude,
        password_hash=password_hash
    )

    db.session.add(new_lab)

    application.status = "approved"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Lab approved",
        "lab_password": password
    })

@app.route("/admin/reject-lab/<int:id>", methods=["POST"])
def reject_lab(id):

    current_user, error = get_admin_user()

    if error:
        return error

    application = db.session.get(LabApplication, id)

    if not application:
        return jsonify({"error": "Application not found"}), 404

    application.status = "rejected"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Lab rejected"
    })

@app.route("/labs", methods=["GET"])
def get_labs():

    labs = Lab.query.all()

    data = []

    for lab in labs:
        data.append({
            "id": lab.id,
            "lab_name": lab.lab_name,
            "city": lab.city,
            "services": lab.services,
            "latitude": lab.latitude,
            "longitude": lab.longitude
        })

    return jsonify(data)


@app.route("/labs/<int:id>", methods=["GET"])
def get_lab_details(id):

    lab = Lab.query.get(id)

    if not lab:
        return jsonify({"error": "Lab not found"}), 404

    return jsonify({
        "lab_name": lab.lab_name,
        "owner_name": lab.owner_name,
        "city": lab.city,
        "address": lab.address,
        "phone": lab.phone,
        "services": lab.services,
        "working_hours": lab.working_hours,
        "latitude": lab.latitude,
        "longitude": lab.longitude
    })

@app.route("/labs/search")
def search_lab():

    city = request.args.get("city")

    labs = Lab.query.filter_by(city=city).all()

    data = []

    for lab in labs:
        data.append({
            "id": lab.id,
            "lab_name": lab.lab_name,
            "city": lab.city
        })

    return jsonify(data)

@app.route("/lab/login", methods=["POST"])
def lab_login():

    data = request.json

    email = data.get("email")
    password = data.get("password")

    lab = Lab.query.filter_by(email=email).first()

    if not lab:
        return jsonify({"error": "Invalid login"}), 401

    if not check_password_hash(lab.password_hash, password):
        return jsonify({"error": "Invalid login"}), 401

    token = create_token(lab.id)

    return jsonify({
        "success": True,
        "token": token,
        "lab": {
            "lab_name": lab.lab_name,
            "city": lab.city
        }
    })

@app.route("/lab/upload-report", methods=["POST"])
def lab_upload_report():

    try:

        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Unauthorized"}), 401

        token = token.split(" ")[1]

        data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])

        lab = Lab.query.get(data["user_id"])

        if not lab:
            return jsonify({"error": "Invalid lab"}), 401

        patient_email = request.form.get("patient_email")

        file = request.files.get("file")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)

        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        file.save(path)

        extracted_text = extract_text_from_pdf(path)

        if USE_AI:

            response = co.chat(
                model="c4ai-aya-expanse-32b",
                message=build_medical_prompt(extracted_text[:6000]),
                temperature=0.3
            )

            ai_output = response.text

        else:

            ai_output = extracted_text[:1500]

        new_report = Report(
            extracted_text=extracted_text,
            pdf_path=path,
            ai_summary=ai_output,
            lab_id=lab.id,
            patient_email=patient_email
        )

        db.session.add(new_report)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Report uploaded successfully",
            "ai_summary": ai_output
        })

    except Exception as e:

        print(e)

        return jsonify({"error": "Upload failed"}), 500
    
@app.route("/lab/reports", methods=["GET"])
def lab_reports():

    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    token = token.split(" ")[1]

    data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])

    lab = Lab.query.get(data["user_id"])

    reports = Report.query.filter_by(lab_id=lab.id).all()

    data = []

    for r in reports:

        data.append({
            "id": r.id,
            "patient_email": r.patient_email,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
        })

    return jsonify(data)

@app.route("/patient/reports")
def patient_reports():

    email = request.args.get("email")

    reports = Report.query.filter_by(patient_email=email).all()

    data = []

    for r in reports:

        data.append({
            "id": r.id,
            "ai_summary": r.ai_summary,
            "created_at": r.created_at.strftime("%Y-%m-%d")
        })

    return jsonify(data)

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
    logo_path = os.path.join("static", "logo.png")
    pdf.image(logo_path, x=10, y=8, w=25)
    # pdf.image("backend/static/logo.png", x=10, y=8, w=25)
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

        # path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        # print(path)
        # file.save(path)

        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
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

        analysis_data = {
            "risk_level": "Low",
            "ai_model": "c4ai-aya-expanse-32b",
            "word_count": len(extracted_text.split()),
            "generated_at": datetime.utcnow().isoformat()
        }

        # 1. Create the entry for database
        new_report = Report(
            extracted_text=extracted_text,
            pdf_path=path,
            ai_summary=ai_output,
            user_id=current_user.id,
            analysis_data=analysis_data
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


@app.route("/share-reports", methods=["POST"])
def share_reports():
    current_user, error = get_current_user()
    if error:
        return error

    # Step 1: Delete existing share link (only one active allowed)
    existing_share = SharedAccess.query.filter_by(user_id=current_user.id).first()

    if existing_share:
        db.session.delete(existing_share)
        db.session.commit()

    # Step 2: Generate secure token
    token = secrets.token_urlsafe(32)

    # Step 3: Set expiration
    expires_at = datetime.now(UTC) + timedelta(days=7)

    # Step 4: Create new share entry
    new_share = SharedAccess(
        user_id=current_user.id,
        share_token=token,
        expires_at=expires_at
    )

    db.session.add(new_share)
    db.session.commit()

    # # Step 5: Return real link
    # return jsonify({
    #     "share_link": f"http://127.0.0.1:5000/doctor-view/{token}"
    # })
    # Step 5: Return the UI link (not the API link)
    return jsonify({
        "success": True,
        "share_link": f"http://127.0.0.1:5000/doctor-report/{token}"
    })


@app.route('/doctor-report/<token>')
def view_report_page(token):
    return send_from_directory(FRONTEND_PATH, 'doctor_view.html')

@app.route('/doctor-view/<token>', methods=['GET'])
def doctor_view(token):
    shared = SharedAccess.query.filter_by(share_token=token).first()

    if not shared:
        return jsonify({"success": False, "error": "Invalid or expired link"}), 404

    if datetime.now(UTC) > shared.expires_at:
        return jsonify({"success": False, "error": "Link has expired"}), 403

    reports = Report.query.filter_by(user_id=shared.user_id).all()
    patient = shared.user 

    # Serialize Patient
    patient_data = {
        "username": patient.name,
        "email": patient.email
    }

    # Serialize Reports
    reports_data = [{
        "id": r.id,
        "ai_summary": r.ai_summary,
        "extracted_text": r.extracted_text,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") 
    } for r in reports]

    return jsonify({
        "success": True,
        "patient": patient_data,
        "reports": reports_data,
        "expires_at": shared.expires_at.strftime("%Y-%m-%d %H:%M")
    })

# --- STATIC FILES ROUTE (The 404 Fix) ---
# This MUST be below the other routes
@app.route('/<path:filename>')
def serve_frontend_files(filename):
    return send_from_directory(FRONTEND_PATH, filename)

if __name__ == "__main__":
    # init_db(app)
    app.run(debug=True)
