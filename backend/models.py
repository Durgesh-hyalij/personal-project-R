from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Patient(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    Name = db.Column(db.String(100) , nullable = False)
    phone = db.Column(db.Integer , nullable = False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    reports = db.relationship("Report", backref='patient' , lazy = True)

        
class Report(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    extracted_text = db.Column(db.String(1000) , nullable = False)
    pdf_path = db.Column(db.String(1000) , nullable = False)
    ai_summary = db.Column(db.Text, nullable=True   )
    created_at = db.Column(db.DateTime, default=db.func.now())
    #foreign key    
    patiend_id = db.Column(db.Integer, db.ForeignKey('patient.id') ,nullable = True )
    


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()