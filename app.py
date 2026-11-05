import io
import os
import secrets
from xml.sax.saxutils import escape

import pandas as pd
from flask import (
    Flask, render_template, request, redirect, url_for,
    send_file, flash
)
from flask_login import (
    login_user, login_required, logout_user, current_user
)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import inspect, or_, text
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager
from models import User, MuseumRecord, AuditLog

app = Flask(__name__)

# Set FLASK_SECRET_KEY in your environment for a stable production secret.
# The generated fallback is suitable only for local development.
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///museum.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_HTTPS_ONLY") == "1"

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access the admin area."
login_manager.login_message_category = "info"

ALLOWED_FIELDS = {
    "sr_no", "date", "accession_no", "code_no", "object_name",
    "pieces", "category", "material", "dimension", "form", "region",
    "purchase_date", "amount", "remarks", "description",
    "historical_period", "creator", "cultural_significance",
    "image_url", "video_url", "model_3d_url", "museum_name",
    "exhibition_name"
}


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def update_database():
    """Create tables and add fields introduced after the initial schema."""
    db.create_all()

    table_name = MuseumRecord.__tablename__
    existing_columns = {
        column["name"] for column in inspect(db.engine).get_columns(table_name)
    }
    new_columns = {
        "description": "TEXT",
        "historical_period": "VARCHAR(100)",
        "creator": "VARCHAR(200)",
        "cultural_significance": "TEXT",
        "image_url": "VARCHAR(500)",
        "video_url": "VARCHAR(500)",
        "model_3d_url": "VARCHAR(500)",
        "museum_name": "VARCHAR(200)",
        "exhibition_name": "VARCHAR(200)",
    }

    # The table/column names and SQL types here are fixed by this application.
    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            db.session.execute(
                text(
                    f'ALTER TABLE "{table_name}" '
                    f'ADD COLUMN "{column_name}" {column_type}'
                )
            )
    db.session.commit()


def create_admin_from_environment():
    """Create the first admin only when credentials are explicitly configured."""
    username = os.environ.get("ADMIN_USERNAME", "admin").strip()
    password = os.environ.get("ADMIN_PASSWORD", "admin123")

    if not username or not password:
        return

    if not User.query.filter_by(username=username).first():
        admin = User(
            username=username,
            password=generate_password_hash(password)
        )
        db.session.add(admin)
        db.session.commit()


@app.route("/")
def index():
    featured_artifacts = MuseumRecord.query.order_by(
        MuseumRecord.id.desc()
    ).limit(6).all()
    return render_template(
        "index.html",
        featured_artifacts=featured_artifacts,
        records=featured_artifacts
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "admin").strip()
        password = request.form.get("password", "admin123")
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get("next", "")
            # Only allow local application paths as post-login redirects.
            if next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    records = MuseumRecord.query.order_by(MuseumRecord.id.desc()).all()
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()

    total_artifacts = MuseumRecord.query.count()
    total_categories = db.session.query(MuseumRecord.category).filter(
        MuseumRecord.category.isnot(None),
        MuseumRecord.category != ""
    ).distinct().count()
    total_regions = db.session.query(MuseumRecord.region).filter(
        MuseumRecord.region.isnot(None),
        MuseumRecord.region != ""
    ).distinct().count()

    return render_template(
        "dashboard.html",
        records=records,
        logs=logs,
        total_artifacts=total_artifacts,
        total_categories=total_categories,
        total_regions=total_regions
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_record():
    if request.method == "POST":
        data = {
            key: value.strip()
            for key, value in request.form.items()
            if key in ALLOWED_FIELDS
        }
        record = MuseumRecord(**data)
        db.session.add(record)
        db.session.flush()

        db.session.add(AuditLog(
            action="Created",
            user=current_user.username,
            record_id=record.id
        ))
        db.session.commit()
        flash("Artifact added successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add.html", record=None, page_heading="Add Artifact")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_record(id):
    record = MuseumRecord.query.get_or_404(id)

    if request.method == "POST":
        for key, value in request.form.items():
            if key in ALLOWED_FIELDS:
                setattr(record, key, value.strip())

        db.session.add(AuditLog(
            action="Edited",
            user=current_user.username,
            record_id=record.id
        ))
        db.session.commit()
        flash("Artifact updated successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add.html", record=record, page_heading="Edit Artifact")


@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_record(id):
    record = MuseumRecord.query.get_or_404(id)
    record_id = record.id

    db.session.add(AuditLog(
        action="Deleted",
        user=current_user.username,
        record_id=record_id
    ))
    db.session.delete(record)
    db.session.commit()

    flash("Artifact deleted successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/artifact/<int:id>")
def artifact_detail(id):
    record = MuseumRecord.query.get_or_404(id)
    return render_template("artifact_detail.html", record=record)


@app.route("/artifacts")
def artifacts():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    region = request.args.get("region", "").strip()
    material = request.args.get("material", "").strip()
    historical_period = request.args.get("historical_period", "").strip()

    records_query = MuseumRecord.query

    if query:
        search_term = f"%{query}%"
        records_query = records_query.filter(or_(
            MuseumRecord.object_name.ilike(search_term),
            MuseumRecord.category.ilike(search_term),
            MuseumRecord.material.ilike(search_term),
            MuseumRecord.region.ilike(search_term),
            MuseumRecord.historical_period.ilike(search_term),
            MuseumRecord.creator.ilike(search_term),
            MuseumRecord.museum_name.ilike(search_term)
        ))

    if category:
        records_query = records_query.filter(MuseumRecord.category == category)
    if region:
        records_query = records_query.filter(MuseumRecord.region == region)
    if material:
        records_query = records_query.filter(MuseumRecord.material == material)
    if historical_period:
        records_query = records_query.filter(
            MuseumRecord.historical_period == historical_period
        )

    records = records_query.order_by(MuseumRecord.id.desc()).all()

    def distinct_values(column):
        return [
            row[0] for row in db.session.query(column)
            .filter(column.isnot(None), column != "")
            .distinct().order_by(column).all()
        ]

    return render_template(
        "artifacts.html",
        records=records,
        categories=distinct_values(MuseumRecord.category),
        regions=distinct_values(MuseumRecord.region),
        materials=distinct_values(MuseumRecord.material),
        historical_periods=distinct_values(MuseumRecord.historical_period),
        query=query,
        selected_category=category,
        selected_region=region,
        selected_material=material,
        selected_historical_period=historical_period
    )


@app.route("/export_excel")
@login_required
def export_excel():
    records = MuseumRecord.query.order_by(MuseumRecord.id.asc()).all()
    data = [
        {
            column.name: getattr(record, column.name)
            for column in MuseumRecord.__table__.columns
        }
        for record in records
    ]
    output = io.BytesIO()
    pd.DataFrame(data).to_excel(output, index=False)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="museum_artifacts.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/export_pdf")
@login_required
def export_pdf():
    output = io.BytesIO()
    doc = SimpleDocTemplate(output)
    elements = []
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]

    elements.append(Paragraph("Digital Museum Artifact Collection", styles["Title"]))
    elements.append(Spacer(1, 20))

    records = MuseumRecord.query.order_by(MuseumRecord.id.asc()).all()
    if not records:
        elements.append(Paragraph("No artifacts have been added yet.", normal_style))

    for record in records:
        object_name = escape(record.object_name or "Untitled Artifact")
        region = escape(record.region or "Unknown Region")
        category = escape(record.category or "Uncategorized")

        elements.append(Paragraph(f"<b>{object_name}</b>", normal_style))
        elements.append(Paragraph(f"Category: {category}", normal_style))
        elements.append(Paragraph(f"Region: {region}", normal_style))

        if record.historical_period:
            period = escape(record.historical_period)
            elements.append(Paragraph(f"Historical Period: {period}", normal_style))

        elements.append(Spacer(1, 12))

    doc.build(elements)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="museum_artifacts.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    with app.app_context():
        update_database()
        create_admin_from_environment()

    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
