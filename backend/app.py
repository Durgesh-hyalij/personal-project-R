from flask import Flask, request, jsonify
from flask_cors import CORS
from PyPDF2 import PdfReader
import os
import cohere
from dotenv import load_dotenv  # Load .env file
from models import db, init_db, Report
from flask_sqlalchemy import SQLAlchemy

USE_AI = True   # 🔴 Turn OFF AI for development

# Load environment variables from .env file
if USE_AI:  # Optional: load env only if AI is enabled
    load_dotenv()

COHERE_API_KEY = os.getenv('API_URL')
UPLOAD_FOLDER = "Backend/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Defines the upload path and creates the directory if it doesn't already exist


# Create client ONLY if AI is enabled # COHERE_API_KEY = "COHERE_API_KEY"
co = None
if USE_AI and COHERE_API_KEY:
    co = cohere.Client(COHERE_API_KEY)

app = Flask(__name__)
CORS(app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_demo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def extract_text_from_pdf(pdf_path):  # Iterates through all PDF pages to extract and combine their text into a single string
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

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


@app.route("/upload-report", methods=["POST"])
def upload_report():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF allowed"}), 400

        path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(path)

        extracted_text = extract_text_from_pdf(path)
        if not extracted_text:
            return jsonify({"error": "No text extracted from PDF"}), 500

        if USE_AI:
            response = co.chat(
                model="c4ai-aya-expanse-32b",
                message=(
                    "You are a medical assistant. "
                    "Explain the following medical report in very simple language.\n\n"
                    f"{extracted_text}"
                ),
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
        # 1. Create the entry
        new_report = Report(
            extracted_text=extracted_text,
            pdf_path=path,
            ai_summary=ai_output
        )
        db.session.add(new_report)
        db.session.commit()
            
        return jsonify({
            "status": "success",
            "ai_response": ai_output
        })

    except Exception as e:          # Catches any server-side crashes, logs the error, and alerts the frontend
        print("ERROR:", e)
        return jsonify({"error": "Internal server error"}), 500   


if __name__ == "__main__":
    init_db(app)
    app.run(debug=True)
