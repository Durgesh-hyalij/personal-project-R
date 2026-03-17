from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    is_admin = db.Column(db.Boolean, default=False)

    reports = db.relationship("Report", backref="user", lazy=True)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    extracted_text = db.Column(db.Text, nullable=False)
    pdf_path = db.Column(db.String(1000), nullable=False)
    ai_summary = db.Column(db.Text)
    analysis_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    lab_id = db.Column(db.Integer, db.ForeignKey("lab.id"), nullable=True)
    patient_email = db.Column(db.String(120))


class SharedAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    share_token = db.Column(db.String(255), unique=True, nullable=False)

    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship("User", backref="shared_links", lazy=True)


# -----------------------------
# NEW MODELS FOR LAB SYSTEM
# -----------------------------

class LabApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    lab_name = db.Column(db.String(200), nullable=False)
    owner_name = db.Column(db.String(150), nullable=False)

    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    address = db.Column(db.String(500))
    city = db.Column(db.String(100))

    license_number = db.Column(db.String(200))

    documents_path = db.Column(db.String(500))

    services = db.Column(db.JSON)

    working_hours = db.Column(db.String(200))

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    status = db.Column(db.String(50), default="pending")

    created_at = db.Column(db.DateTime, default=db.func.now())


class Lab(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    lab_name = db.Column(db.String(200), nullable=False)
    owner_name = db.Column(db.String(150))

    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    phone = db.Column(db.String(20))

    address = db.Column(db.String(500))
    city = db.Column(db.String(100))

    license_number = db.Column(db.String(200))

    services = db.Column(db.JSON)

    working_hours = db.Column(db.String(200))

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    is_verified = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=db.func.now())


def init_db(app):
    db.init_app(app)

    with app.app_context():
        db.create_all()