import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify
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
DB_PASSWORD = 'alu potol'  # XAMPP default is empty
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

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM Users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        conn.close()
    except pymysql.err.OperationalError as e:
        flash(f'Database connection error: {str(e)}')
        return redirect(url_for('index'))

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

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM Users WHERE role='Student'")
    students_count = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM Users WHERE role='Teacher'")
    teachers_count = cursor.fetchone()['count']
    cursor.execute(
        "SELECT COUNT(*) as count FROM Complaints WHERE status='Pending'")
    complaints_count = cursor.fetchone()['count']
    cursor.execute(
        "SELECT COUNT(*) as count FROM Maintenance_Requests WHERE status='Pending'")
    maintenance_count = cursor.fetchone()['count']
    conn.close()

    return render_template('admin/dashboard.html',
                           students_count=students_count,
                           teachers_count=teachers_count,
                           complaints_count=complaints_count,
                           maintenance_count=maintenance_count)

# --- ADMIN ROOM MANAGEMENT ---


@app.route('/admin/rooms', methods=['GET', 'POST'])
def admin_rooms():
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        room_number = request.form['room_number']
        capacity = request.form['capacity']
        teacher_id = request.form.get('teacher_id')
        if not teacher_id:
            teacher_id = None

        try:
            cursor.execute('INSERT INTO Rooms (room_number, capacity, teacher_id) VALUES (%s, %s, %s)',
                           (room_number, capacity, teacher_id))
            conn.commit()
            flash('Room added successfully!')
        except Exception as e:
            flash(f'Error: {e}')
        return redirect(url_for('admin_rooms'))

    cursor.execute('''SELECT r.*, u.full_name as teacher_name 
                      FROM Rooms r LEFT JOIN Users u ON r.teacher_id = u.id''')
    rooms = cursor.fetchall()

    cursor.execute("SELECT id, full_name FROM Users WHERE role='Teacher'")
    teachers = cursor.fetchall()

    # fetch current room assignments to display space
    cursor.execute(
        "SELECT room_id, COUNT(*) as current_occupancy FROM Room_Assignments GROUP BY room_id")
    occupancy = {str(row['room_id']): row['current_occupancy']
                 for row in cursor.fetchall()}

    conn.close()
    return render_template('admin/rooms.html', rooms=rooms, teachers=teachers, occupancy=occupancy)


@app.route('/admin/rooms/delete/<int:id>')
def delete_room(id):
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Rooms WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    flash('Room deleted successfully!')
    return redirect(url_for('admin_rooms'))

# --- ADMIN FOOD MANAGEMENT ---


@app.route('/admin/food', methods=['GET', 'POST'])
def admin_food():
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        try:
            cursor.execute('INSERT INTO Food_Items (name, category, price) VALUES (%s, %s, %s)',
                           (name, category, price))
            conn.commit()
            flash('Food item added successfully!')
        except Exception as e:
            flash(f'Error: {e}')
        return redirect(url_for('admin_food'))

    cursor.execute('SELECT * FROM Food_Items')
    foods = cursor.fetchall()
    conn.close()
    return render_template('admin/food.html', foods=foods)


@app.route('/admin/food/delete/<int:id>')
def delete_food(id):
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Food_Items WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    flash('Food item deleted successfully!')
    return redirect(url_for('admin_food'))


# --- ADMIN ASSIGNMENTS ---
@app.route('/admin/assignments', methods=['GET', 'POST'])
def admin_assignments():
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        student_id = request.form['student_id']
        room_id = request.form['room_id']

        # Check capacity
        cursor.execute("SELECT capacity FROM Rooms WHERE id=%s", (room_id,))
        capacity = cursor.fetchone()['capacity']

        cursor.execute(
            "SELECT COUNT(*) as count FROM Room_Assignments WHERE room_id=%s", (room_id,))
        count = cursor.fetchone()['count']

        if count >= capacity:
            flash("Error: Room is full!")
        else:
            # check if student already has a room
            cursor.execute(
                "SELECT * FROM Room_Assignments WHERE student_id=%s", (student_id,))
            if cursor.fetchone():
                flash("Error: Student already assigned to a room!")
            else:
                assigned_date = datetime.now().date()
                cursor.execute("INSERT INTO Room_Assignments (student_id, room_id, assigned_date) VALUES (%s, %s, %s)",
                               (student_id, room_id, assigned_date))
                conn.commit()
                flash("Student assigned successfully!")

        return redirect(url_for('admin_assignments'))

    # Fetch Unassigned Students
    cursor.execute('''SELECT id, full_name FROM Users 
                      WHERE role='Student' AND id NOT IN (SELECT student_id FROM Room_Assignments)''')
    unassigned_students = cursor.fetchall()

    # Fetch Rooms
    cursor.execute('SELECT id, room_number FROM Rooms')
    rooms_list = cursor.fetchall()

    # Fetch Current Assignments
    cursor.execute('''SELECT ra.id, u.full_name, r.room_number, ra.assigned_date 
                      FROM Room_Assignments ra
                      JOIN Users u ON ra.student_id = u.id
                      JOIN Rooms r ON ra.room_id = r.id''')
    assignments = cursor.fetchall()

    conn.close()
    return render_template('admin/assignments.html',
                           unassigned_students=unassigned_students,
                           rooms=rooms_list,
                           assignments=assignments)


@app.route('/admin/assignments/remove/<int:id>')
def remove_assignment(id):
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Room_Assignments WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    flash('Student removed from room successfully!')
    return redirect(url_for('admin_assignments'))

# --- ADMIN ORDERS, COMPLAINTS, MAINTENANCE ---


@app.route('/admin/orders')
def admin_orders():
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT o.id, u.full_name as student_name, o.total_amount, o.order_date, 
                      GROUP_CONCAT(CONCAT(f.name, " (", od.quantity, ")") SEPARATOR ", ") as items
                      FROM Orders o
                      JOIN Users u ON o.student_id = u.id
                      JOIN Order_Details od ON o.id = od.order_id
                      JOIN Food_Items f ON od.food_item_id = f.id
                      GROUP BY o.id
                      ORDER BY o.order_date DESC''')
    orders = cursor.fetchall()
    conn.close()
    return render_template('admin/orders.html', orders=orders)


@app.route('/admin/complaints')
def admin_complaints():
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT c.*, u.full_name, r.room_number 
                      FROM Complaints c
                      LEFT JOIN Users u ON c.student_id = u.id
                      LEFT JOIN Rooms r ON c.room_id = r.id
                      ORDER BY c.created_at DESC''')
    complaints = cursor.fetchall()
    conn.close()
    return render_template('admin/complaints.html', complaints=complaints)


@app.route('/admin/complaints/update/<int:id>')
def update_complaint(id):
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Complaints SET status='Reviewed' WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_complaints'))


@app.route('/admin/maintenance')
def admin_maintenance():
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT m.*, u.full_name, r.room_number 
                      FROM Maintenance_Requests m
                      JOIN Users u ON m.student_id = u.id
                      JOIN Rooms r ON m.room_id = r.id
                      ORDER BY m.created_at DESC''')
    requests = cursor.fetchall()
    conn.close()
    return render_template('admin/maintenance.html', requests=requests)


@app.route('/admin/maintenance/update/<int:id>/<status>')
def update_maintenance(id, status):
    if session.get('role') != 'Admin':
        return redirect(url_for('index'))
    if status not in ['Pending', 'In Progress', 'Resolved']:
        return redirect(url_for('admin_maintenance'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Maintenance_Requests SET status=%s WHERE id=%s", (status, id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_maintenance'))


@app.route('/student')
def student_dashboard():
    if session.get('role') != 'Student':
        return redirect(url_for('index'))

    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get room
    cursor.execute('''SELECT r.room_number FROM Room_Assignments ra 
                      JOIN Rooms r ON ra.room_id = r.id 
                      WHERE ra.student_id = %s''', (student_id,))
    room_data = cursor.fetchone()
    my_room = room_data['room_number'] if room_data else "Not Assigned"

    # Get pending dues
    cursor.execute(
        "SELECT SUM(amount) as pending_dues FROM Payments WHERE student_id=%s AND status='Pending'", (student_id,))
    dues_data = cursor.fetchone()
    pending_dues = float(dues_data['pending_dues']
                         ) if dues_data['pending_dues'] else 0.00

    # Get recent orders count
    cursor.execute(
        "SELECT COUNT(*) as order_count FROM Orders WHERE student_id=%s", (student_id,))
    order_data = cursor.fetchone()
    order_count = order_data['order_count']

    conn.close()

    return render_template('student/dashboard.html',
                           my_room=my_room,
                           pending_dues=pending_dues,
                           order_count=order_count)

# --- STUDENT FOOD ORDERING ---


@app.route('/student/order-food', methods=['GET', 'POST'])
def student_order_food():
    if session.get('role') != 'Student':
        return redirect(url_for('index'))
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        item_ids = request.form.getlist('items[]')

        if not item_ids:
            flash('No items selected!')
            return redirect(url_for('student_order_food'))

        total_amount = 0
        order_details = []

        # Calculate total and prepare details
        for item_id in item_ids:
            qty = int(request.form.get(f'qty_{item_id}', 1))
            if qty > 0:
                cursor.execute(
                    'SELECT price FROM Food_Items WHERE id=%s', (item_id,))
                price = cursor.fetchone()['price']
                total_amount += (float(price) * qty)
                order_details.append((item_id, qty, price))

        if total_amount > 0:
            # Create Order
            cursor.execute('INSERT INTO Orders (student_id, total_amount) VALUES (%s, %s)',
                           (student_id, total_amount))
            order_id = cursor.lastrowid

            # Insert Details
            for detail in order_details:
                cursor.execute('INSERT INTO Order_Details (order_id, food_item_id, quantity, price) VALUES (%s, %s, %s, %s)',
                               (order_id, detail[0], detail[1], detail[2]))

            # Create a pending payment
            cursor.execute("INSERT INTO Payments (student_id, amount, payment_type, status) VALUES (%s, %s, 'Meal', 'Pending')",
                           (student_id, total_amount))

            conn.commit()
            flash('Food ordered successfully! Payment added to pending dues.')

        return redirect(url_for('student_my_orders'))

    cursor.execute('SELECT * FROM Food_Items ORDER BY category, name')
    foods = cursor.fetchall()
    conn.close()

    return render_template('student/order_food.html', foods=foods)


@app.route('/student/my-orders')
def student_my_orders():
    if session.get('role') != 'Student':
        return redirect(url_for('index'))
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''SELECT o.id, o.total_amount, o.order_date, 
                      GROUP_CONCAT(CONCAT(f.name, " (", od.quantity, ")") SEPARATOR ", ") as items
                      FROM Orders o
                      JOIN Order_Details od ON o.id = od.order_id
                      JOIN Food_Items f ON od.food_item_id = f.id
                      WHERE o.student_id = %s
                      GROUP BY o.id
                      ORDER BY o.order_date DESC''', (student_id,))
    orders = cursor.fetchall()
    conn.close()

    return render_template('student/my_orders.html', orders=orders)


@app.route('/student/complaints', methods=['GET', 'POST'])
def student_complaints():
    if session.get('role') != 'Student':
        return redirect(url_for('index'))
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        description = request.form['description']
        is_anonymous = True if request.form.get('is_anonymous') else False

        cursor.execute(
            "SELECT room_id FROM Room_Assignments WHERE student_id=%s", (student_id,))
        room = cursor.fetchone()
        room_id = room['room_id'] if room else None

        cursor.execute('INSERT INTO Complaints (student_id, room_id, description, is_anonymous) VALUES (%s, %s, %s, %s)',
                       (student_id, room_id, description, is_anonymous))
        conn.commit()
        flash('Complaint submitted successfully')
        return redirect(url_for('student_complaints'))

    cursor.execute(
        'SELECT * FROM Complaints WHERE student_id=%s ORDER BY created_at DESC', (student_id,))
    complaints = cursor.fetchall()
    conn.close()

    return render_template('student/complaints.html', complaints=complaints)


@app.route('/student/maintenance', methods=['GET', 'POST'])
def student_maintenance():
    if session.get('role') != 'Student':
        return redirect(url_for('index'))
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        issue = request.form['issue']

        cursor.execute(
            "SELECT room_id FROM Room_Assignments WHERE student_id=%s", (student_id,))
        room = cursor.fetchone()

        if not room:
            flash('You must be assigned a room before requesting maintenance!')
        else:
            cursor.execute('INSERT INTO Maintenance_Requests (student_id, room_id, issue) VALUES (%s, %s, %s)',
                           (student_id, room['room_id'], issue))
            conn.commit()
            flash('Maintenance request submitted.')

        return redirect(url_for('student_maintenance'))

    cursor.execute(
        'SELECT * FROM Maintenance_Requests WHERE student_id=%s ORDER BY created_at DESC', (student_id,))
    requests = cursor.fetchall()
    conn.close()

    return render_template('student/maintenance.html', requests=requests)


@app.route('/student/payments')
def student_payments():
    if session.get('role') != 'Student':
        return redirect(url_for('index'))
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM Payments WHERE student_id=%s ORDER BY payment_date DESC', (student_id,))
    payments = cursor.fetchall()

    # Calculate Total Due
    cursor.execute(
        "SELECT SUM(amount) as dues FROM Payments WHERE student_id=%s AND status='Pending'", (student_id,))
    dues = cursor.fetchone()['dues'] or 0.0

    conn.close()
    return render_template('student/payments.html', payments=payments, dues=dues)


@app.route('/student/payments/pay/<int:id>', methods=['POST'])
def pay_amount(id):
    if session.get('role') != 'Student':
        return redirect(url_for('index'))

    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT status FROM Payments WHERE id=%s AND student_id=%s", (id, student_id))
    payment = cursor.fetchone()

    if not payment:
        conn.close()
        flash('Payment not found.')
        return redirect(url_for('student_payments'))

    if payment['status'] == 'Paid':
        conn.close()
        flash('This payment is already marked as paid.')
        return redirect(url_for('student_payments'))

    cursor.execute(
        "UPDATE Payments SET status='Paid' WHERE id=%s AND student_id=%s", (id, student_id))
    conn.commit()
    conn.close()
    flash('Payment marked as paid (cash).')
    return redirect(url_for('student_payments'))


@app.route('/student/payments/receipt/<int:id>')
def download_receipt(id):
    if session.get('role') != 'Student':
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM Payments WHERE id=%s AND student_id=%s', (id, session['user_id']))
    payment = cursor.fetchone()
    conn.close()

    if not payment:
        flash('Payment not found.')
        return redirect(url_for('student_payments'))

    html = render_template('student/receipt_pdf.html',
                           payment=payment, user_name=session['full_name'])

    # Needs wkhtmltopdf installed on system for pdfkit to work!
    # For demo purposes we can attempt to generate it or return HTML that looks like a PDF if not installed
    try:
        pdf_options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
        }
        pdf = pdfkit.from_string(html, False, options=pdf_options)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=receipt_{id}.pdf'
        return response
    except Exception as e:
        print(f"PDF generation error: {e}")
        flash('PDF Generation failed. Please install wkhtmltopdf on your system.')
        return redirect(url_for('student_payments'))


@app.route('/teacher')
def teacher_dashboard():
    if session.get('role') != 'Teacher':
        return redirect(url_for('index'))
    return render_template('teacher/dashboard.html')


@app.route('/teacher/rooms')
def teacher_rooms():
    if session.get('role') != 'Teacher':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.room_number, r.capacity, 
               (SELECT COUNT(*) FROM Room_Assignments WHERE room_id = r.id) as current_occupancy
        FROM Rooms r
        WHERE r.teacher_id = %s
    """, (session['user_id'],))
    rooms = cursor.fetchall()

    room_details = []
    for r in rooms:
        cursor.execute("""
            SELECT u.full_name, u.email, ra.assigned_date
            FROM Room_Assignments ra
            JOIN Users u ON ra.student_id = u.id
            WHERE ra.room_id = %s
        """, (r['id'],))
        students = cursor.fetchall()
        r['students'] = students
        room_details.append(r)

    cursor.close()
    conn.close()
    return render_template('teacher/rooms.html', rooms=room_details)


@app.route('/teacher/complaints')
def teacher_complaints():
    if session.get('role') != 'Teacher':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, u.full_name as student_name, r.room_number 
        FROM Complaints c
        LEFT JOIN Users u ON c.student_id = u.id
        LEFT JOIN Rooms r ON c.room_id = r.id
        WHERE r.teacher_id = %s
        ORDER BY c.created_at DESC
    """, (session['user_id'],))
    complaints = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('teacher/complaints.html', complaints=complaints)


@app.route('/teacher/complaints/update/<int:id>', methods=['POST'])
def teacher_update_complaint(id):
    if session.get('role') != 'Teacher':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Complaints SET status='Reviewed' WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('teacher_complaints'))


@app.route('/student/reading_room', methods=['GET', 'POST'])
def student_reading_room():
    if session.get('role') != 'Student':
        return redirect(url_for('index'))
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        booking_date = request.form['booking_date']
        time_slot = request.form['time_slot']

        try:
            cursor.execute('''INSERT INTO Reading_Room_Bookings (student_id, booking_date, time_slot)
                              VALUES (%s, %s, %s)''', (student_id, booking_date, time_slot))
            conn.commit()
            flash('Reading room booked successfully!')
        except Exception as e:
            flash('Slot already booked or invalid request.')
            conn.rollback()
        return redirect(url_for('student_reading_room'))

    cursor.execute('''SELECT * FROM Reading_Room_Bookings 
                      WHERE student_id=%s AND booking_date >= CURDATE()
                      ORDER BY booking_date, time_slot''', (student_id,))
    bookings = cursor.fetchall()
    conn.close()
    return render_template('student/reading_room.html', bookings=bookings)


@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if session['role'] == 'Student':
        cursor.execute('''SELECT u.id, u.full_name as name, 'Teacher' as info
                          FROM Users u
                          JOIN Rooms r ON u.id = r.teacher_id
                          JOIN Room_Assignments ra ON r.id = ra.room_id
                          WHERE ra.student_id = %s''', (session['user_id'],))
        contacts = cursor.fetchall()
        base_tmpl = 'student/dashboard.html'
    elif session['role'] == 'Teacher':
        cursor.execute('''SELECT u.id, u.full_name as name, r.room_number as info
                          FROM Users u
                          JOIN Room_Assignments ra ON u.id = ra.student_id
                          JOIN Rooms r ON ra.room_id = r.id
                          WHERE r.teacher_id = %s''', (session['user_id'],))
        contacts = cursor.fetchall()
        base_tmpl = 'teacher/dashboard.html'
    else:
        contacts = []
        base_tmpl = 'admin/dashboard.html'

    cursor.close()
    conn.close()

    return render_template('chat.html', contacts=contacts, base_template=base_tmpl)


@app.route('/api/chat/<int:receiver_id>')
def get_chat_history(receiver_id):
    if 'user_id' not in session:
        return jsonify([])

    sender_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''SELECT * FROM Chat_Messages 
                      WHERE (sender_id = %s AND receiver_id = %s) 
                         OR (sender_id = %s AND receiver_id = %s)
                      ORDER BY sent_at ASC''',
                   (sender_id, receiver_id, receiver_id, sender_id))
    messages = cursor.fetchall()

    # Convert datetime to string for JSON serialization
    for m in messages:
        m['sent_at'] = m['sent_at'].strftime('%Y-%m-%d %H:%M')

    cursor.close()
    conn.close()

    return jsonify(messages)


@socketio.on('send_message')
def handle_message(data):
    sender_id = session.get('user_id')
    if not sender_id:
        return

    receiver_id = data['receiver_id']
    message = data['message']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO Chat_Messages (sender_id, receiver_id, message) 
                      VALUES (%s, %s, %s)''', (sender_id, receiver_id, message))
    conn.commit()
    msg_id = cursor.lastrowid

    cursor.execute('SELECT * FROM Chat_Messages WHERE id = %s', (msg_id,))
    msg_data = cursor.fetchone()
    msg_data['sent_at'] = msg_data['sent_at'].strftime('%Y-%m-%d %H:%M')

    cursor.close()
    conn.close()

    # Send to the receiver's room and the sender's room
    emit('receive_message', msg_data, room=f"user_{receiver_id}")
    emit('receive_message', msg_data, room=f"user_{sender_id}")


@socketio.on('join')
def on_join(data):
    if 'user_id' in session:
        room = f"user_{session['user_id']}"
        join_room(room)

# Placeholder for modular routes like /admin/rooms, /student/meals, etc.


if __name__ == '__main__':
    socketio.run(app, debug=True)
