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

@app.route('/history')
def history():
    try:
        # Get students from Supabase for history page
        response = supabase.table('students').select('*').execute()
        students_data = response.data
        today = datetime.now().strftime('%Y-%m-%d')
        return render_template('history.html', students=students_data, today=today)
    except Exception as e:
        print(f"Error fetching students for history: {e}")
        today = datetime.now().strftime('%Y-%m-%d')
        return render_template('history.html', students=[], today=today)

@app.route('/admin')
def admin():
    """Admin page for database management"""
    try:
        # Get database statistics
        students_response = supabase.table('students').select('*').execute()
        attendance_response = supabase.table('attendance').select('*').execute()
        
        # Get unique dates
        unique_dates = []
        if attendance_response.data:
            unique_dates = list(set(record['date'] for record in attendance_response.data))
            unique_dates.sort(reverse=True)
        
        stats = {
            'total_students': len(students_response.data),
            'total_attendance_records': len(attendance_response.data),
            'unique_dates': len(unique_dates),
            'recent_dates': unique_dates[:10]  # Show last 10 dates
        }
        
        return render_template('admin.html', stats=stats, students=students_response.data)
    except Exception as e:
        print(f"Error in admin page: {e}")
        return render_template('admin.html', stats={'error': str(e)}, students=[])

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        data = request.get_json()
        roll_number = data.get('roll_number')
        status = data.get('status')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Validate input
        if not roll_number or not status:
            return jsonify({'success': False, 'error': 'Roll number and status are required'}), 400
        
        if status not in ['present', 'absent']:
            return jsonify({'success': False, 'error': 'Status must be either "present" or "absent"'}), 400
        
        # Verify student exists
        student_check = supabase.table('students').select('roll_number').eq('roll_number', roll_number).execute()
        if not student_check.data:
            return jsonify({'success': False, 'error': f'Student with roll number {roll_number} does not exist'}), 400
        
        current_timestamp = datetime.now().isoformat()
        
        # Use upsert operation to handle insert/update atomically
        # This prevents race conditions and duplicate entries
        try:
            # First attempt: try to insert new record
            response = supabase.table('attendance').insert({
                'roll_number': roll_number,
                'status': status,
                'date': date,
                'timestamp': current_timestamp
            }).execute()
            
            return jsonify({
                'success': True, 
                'message': f'Attendance marked as {status} for {roll_number}',
                'action': 'created'
            })
            
        except Exception as insert_error:
            # If insert fails (likely due to unique constraint), try update
            print(f"Insert failed, attempting update: {insert_error}")
            
            try:
                # Update existing record
                update_response = supabase.table('attendance').update({
                    'status': status,
                    'timestamp': current_timestamp
                }).eq('roll_number', roll_number).eq('date', date).execute()
                
                if update_response.data:
                    return jsonify({
                        'success': True, 
                        'message': f'Attendance updated to {status} for {roll_number}',
                        'action': 'updated'
                    })
                else:
                    # If update didn't affect any rows, the record might not exist
                    # Try insert one more time
                    final_response = supabase.table('attendance').insert({
                        'roll_number': roll_number,
                        'status': status,
                        'date': date,
                        'timestamp': current_timestamp
                    }).execute()
                    
                    return jsonify({
                        'success': True, 
                        'message': f'Attendance marked as {status} for {roll_number}',
                        'action': 'created_retry'
                    })
                    
            except Exception as update_error:
                print(f"Update also failed: {update_error}")
                raise update_error
    
    except Exception as e:
        error_message = str(e)
        print(f"Error marking attendance: {error_message}")
        
        # Check if it's a constraint violation
        if 'unique' in error_message.lower() or 'duplicate' in error_message.lower():
            return jsonify({
                'success': False, 
                'error': f'Attendance for {roll_number} on {date} has already been recorded. Use the update function instead.'
            }), 409
        
        return jsonify({'success': False, 'error': f'Database error: {error_message}'}), 500

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

@app.route('/clear_attendance', methods=['POST'])
def clear_attendance():
    """Clear all attendance records - for testing purposes"""
    try:
        # Get count before deletion for confirmation
        count_response = supabase.table('attendance').select('id').execute()
        record_count = len(count_response.data)
        
        # Clear all attendance records
        response = supabase.table('attendance').delete().neq('id', 0).execute()
        
        return jsonify({
            'success': True, 
            'message': f'Successfully cleared {record_count} attendance records'
        })
    
    except Exception as e:
        print(f"Error clearing attendance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/database_status')
def database_status():
    """Get database status and statistics"""
    try:
        # Get student count
        students_response = supabase.table('students').select('id').execute()
        student_count = len(students_response.data)
        
        # Get attendance record count
        attendance_response = supabase.table('attendance').select('id').execute()
        attendance_count = len(attendance_response.data)
        
        # Get unique dates with attendance
        dates_response = supabase.rpc('get_attendance_dates').execute() if hasattr(supabase, 'rpc') else None
        unique_dates = []
        
        # Alternative way to get unique dates
        if attendance_response.data:
            all_records = supabase.table('attendance').select('date').execute()
            unique_dates = list(set(record['date'] for record in all_records.data))
            unique_dates.sort()
        
        return jsonify({
            'success': True,
            'data': {
                'students': student_count,
                'attendance_records': attendance_count,
                'unique_attendance_dates': len(unique_dates),
                'dates': unique_dates
            }
        })
    
    except Exception as e:
        print(f"Error getting database status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/validate_attendance_integrity')
def validate_attendance_integrity():
    """Validate that there are no duplicate attendance records for same student on same date"""
    try:
        # Get all attendance records
        response = supabase.table('attendance').select('roll_number, date').execute()
        records = response.data
        
        # Check for duplicates
        seen = set()
        duplicates = []
        
        for record in records:
            key = (record['roll_number'], record['date'])
            if key in seen:
                duplicates.append(key)
            else:
                seen.add(key)
        
        if duplicates:
            return jsonify({
                'success': False,
                'message': 'Duplicate records found',
                'duplicates': [{'roll_number': dup[0], 'date': dup[1]} for dup in duplicates]
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No duplicate records found',
                'total_records': len(records)
            })
    
    except Exception as e:
        print(f"Error validating attendance integrity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
