from datetime import datetime

from flask_login import UserMixin

from extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class MuseumRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sr_no = db.Column(db.String(50))
    date = db.Column(db.String(50))
    accession_no = db.Column(db.String(50))
    code_no = db.Column(db.String(50))
    object_name = db.Column(db.String(200))
    pieces = db.Column(db.String(50))
    category = db.Column(db.String(100))
    material = db.Column(db.String(100))
    dimension = db.Column(db.String(100))
    form = db.Column(db.String(100))
    region = db.Column(db.String(100))
    purchase_date = db.Column(db.String(50))
    amount = db.Column(db.String(50))
    remarks = db.Column(db.String(300))

    description = db.Column(db.Text)
    historical_period = db.Column(db.String(100))
    creator = db.Column(db.String(200))
    cultural_significance = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    model_3d_url = db.Column(db.String(500))
    museum_name = db.Column(db.String(200))
    exhibition_name = db.Column(db.String(200))


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100))
    user = db.Column(db.String(100))
    record_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
