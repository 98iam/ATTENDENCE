from app import app
from flask import render_template, request, jsonify, redirect, url_for
from datetime import datetime
import json
import os

# In-memory storage for attendance data (you can replace this with a database)
attendance_records = {}
students_data = [
    {'roll_number': '001', 'name': 'John Smith'},
    {'roll_number': '002', 'name': 'Emma Johnson'},
    {'roll_number': '003', 'name': 'Michael Brown'},
    {'roll_number': '004', 'name': 'Sarah Davis'},
    {'roll_number': '005', 'name': 'David Wilson'},
    {'roll_number': '006', 'name': 'Lisa Anderson'},
    {'roll_number': '007', 'name': 'James Taylor'},
    {'roll_number': '008', 'name': 'Jennifer Martinez'},
    {'roll_number': '009', 'name': 'Robert Garcia'},
    {'roll_number': '010', 'name': 'Maria Rodriguez'},
    {'roll_number': '011', 'name': 'Christopher Lee'},
    {'roll_number': '012', 'name': 'Amanda White'},
    {'roll_number': '013', 'name': 'Matthew Harris'},
    {'roll_number': '014', 'name': 'Jessica Clark'},
    {'roll_number': '015', 'name': 'Andrew Lewis'},
    {'roll_number': '016', 'name': 'Ashley Walker'},
    {'roll_number': '017', 'name': 'Joshua Hall'},
    {'roll_number': '018', 'name': 'Nicole Allen'},
    {'roll_number': '019', 'name': 'Daniel Young'},
    {'roll_number': '020', 'name': 'Stephanie King'},
    {'roll_number': '021', 'name': 'Ryan Wright'},
    {'roll_number': '022', 'name': 'Megan Lopez'},
    {'roll_number': '023', 'name': 'Kevin Hill'},
    {'roll_number': '024', 'name': 'Lauren Green'},
    {'roll_number': '025', 'name': 'Brandon Adams'}
]

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('attendance'))

@app.route('/attendance')
def attendance():
    return render_template('attendance.html', students=students_data)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        data = request.get_json()
        roll_number = data.get('roll_number')
        status = data.get('status')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Store attendance record
        if date not in attendance_records:
            attendance_records[date] = {}
        
        attendance_records[date][roll_number] = {
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'message': 'Attendance marked successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/get_attendance/<date>')
def get_attendance(date):
    try:
        records = attendance_records.get(date, {})
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_attendance/<date>')
def export_attendance(date):
    try:
        records = attendance_records.get(date, {})
        csv_data = []
        csv_data.append(['Roll Number', 'Name', 'Status', 'Timestamp'])
        
        for student in students_data:
            roll_number = student['roll_number']
            name = student['name']
            record = records.get(roll_number, {})
            status = record.get('status', 'not_marked')
            timestamp = record.get('timestamp', '')
            csv_data.append([roll_number, name, status, timestamp])
        
        return jsonify({'success': True, 'data': csv_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/students')
def get_students():
    return jsonify({'success': True, 'data': students_data})

@app.route('/add_student', methods=['POST'])
def add_student():
    try:
        data = request.get_json()
        roll_number = data.get('roll_number')
        name = data.get('name')
        
        # Check if student already exists
        if any(s['roll_number'] == roll_number for s in students_data):
            return jsonify({'success': False, 'error': 'Student with this roll number already exists'}), 400
        
        students_data.append({'roll_number': roll_number, 'name': name})
        return jsonify({'success': True, 'message': 'Student added successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
