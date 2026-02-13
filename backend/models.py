from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    ai_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class SharedAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    share_token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="shared_links", lazy=True)
    
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()