import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_socketio import SocketIO, emit, join_room
import pymysql
import pdfkit
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'nasa_home_secret_key'
socketio = SocketIO(app)

# Database connection details
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'alu potol'
DB_NAME = 'nasa_home'


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'Student':
            return redirect(url_for('student_dashboard'))
        elif session['role'] == 'Teacher':
            return redirect(url_for('teacher_dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM Users WHERE email = %s AND password = %s', (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        return redirect(url_for('index'))
    else:
        flash('Invalid credentials')
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if role not in ['Student', 'Teacher']:
            flash('Invalid role selected')
            return redirect(url_for('register'))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email exists
        cursor.execute('SELECT * FROM Users WHERE email = %s', (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash('Email already exists!')
            return redirect(url_for('register'))

        # Insert user
        cursor.execute(
            'INSERT INTO Users (full_name, email, password, role) VALUES (%s, %s, %s, %s)',
            (full_name, email, password, role)
        )
        conn.commit()
        conn.close()

        flash('Registration successful! Please login.')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    return render_template('admin/dashboard.html')


@app.route('/student')
def student_dashboard():
    if session.get('role') != 'Student':
        return redirect(url_for('index'))
    return render_template('student/dashboard.html')


@app.route('/teacher')
def teacher_dashboard():
    if session.get('role') != 'Teacher':
        return redirect(url_for('index'))
    return render_template('teacher/dashboard.html')

# Placeholder for modular routes like /admin/rooms, /student/meals, etc.


if __name__ == '__main__':
    socketio.run(app, debug=True)
