from dotenv import load_dotenv

load_dotenv()
import csv
import io
import os
import secrets
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask, abort, flash, redirect, render_template,
    request, session, url_for, send_file
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-development-secret-key"
)

ADMIN_EMAIL = os.environ.get(
    "ADMIN_EMAIL", "lakshmi@gmail.com"
).strip().lower()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

# ---------------- DATABASE ----------------

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                rating INTEGER NOT NULL
                    CHECK (rating BETWEEN 1 AND 5),
                comments TEXT,
                date_submitted TEXT NOT NULL
            )
        """)
        conn.commit()


# ---------------- CSRF PROTECTION ----------------

def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


def verify_csrf():
    submitted = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")

    if not expected or not secrets.compare_digest(
        submitted, expected
    ):
        abort(400, description="Invalid or expired form token.")


# ---------------- ADMIN AUTHENTICATION ----------------

def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if not session.get("admin_logged_in"):
            flash(
                "Please sign in to access the admin dashboard.",
                "warning"
            )
            return redirect(url_for("admin_login"))

        return view(*args, **kwargs)

    return wrapped_view


# ---------------- HOME PAGE ----------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------- SUBMIT FEEDBACK ----------------

@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():

    verify_csrf()

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    comments = request.form.get("comments", "").strip()

    try:
        rating = int(request.form.get("rating", ""))
    except ValueError:
        rating = 0

    if not name or not email or rating not in range(1, 6):
        flash(
            "Please enter your name, email and a rating.",
            "error"
        )
        return redirect(url_for("index"))

    if (
        len(name) > 100
        or len(email) > 254
        or len(comments) > 2000
    ):
        flash("Please check the length of your inputs.", "error")
        return redirect(url_for("index"))

    with get_db_connection() as conn:

        conn.execute("""
            INSERT INTO Feedback
            (name, email, rating, comments, date_submitted)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            email,
            rating,
            comments,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()

    return redirect(url_for("thank_you"))


# ---------------- THANK YOU PAGE ----------------

@app.route("/thankyou")
def thank_you():
    return render_template("thank_you.html")


# ---------------- END PAGE ----------------

@app.route("/end")
def end():
    return render_template("end.html")


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":

        verify_csrf()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get("password", "")

        if (
            secrets.compare_digest(email, ADMIN_EMAIL)
            and secrets.compare_digest(password, ADMIN_PASSWORD)
        ):

            session.clear()
            session["admin_logged_in"] = True
            session["admin_email"] = email

            flash("Successfully logged in!", "success")

            return redirect(url_for("admin_dashboard"))

        flash("Incorrect email or password.", "error")

    return render_template("admin_login.html")


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():

    with get_db_connection() as conn:

        feedback = conn.execute(
            "SELECT * FROM Feedback ORDER BY id DESC"
        ).fetchall()

        total = conn.execute(
            "SELECT COUNT(*) FROM Feedback"
        ).fetchone()[0]

        average = conn.execute(
            "SELECT AVG(rating) FROM Feedback"
        ).fetchone()[0] or 0

        rating_rows = conn.execute("""
            SELECT rating, COUNT(*) AS count
            FROM Feedback
            GROUP BY rating
        """).fetchall()

    rating_counts = {
        str(i): 0 for i in range(1, 6)
    }

    for row in rating_rows:
        rating_counts[str(row["rating"])] = row["count"]

    return render_template(
        "admin.html",
        feedback=feedback,
        total=total,
        average=round(average, 2),
        rating_counts=rating_counts
    )


# ---------------- EXPORT CSV ----------------

@app.route("/export-csv")
@admin_required
def export_csv():

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Name",
        "Email",
        "Rating",
        "Comments",
        "Date Submitted"
    ])

    with get_db_connection() as conn:

        rows = conn.execute("""
            SELECT id, name, email, rating,
                   comments, date_submitted
            FROM Feedback
            ORDER BY id DESC
        """).fetchall()

    for row in rows:
        writer.writerow([
            row["id"],
            row["name"],
            row["email"],
            row["rating"],
            row["comments"],
            row["date_submitted"]
        ])

    memory_file = io.BytesIO(
        output.getvalue().encode("utf-8-sig")
    )

    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype="text/csv",
        as_attachment=True,
        download_name="feedback.csv"
    )


# ---------------- CLEAR ALL FEEDBACK ----------------

@app.route("/clear-data", methods=["POST"])
@admin_required
def clear_data():

    verify_csrf()

    with get_db_connection() as conn:
        conn.execute("DELETE FROM Feedback")
        conn.commit()

    flash("All feedback records have been deleted.", "success")

    return redirect(url_for("admin_dashboard"))


# ---------------- CONFIRM LOGOUT ----------------

@app.route("/confirm-logout")
@admin_required
def confirm_logout():
    return render_template("confirm_logout.html")


# ---------------- LOGOUT ----------------

@app.route("/logout", methods=["POST"])
@admin_required
def logout():

    verify_csrf()

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("admin_login"))


# ---------------- ERROR HANDLER ----------------

@app.errorhandler(400)
def bad_request(error):

    return render_template(
        "end.html",
        error_message=getattr(
            error, "description", "Bad request."
        )
    ), 400


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":

    init_db()

    app.run(
        debug=os.environ.get(
            "FLASK_DEBUG", "false"
        ).lower() == "true"
    )
