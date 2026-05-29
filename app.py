from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'hospital_secret_key_2024'

FEES = {
    'General': 300,
    'Cardiologist': 800,
    'Dermatologist': 500,
    'Orthopedic': 600,
    'Neurologist': 900,
    'Pediatrician': 400
}

DOCTOR_INFO = {
    'General': {'icon': '🩺', 'desc': 'General Health Checkup'},
    'Cardiologist': {'icon': '❤️', 'desc': 'Heart & Cardiovascular'},
    'Dermatologist': {'icon': '🧴', 'desc': 'Skin & Hair Care'},
    'Orthopedic': {'icon': '🦴', 'desc': 'Bones & Joints'},
    'Neurologist': {'icon': '🧠', 'desc': 'Brain & Nervous System'},
    'Pediatrician': {'icon': '👶', 'desc': 'Child Health Care'}
}

def get_db():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            phone TEXT,
            email TEXT,
            doctor TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            patients INTEGER DEFAULT 1,
            total INTEGER NOT NULL,
            status TEXT DEFAULT 'Confirmed',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as count FROM appointments")
    total_appointments = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) as count FROM appointments WHERE date = ?", (datetime.today().strftime('%Y-%m-%d'),))
    today_appointments = cur.fetchone()['count']
    cur.execute("SELECT SUM(total) as revenue FROM appointments")
    revenue = cur.fetchone()['revenue'] or 0
    conn.close()
    return render_template('index.html',
        fees=FEES,
        doctor_info=DOCTOR_INFO,
        total_appointments=total_appointments,
        today_appointments=today_appointments,
        revenue=revenue
    )

@app.route('/book', methods=['POST'])
def book():
    name = request.form.get('name', '').strip()
    age = request.form.get('age', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    doctor = request.form.get('doctor', '').strip()
    date = request.form.get('date', '').strip()
    time = request.form.get('time', '').strip()
    patients = request.form.get('patients', '1').strip()
    notes = request.form.get('notes', '').strip()

    if not all([name, doctor, date, time, patients]):
        flash('⚠️ Please fill all required fields.', 'error')
        return redirect(url_for('home'))

    try:
        patients = int(patients)
        if patients < 1 or patients > 10:
            raise ValueError
    except ValueError:
        flash('⚠️ Invalid patient count (1–10 allowed).', 'error')
        return redirect(url_for('home'))

    # Validate date is not in the past
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
        if selected_date < datetime.today().date():
            flash('⚠️ Cannot book appointments for past dates.', 'error')
            return redirect(url_for('home'))
    except ValueError:
        flash('⚠️ Invalid date format.', 'error')
        return redirect(url_for('home'))

    total = FEES.get(doctor, 0) * patients

    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT * FROM appointments 
        WHERE doctor=? AND date=? AND time=? AND status != 'Cancelled'
    ''', (doctor, date, time))

    if cur.fetchone():
        conn.close()
        flash(f'⚠️ The {time} slot with {doctor} on {date} is already booked. Please choose another time.', 'error')
        return redirect(url_for('home'))

    cur.execute('''
        INSERT INTO appointments 
        (name, age, phone, email, doctor, date, time, patients, total, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, age or None, phone or None, email or None, doctor, date, time, patients, total, notes or None))
    conn.commit()
    appointment_id = cur.lastrowid
    conn.close()

    flash(f'✅ Appointment #{appointment_id} confirmed for {name} with {doctor} on {date} at {time}. Total: ₹{total}', 'success')
    return redirect(url_for('home'))

@app.route('/appointments')
def appointments():
    search = request.args.get('search', '').strip()
    doctor_filter = request.args.get('doctor', '').strip()
    status_filter = request.args.get('status', '').strip()

    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM appointments WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR phone LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])
    if doctor_filter:
        query += " AND doctor = ?"
        params.append(doctor_filter)
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY date DESC, time DESC"
    cur.execute(query, params)
    data = cur.fetchall()
    conn.close()

    return render_template('appointments.html',
        data=data,
        fees=FEES,
        doctor_info=DOCTOR_INFO,
        search=search,
        doctor_filter=doctor_filter,
        status_filter=status_filter
    )

@app.route('/cancel/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE appointments SET status='Cancelled' WHERE id=?", (appointment_id,))
    conn.commit()
    conn.close()
    flash(f'Appointment #{appointment_id} has been cancelled.', 'info')
    return redirect(url_for('appointments'))

@app.route('/api/check-slot')
def check_slot():
    doctor = request.args.get('doctor')
    date = request.args.get('date')
    time = request.args.get('time')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM appointments WHERE doctor=? AND date=? AND time=? AND status != 'Cancelled'", (doctor, date, time))
    exists = cur.fetchone() is not None
    conn.close()
    return jsonify({'available': not exists})

if __name__ == '__main__':
    app.run(debug=True)