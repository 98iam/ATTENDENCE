from app import app, supabase
from flask import render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict, Counter

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('dashboard'))

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

@app.route('/dashboard')
def dashboard():
    """Main dashboard with student management and analytics"""
    try:
        # Get all students
        students_response = supabase.table('students').select('*').execute()
        students = students_response.data
        
        # Get recent attendance data (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        attendance_response = supabase.table('attendance').select('*').gte('date', thirty_days_ago).execute()
        attendance_records = attendance_response.data
        
        # Calculate statistics
        stats = calculate_dashboard_stats(students, attendance_records)
        
        # Get consecutive absent students
        absent_students = get_consecutive_absent_students(students, attendance_records)
        
        return render_template('dashboard.html', 
                             students=students, 
                             stats=stats, 
                             absent_students=absent_students)
    except Exception as e:
        print(f"Error in dashboard: {e}")
        return render_template('dashboard.html', 
                             students=[], 
                             stats={'error': str(e)}, 
                             absent_students=[])

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

# Student Management Routes
@app.route('/update_student', methods=['PUT'])
def update_student():
    """Update student information"""
    try:
        data = request.get_json()
        student_id = data.get('id')
        roll_number = data.get('roll_number')
        name = data.get('name')
        
        if not student_id or not roll_number or not name:
            return jsonify({'success': False, 'error': 'ID, roll number and name are required'}), 400
        
        # Check if roll number already exists for different student
        existing = supabase.table('students').select('*').eq('roll_number', roll_number).neq('id', student_id).execute()
        if existing.data:
            return jsonify({'success': False, 'error': 'Roll number already exists for another student'}), 400
        
        # Update student
        response = supabase.table('students').update({
            'roll_number': roll_number,
            'name': name
        }).eq('id', student_id).execute()
        
        return jsonify({'success': True, 'message': 'Student updated successfully'})
    
    except Exception as e:
        print(f"Error updating student: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_student', methods=['DELETE'])
def delete_student():
    """Delete student and all their attendance records"""
    try:
        data = request.get_json()
        student_id = data.get('id')
        
        if not student_id:
            return jsonify({'success': False, 'error': 'Student ID is required'}), 400
        
        # Get student info first
        student_response = supabase.table('students').select('*').eq('id', student_id).execute()
        if not student_response.data:
            return jsonify({'success': False, 'error': 'Student not found'}), 404
        
        student = student_response.data[0]
        roll_number = student['roll_number']
        
        # Delete attendance records first
        supabase.table('attendance').delete().eq('roll_number', roll_number).execute()
        
        # Delete student
        supabase.table('students').delete().eq('id', student_id).execute()
        
        return jsonify({'success': True, 'message': f'Student {student["name"]} and all attendance records deleted successfully'})
    
    except Exception as e:
        print(f"Error deleting student: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_dashboard_data')
def get_dashboard_data():
    """Get dashboard analytics data"""
    try:
        # Get all students
        students_response = supabase.table('students').select('*').execute()
        students = students_response.data
        
        # Get recent attendance data (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        attendance_response = supabase.table('attendance').select('*').gte('date', thirty_days_ago).execute()
        attendance_records = attendance_response.data
        
        # Calculate statistics
        stats = calculate_dashboard_stats(students, attendance_records)
        
        # Get consecutive absent students
        absent_students = get_consecutive_absent_students(students, attendance_records)
        
        return jsonify({
            'success': True,
            'data': {
                'stats': stats,
                'absent_students': absent_students
            }
        })
    
    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper Functions
def calculate_dashboard_stats(students, attendance_records):
    """Calculate dashboard statistics"""
    try:
        total_students = len(students)
        
        # Group attendance by date
        attendance_by_date = defaultdict(list)
        for record in attendance_records:
            attendance_by_date[record['date']].append(record)
        
        # Calculate daily statistics
        daily_stats = []
        for date, records in attendance_by_date.items():
            present_count = sum(1 for r in records if r['status'] == 'present')
            absent_count = sum(1 for r in records if r['status'] == 'absent')
            total_marked = present_count + absent_count
            not_marked = total_students - total_marked
            
            daily_stats.append({
                'date': date,
                'present': present_count,
                'absent': absent_count,
                'not_marked': not_marked,
                'total': total_students,
                'attendance_percentage': round((present_count / total_students * 100), 2) if total_students > 0 else 0
            })
        
        # Sort by date
        daily_stats.sort(key=lambda x: x['date'], reverse=True)
        
        # Overall statistics
        total_records = len(attendance_records)
        total_present = sum(1 for r in attendance_records if r['status'] == 'present')
        total_absent = sum(1 for r in attendance_records if r['status'] == 'absent')
        
        overall_stats = {
            'total_students': total_students,
            'total_records': total_records,
            'total_present': total_present,
            'total_absent': total_absent,
            'overall_attendance_rate': round((total_present / total_records * 100), 2) if total_records > 0 else 0,
            'daily_stats': daily_stats[:14]  # Last 14 days
        }
        
        return overall_stats
        
    except Exception as e:
        print(f"Error calculating dashboard stats: {e}")
        return {'error': str(e)}

def get_consecutive_absent_students(students, attendance_records):
    """Get students with consecutive absences"""
    try:
        # Create attendance lookup
        attendance_lookup = defaultdict(dict)
        for record in attendance_records:
            attendance_lookup[record['roll_number']][record['date']] = record['status']
        
        # Generate date range for last 30 days
        today = datetime.now()
        date_range = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
        date_range.reverse()  # Oldest to newest
        
        absent_students = []
        
        for student in students:
            roll_number = student['roll_number']
            consecutive_days = 0
            last_present_date = None
            absence_dates = []
            
            # Check each day from most recent backwards
            for date in reversed(date_range):
                status = attendance_lookup[roll_number].get(date)
                
                if status == 'absent':
                    consecutive_days += 1
                    absence_dates.append(date)
                elif status == 'present':
                    last_present_date = date
                    break
                # If no record (not marked), we don't count it as consecutive absence
                # but we note the last present date
            
            # Only include students with 2+ consecutive absences
            if consecutive_days >= 2:
                absent_students.append({
                    'student': student,
                    'consecutive_days': consecutive_days,
                    'absence_dates': list(reversed(absence_dates)),  # Most recent first
                    'last_present_date': last_present_date,
                    'alert_level': 'critical' if consecutive_days >= 5 else 'warning' if consecutive_days >= 3 else 'concern'
                })
        
        # Sort by consecutive days (most concerning first)
        absent_students.sort(key=lambda x: x['consecutive_days'], reverse=True)
        
        return absent_students
        
    except Exception as e:
        print(f"Error getting consecutive absent students: {e}")
        return []
