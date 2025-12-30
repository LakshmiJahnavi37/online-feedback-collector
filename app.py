from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
from datetime import datetime
import csv

app = Flask(__name__)
app.secret_key = 'secret-key'

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- INIT DB ----------------
def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            rating INTEGER,
            comments TEXT,
            date_submitted TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- USER ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    name = request.form['name']
    email = request.form['email']
    rating = request.form['rating']
    comments = request.form['comments']
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO Feedback (name,email,rating,comments,date_submitted) VALUES (?,?,?,?,?)",
        (name, email, rating, comments, date)
    )
    conn.commit()
    conn.close()

    return redirect('/thankyou')

@app.route('/thankyou')
def thankyou():
    return render_template('thank_you.html')


@app.route('/end')
def end():
    return render_template('end.html')

# ---------------- ADMIN LOGIN ----------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():

    ADMIN_ACCOUNTS = {
        "admin@gmail.com": "admin123",
        "hod@gmail.com": "hod123",
        "faculty@gmail.com": "faculty123"
    }

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email in ADMIN_ACCOUNTS and password == ADMIN_ACCOUNTS[email]:
            session['admin_email'] = email
            return redirect('/admin-dashboard')
        else:
            return render_template(
                'admin_login.html',
                error="Invalid credentials"
            )

    return render_template('admin_login.html')

 
# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin-dashboard')
def admin_dashboard():
    if 'admin_email' not in session:
        return redirect('/admin-login')

    conn = get_db_connection()
    feedbacks = conn.execute("SELECT * FROM Feedback").fetchall()

    ratings = conn.execute("""
        SELECT rating, COUNT(*) AS count
        FROM Feedback
        GROUP BY rating
        ORDER BY rating
    """).fetchall()

    conn.close()

    total = len(feedbacks)
    avg = round(sum(int(f['rating']) for f in feedbacks)/total,2) if total else 0

    return render_template(
        'admin.html',
        feedbacks=feedbacks,
        total=total,
        avg_rating=avg,
        ratings=ratings
    )

# ---------------- ADMIN ACTIONS ----------------
@app.route('/export-csv')
def export_csv():
    if 'admin_email' not in session:
        return redirect('/admin-login')

    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM Feedback").fetchall()
    conn.close()

    with open('feedback.csv','w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID','Name','Email','Rating','Comments','Date'])
        for r in rows:
            writer.writerow(r)

    return send_file('feedback.csv', as_attachment=True)

@app.route('/clear-data', methods=['POST'])
def clear_data():
    if 'admin_email' not in session:
        return redirect('/admin-login')

    conn = get_db_connection()
    conn.execute("DELETE FROM Feedback")
    conn.commit()
    conn.close()
    return redirect('/admin-dashboard')

# ---------------- LOGOUT FLOW ----------------
@app.route('/confirm-logout')
def confirm_logout():
    if 'admin_email' not in session:
        return redirect('/')
    return render_template('confirm_logout.html')

@app.route('/logout')
def logout():
    session.pop('admin_email', None)
    return redirect('/')

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
