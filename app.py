import os
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "submissions.db")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

OWNER_PASSWORD = os.environ.get("OWNER_PASSWORD")
if not OWNER_PASSWORD:
    raise RuntimeError(
        "OWNER_PASSWORD is not set. Set it before starting the application."
    )

COOKIE_NAME = "grandfather_submission_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 10  # 10 years
NAME_MAX_LENGTH = 120


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grandfather_name TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                browser_token_hash TEXT NOT NULL UNIQUE
            )
            """
        )
        db.commit()


def hash_token(token):
    # A random token is stored in the browser; only its SHA-256 hash is stored in SQLite.
    import hashlib
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def owner_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("owner_authenticated"):
            return redirect(url_for("owner_login"))
        return view(*args, **kwargs)

    return wrapped


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = " ".join(request.form.get("grandfather_name", "").split())

        if not name:
            flash("Please enter your grandfather's name.", "error")
            return render_template("index.html"), 400

        if len(name) > NAME_MAX_LENGTH:
            flash(f"Please keep the name under {NAME_MAX_LENGTH} characters.", "error")
            return render_template("index.html"), 400

        token = request.cookies.get(COOKIE_NAME)
        if not token:
            token = secrets.token_urlsafe(32)

        token_hash = hash_token(token)

        try:
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO submissions
                    (grandfather_name, submitted_at, browser_token_hash)
                    VALUES (?, ?, ?)
                    """,
                    (
                        name,
                        datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        token_hash,
                    ),
                )
                db.commit()
        except sqlite3.IntegrityError:
            flash("This browser has already submitted a name.", "error")
            response = render_template("index.html")
            response = app.make_response(response)
            response.set_cookie(
                COOKIE_NAME,
                token,
                max_age=COOKIE_MAX_AGE,
                httponly=True,
                samesite="Lax",
                secure=False,  # Set True when deployed over HTTPS.
            )
            return response, 409

        response = app.make_response(render_template("success.html"))
        response.set_cookie(
            COOKIE_NAME,
            token,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
            secure=False,  # Set True when deployed over HTTPS.
        )
        return response

    return render_template("index.html")


@app.route("/owner/login", methods=["GET", "POST"])
def owner_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if secrets.compare_digest(password, OWNER_PASSWORD):
            session.clear()
            session["owner_authenticated"] = True
            return redirect(url_for("owner_dashboard"))

        flash("Incorrect password.", "error")

    return render_template("login.html")


@app.route("/owner")
@owner_required
def owner_dashboard():
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]
        submissions = db.execute(
            """
            SELECT id, grandfather_name, submitted_at
            FROM submissions
            ORDER BY id DESC
            """
        ).fetchall()

    return render_template(
        "owner.html",
        total=total,
        submissions=submissions,
    )


@app.post("/owner/logout")
@owner_required
def owner_logout():
    session.clear()
    return redirect(url_for("owner_login"))


init_db()

if __name__ == "__main__":
    # Development/local use only. For production, use a proper WSGI server.
    app.run(host="127.0.0.1", port=5000, debug=False)
