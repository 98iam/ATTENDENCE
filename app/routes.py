from app import app, supabase
from flask import render_template, request, jsonify, redirect, url_for
from datetime import datetime
import json
import os

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('attendance'))

@app.route('/attendance')
def attendance():
    try:
        # Get students from Supabase
        response = supabase.table('students').select('*').execute()
        students_data = response.data
        return render_template('attendance.html', students=students_data)
    except Exception as e:
        print(f"Error fetching students: {e}")
        return render_template('attendance.html', students=[])

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        data = request.get_json()
        roll_number = data.get('roll_number')
        status = data.get('status')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Check if attendance already exists for this student on this date
        existing = supabase.table('attendance').select('*').eq('roll_number', roll_number).eq('date', date).execute()
        
        if existing.data:
            # Update existing attendance record
            response = supabase.table('attendance').update({
                'status': status,
                'timestamp': datetime.now().isoformat()
            }).eq('roll_number', roll_number).eq('date', date).execute()
        else:
            # Insert new attendance record
            response = supabase.table('attendance').insert({
                'roll_number': roll_number,
                'status': status,
                'date': date,
                'timestamp': datetime.now().isoformat()
            }).execute()
        
        return jsonify({'success': True, 'message': 'Attendance marked successfully'})
    
    except Exception as e:
        print(f"Error marking attendance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/get_attendance/<date>')
def get_attendance(date):
    try:
        # Get attendance records from Supabase for the specified date
        response = supabase.table('attendance').select('*').eq('date', date).execute()
        records = {}
        for record in response.data:
            records[record['roll_number']] = {
                'status': record['status'],
                'timestamp': record['timestamp']
            }
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        print(f"Error fetching attendance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_attendance/<date>')
def export_attendance(date):
    try:
        # Get students and attendance records from Supabase
        students_response = supabase.table('students').select('*').execute()
        attendance_response = supabase.table('attendance').select('*').eq('date', date).execute()
        
        # Create a dictionary for quick lookup of attendance records
        attendance_dict = {}
        for record in attendance_response.data:
            attendance_dict[record['roll_number']] = {
                'status': record['status'],
                'timestamp': record['timestamp']
            }
        
        csv_data = []
        csv_data.append(['Roll Number', 'Name', 'Status', 'Timestamp'])
        
        for student in students_response.data:
            roll_number = student['roll_number']
            name = student['name']
            record = attendance_dict.get(roll_number, {})
            status = record.get('status', 'not_marked')
            timestamp = record.get('timestamp', '')
            csv_data.append([roll_number, name, status, timestamp])
        
        return jsonify({'success': True, 'data': csv_data})
    except Exception as e:
        print(f"Error exporting attendance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/students')
def get_students():
    try:
        response = supabase.table('students').select('*').execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        print(f"Error fetching students: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/add_student', methods=['POST'])
def add_student():
    try:
        data = request.get_json()
        roll_number = data.get('roll_number')
        name = data.get('name')
        
        # Check if student already exists
        existing = supabase.table('students').select('*').eq('roll_number', roll_number).execute()
        if existing.data:
            return jsonify({'success': False, 'error': 'Student with this roll number already exists'}), 400
        
        # Insert new student
        response = supabase.table('students').insert({
            'roll_number': roll_number,
            'name': name
        }).execute()
        
        return jsonify({'success': True, 'message': 'Student added successfully'})
    
    except Exception as e:
        print(f"Error adding student: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
