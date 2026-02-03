import os
import io
import jwt
import datetime
import cohere
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from fpdf import FPDF
from functools import wraps

# Local Imports
from models import db, init_db, Report, User
from prompts.medical_prompt import build_medical_prompt
from auth import auth_bp

load_dotenv()

# --- Config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medmitra.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_super_secret_dev_key_123')

# Register Auth Blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

# --- AI Client ---
COHERE_API_KEY = os.getenv('API_URL')
co = None
if COHERE_API_KEY:
    try:
        co = cohere.Client(COHERE_API_KEY)
    except:
        print("⚠️ AI Client failed to connect.")

# --- HELPER: Token Security Guard ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Token format invalid!'}), 401

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.session.get(User, data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found!'}), 401
        except Exception:
            return jsonify({'error': 'Token is invalid or expired!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

def extract_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return "\n".join([page.extract_text() for page in reader.pages]).strip()
    except:
        return None

# ==========================================
#  ROUTES
# ==========================================

@app.route("/")
def check():
    return jsonify({"status": "API Active", "mode": "Secure Auth Mode"})

@app.route("/dashboard-stats", methods=["GET"])
@token_required
def dashboard_stats(current_user):
    total_reports = Report.query.filter_by(user_id=current_user.id).count()
    last_report = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).first()
    last_active = last_report.created_at.strftime("%d %b, %Y") if last_report else "New Member"

    return jsonify({
        "success": True,
        "user": {
            "name": current_user.name,
            "email": current_user.email,
            "avatar_url": f"https://ui-avatars.com/api/?name={current_user.name}&background=2563eb&color=fff&size=128&bold=true"
        },
        "stats": {
            "total_reports": total_reports,
            "last_active": last_active
        }
    })

@app.route("/upload-report", methods=["POST"])
@token_required
def upload_report(current_user):
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "PDF only"}), 400

    try:
        filename = f"{int(datetime.datetime.now().timestamp())}_{file.filename}"
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        
        text = extract_text(path)
        if not text or len(text.strip()) == 0:
            try: os.remove(path) 
            except: pass
            return jsonify({"error": "Scanned Image detected. Please use digital PDF."}), 400

        # AI Processing
        ai_summary = "AI Service Unavailable"
        if co:
            try:
                res = co.chat(
                    model="c4ai-aya-expanse-32b",
                    message=build_medical_prompt(text[:6000]),
                    temperature=0.3
                )
                ai_summary = res.text
            except Exception as e:
                ai_summary = f"AI Error: {str(e)}"

        # Save to DB
        new_report = Report(
            user_id=current_user.id,
            pdf_name=file.filename,
            pdf_path=path,
            extracted_text=text,
            ai_summary=ai_summary
        )
        db.session.add(new_report)
        db.session.commit()

        return jsonify({"success": True, "report_id": new_report.id, "ai_response": ai_summary})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/history", methods=["GET"])
@token_required
def history(current_user):
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    data = [{
        "id": r.id, 
        "pdf_name": r.pdf_name, 
        "date": r.created_at.strftime("%d %b, %I:%M %p")
    } for r in reports]
    return jsonify({"success": True, "data": data})

@app.route("/history/<int:id>", methods=["GET"])
@token_required
def get_report(current_user, id):
    report = Report.query.filter_by(id=id, user_id=current_user.id).first()
    if not report: return jsonify({"error": "Not found"}), 404
    return jsonify({
        "success": True,
        "data": {
            "pdf_name": report.pdf_name,
            "ai_summary": report.ai_summary,
            "id": report.id
        }
    })

@app.route("/history/<int:id>", methods=["DELETE"])
@token_required
def delete_report(current_user, id):
    report = Report.query.filter_by(id=id, user_id=current_user.id).first()
    if not report: return jsonify({"error": "Not found"}), 404
    try:
        if os.path.exists(report.pdf_path):
            os.remove(report.pdf_path)
        db.session.delete(report)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download-pdf/<int:id>")
@token_required
def download_pdf(current_user, id):
    report = Report.query.filter_by(id=id, user_id=current_user.id).first()
    if not report: return "Not found", 404

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    if report.ai_summary:
        clean_text = report.ai_summary.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, clean_text)
    else:
        pdf.cell(0, 10, "No summary.")
    
    return send_file(
        io.BytesIO(bytes(pdf.output())),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Summary_{report.id}.pdf"
    )

if __name__ == "__main__":
    init_db(app)
    app.run(debug=True, port=5000)