"""
app.py — CleanTrack AI Main Application
---------------------------------------
Flask backend for the CleanTrack AI sanitation monitoring platform.
Place this file at: CleanTrackAI/app.py
Run with:
    python app.py
Then open your browser at: http://127.0.0.1:5000
"""
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, send_from_directory
)
from flask_cors import CORS
from werkzeug.utils import secure_filename
# ─── Add ai/ to Python path ─────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ai"))
from garbage_detection import detect_garbage
# ─── App Configuration ───────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.secret_key = "cleantrack_ai_secret_key_2024"
BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
DATABASE = BASE_DIR / "database.db"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
# ─── Helper Functions ────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    """Check if uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DATABASE))
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    """Initialize the SQLite database and create tables."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            image       TEXT NOT NULL,
            latitude    REAL,
            longitude   REAL,
            description TEXT,
            status      TEXT DEFAULT 'Pending',
            date        TEXT NOT NULL,
            ai_result   TEXT DEFAULT 'Pending',
            ai_confidence REAL DEFAULT 0.0,
            resolution_image TEXT,
            location_name TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")
def auto_escalate():
    """
    Escalation Logic:
    Automatically mark complaints as 'Escalated' if they have been
    in 'Pending' or 'In Progress' status for more than 10 days.
    """
    conn = get_db()
    cursor = conn.cursor()
    threshold_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE complaints
        SET status = 'Escalated'
        WHERE status IN ('Pending', 'In Progress')
          AND date <= ?
    """, (threshold_date,))
    escalated_count = cursor.rowcount
    conn.commit()
    conn.close()
    if escalated_count > 0:
        print(f"[ESCALATION] {escalated_count} complaint(s) escalated automatically.")
    return escalated_count
# ─── Routes ──────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """Home / Landing page."""
    auto_escalate()
    return render_template("index.html")
# ── Citizen Portal ────────────────────────────────────────────────────────────
@app.route("/citizen", methods=["GET", "POST"])
def citizen():
    """
    Citizen complaint submission portal.
    GET  → Show submission form
    POST → Process complaint with AI verification
    """
    if request.method == "GET":
        return render_template("citizen.html")
    # ── Handle POST: Submit Complaint ──
    if "image" not in request.files:
        flash("No image file provided.", "error")
        return redirect(request.url)
    file = request.files["image"]
    if file.filename == "":
        flash("No image selected.", "error")
        return redirect(request.url)
    if not allowed_file(file.filename):
        flash("Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP.", "error")
        return redirect(request.url)
    # Save the uploaded image
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
    filename = timestamp + filename
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    # Extract form data
    latitude = request.form.get("latitude", None)
    longitude = request.form.get("longitude", None)
    description = request.form.get("description", "").strip()
    location_name = request.form.get("location_name", "").strip()
    try:
        latitude = float(latitude) if latitude else None
        longitude = float(longitude) if longitude else None
    except ValueError:
        latitude = None
        longitude = None
    # ── Run AI Detection ──
    ai_result = detect_garbage(filepath)
    ai_label = ai_result.get("label", "Detection Failed")
    ai_confidence = ai_result.get("confidence", 0.0)
    # Save complaint to database
    complaint_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO complaints
            (image, latitude, longitude, description, status, date,
             ai_result, ai_confidence, location_name)
        VALUES (?, ?, ?, ?, 'Pending', ?, ?, ?, ?)
    """, (
        filename, latitude, longitude, description,
        complaint_date, ai_label, ai_confidence, location_name
    ))
    complaint_id = cursor.lastrowid
    conn.commit()
    conn.close()
    flash(
        f"✅ Complaint #{complaint_id} submitted! "
        f"AI Analysis: <strong>{ai_label}</strong> "
        f"(Confidence: {round(ai_confidence * 100, 1)}%)",
        "success"
    )
    return redirect(url_for("track_complaint", complaint_id=complaint_id))
@app.route("/track/<int:complaint_id>")
def track_complaint(complaint_id: int):
    """Track the status of a specific complaint."""
    auto_escalate()
    conn = get_db()
    complaint = conn.execute(
        "SELECT * FROM complaints WHERE id = ?", (complaint_id,)
    ).fetchone()
    conn.close()
    if not complaint:
        flash(f"Complaint #{complaint_id} not found.", "error")
        return redirect(url_for("citizen"))
    return render_template("track.html", complaint=complaint)
@app.route("/api/complaints/search")
def search_complaint():
    """API to search complaint by ID (for citizen tracking)."""
    complaint_id = request.args.get("id", "").strip()
    if not complaint_id.isdigit():
        return jsonify({"error": "Invalid complaint ID"}), 400
    auto_escalate()
    conn = get_db()
    complaint = conn.execute(
        "SELECT * FROM complaints WHERE id = ?", (int(complaint_id),)
    ).fetchone()
    conn.close()
    if not complaint:
        return jsonify({"error": "Complaint not found"}), 404
    return jsonify(dict(complaint))
# ── Authority Dashboard ───────────────────────────────────────────────────────
@app.route("/authority")
def authority():
    """Authority dashboard showing all complaints."""
    auto_escalate()
    status_filter = request.args.get("status", "all")
    conn = get_db()
    if status_filter == "all":
        complaints = conn.execute(
            "SELECT * FROM complaints ORDER BY date DESC"
        ).fetchall()
    else:
        complaints = conn.execute(
            "SELECT * FROM complaints WHERE status = ? ORDER BY date DESC",
            (status_filter,)
        ).fetchall()
    conn.close()
    return render_template(
        "authority.html",
        complaints=complaints,
        current_filter=status_filter
    )
@app.route("/authority/update/<int:complaint_id>", methods=["POST"])
def update_complaint(complaint_id: int):
    """Update complaint status by authority."""
    new_status = request.form.get("status")
    valid_statuses = ["Pending", "In Progress", "Resolved", "Escalated"]
    if new_status not in valid_statuses:
        flash("Invalid status value.", "error")
        return redirect(url_for("authority"))
    # Handle resolution proof image upload
    resolution_image = None
    if "resolution_image" in request.files:
        res_file = request.files["resolution_image"]
        if res_file and res_file.filename and allowed_file(res_file.filename):
            res_filename = secure_filename(res_file.filename)
            res_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_resolved_")
            res_filename = res_timestamp + res_filename
            res_filepath = os.path.join(app.config["UPLOAD_FOLDER"], res_filename)
            res_file.save(res_filepath)
            resolution_image = res_filename
    conn = get_db()
    if resolution_image:
        conn.execute("""
            UPDATE complaints
            SET status = ?, resolution_image = ?
            WHERE id = ?
        """, (new_status, resolution_image, complaint_id))
    else:
        conn.execute(
            "UPDATE complaints SET status = ? WHERE id = ?",
            (new_status, complaint_id)
        )
    conn.commit()
    conn.close()
    flash(
        f"✅ Complaint #{complaint_id} status updated to '{new_status}'.",
        "success"
    )
    return redirect(url_for("authority"))
# ── Admin Dashboard ───────────────────────────────────────────────────────────
@app.route("/admin")
def admin():
    """Admin dashboard with full overview and analytics."""
    auto_escalate()
    conn = get_db()
    # All complaints
    complaints = conn.execute(
        "SELECT * FROM complaints ORDER BY date DESC"
    ).fetchall()
    # Statistics
    total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Pending'"
    ).fetchone()[0]
    in_progress = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'"
    ).fetchone()[0]
    resolved = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'"
    ).fetchone()[0]
    escalated = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Escalated'"
    ).fetchone()[0]
    # AI detection breakdown
    garbage_detected = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE ai_result = 'Garbage Detected'"
    ).fetchone()[0]
    no_garbage = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE ai_result = 'No Garbage Detected'"
    ).fetchone()[0]
    # Last 7 days submissions
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    recent_submissions = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE date >= ?", (week_ago,)
    ).fetchone()[0]
    conn.close()
    stats = {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "escalated": escalated,
        "garbage_detected": garbage_detected,
        "no_garbage": no_garbage,
        "recent_submissions": recent_submissions,
        "resolution_rate": (
            round((resolved / total) * 100, 1) if total > 0 else 0
        )
    }
    return render_template("admin.html", complaints=complaints, stats=stats)
@app.route("/admin/delete/<int:complaint_id>", methods=["POST"])
def delete_complaint(complaint_id: int):
    """Admin: Delete a complaint."""
    conn = get_db()
    complaint = conn.execute(
        "SELECT image, resolution_image FROM complaints WHERE id = ?",
        (complaint_id,)
    ).fetchone()
    if complaint:
        # Delete associated image files
        for img_field in ["image", "resolution_image"]:
            img = complaint[img_field]
            if img:
                img_path = UPLOAD_FOLDER / img
                if img_path.exists():
                    img_path.unlink()
        conn.execute("DELETE FROM complaints WHERE id = ?", (complaint_id,))
        conn.commit()
        flash(f"🗑️ Complaint #{complaint_id} deleted.", "info")
    else:
        flash(f"Complaint #{complaint_id} not found.", "error")
    conn.close()
    return redirect(url_for("admin"))
# ── Static Uploads ────────────────────────────────────────────────────────────
@app.route("/uploads/<filename>")
def uploaded_file(filename: str):
    """Serve uploaded images."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
# ── API Endpoints ─────────────────────────────────────────────────────────────
@app.route("/api/stats")
def api_stats():
    """JSON API for dashboard statistics (for charts)."""
    auto_escalate()
    conn = get_db()
    stats = {
        "total": conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0],
        "pending": conn.execute(
            "SELECT COUNT(*) FROM complaints WHERE status='Pending'"
        ).fetchone()[0],
        "in_progress": conn.execute(
            "SELECT COUNT(*) FROM complaints WHERE status='In Progress'"
        ).fetchone()[0],
        "resolved": conn.execute(
            "SELECT COUNT(*) FROM complaints WHERE status='Resolved'"
        ).fetchone()[0],
        "escalated": conn.execute(
            "SELECT COUNT(*) FROM complaints WHERE status='Escalated'"
        ).fetchone()[0],
    }
    # Daily trend (last 14 days)
    daily_trend = []
    for i in range(13, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        count = conn.execute(
            "SELECT COUNT(*) FROM complaints WHERE date LIKE ?", (f"{day}%",)
        ).fetchone()[0]
        daily_trend.append({"date": day, "count": count})
    conn.close()
    stats["daily_trend"] = daily_trend
    return jsonify(stats)
# ─── App Entry Point ─────────────────────────────────────────────────────────
@app.route("/api/report", methods=["POST"])
def report_issue():
    data = request.json

    title = data.get("title")
    issue_type = data.get("type")
    description = data.get("description")
    location = data.get("location")

    print("New Complaint")
    print(title)
    print(issue_type)
    print(description)
    print(location)

    return jsonify({
        "success": True,
        "message": "Complaint received successfully"
    })

if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 55)
    print("  🌿 CleanTrack AI — Sanitation Monitoring Platform")
    print("=" * 55)
    print("  Server running at: http://127.0.0.1:5000")
    print("  Press CTRL+C to stop")
    print("=" * 55 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
