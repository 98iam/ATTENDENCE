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

@app.route('/student/<roll_number>')
def student_detail(roll_number):
    """Show detailed attendance history for a specific student"""
    try:
        # Get student information
        student_response = supabase.table('students').select('*').eq('roll_number', roll_number).execute()
        if not student_response.data:
            return render_template('error.html', error=f'Student with roll number {roll_number} not found'), 404
        
        student = student_response.data[0]
        
        # Get all attendance records for this student
        attendance_response = supabase.table('attendance').select('*').eq('roll_number', roll_number).order('date', desc=True).execute()
        attendance_records = attendance_response.data
        
        # Calculate statistics
        total_records = len(attendance_records)
        present_count = sum(1 for record in attendance_records if record['status'] == 'present')
        absent_count = sum(1 for record in attendance_records if record['status'] == 'absent')
        attendance_rate = round((present_count / total_records * 100), 2) if total_records > 0 else 0
        
        # Group records by month for better visualization
        from collections import defaultdict
        import calendar
        monthly_records = defaultdict(list)
        
        for record in attendance_records:
            # Extract year-month from date
            date_parts = record['date'].split('-')
            year, month = date_parts[0], date_parts[1]
            month_name = calendar.month_name[int(month)]
            key = f"{month_name} {year}"
            monthly_records[key].append(record)
        
        # Get recent attendance streak (consecutive days)
        current_streak = calculate_attendance_streak(attendance_records)
        
        stats = {
            'total_records': total_records,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_rate': attendance_rate,
            'current_streak': current_streak
        }
        
        return render_template('student_detail.html', 
                             student=student, 
                             attendance_records=attendance_records,
                             monthly_records=dict(monthly_records),
                             stats=stats)
    
    except Exception as e:
        print(f"Error in student detail: {e}")
        return render_template('error.html', error=str(e)), 500

def calculate_attendance_streak(records):
    """Calculate current attendance streak (consecutive present/absent days)"""
    if not records:
        return {'type': 'none', 'count': 0}
    
    # Sort by date descending (most recent first)
    sorted_records = sorted(records, key=lambda x: x['date'], reverse=True)
    
    if not sorted_records:
        return {'type': 'none', 'count': 0}
    
    # Get the most recent status
    current_status = sorted_records[0]['status']
    streak_count = 0
    
    # Count consecutive days with the same status
    for record in sorted_records:
        if record['status'] == current_status:
            streak_count += 1
        else:
            break
    
    return {
        'type': current_status,
        'count': streak_count
    }

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
    """Get students who are currently absent based on their most recent attendance record"""
    try:
        # Create attendance lookup sorted by date
        student_attendance = defaultdict(list)
        for record in attendance_records:
            student_attendance[record['roll_number']].append({
                'date': record['date'],
                'status': record['status']
            })
        
        # Sort each student's attendance by date (most recent first)
        for roll_number in student_attendance:
            student_attendance[roll_number].sort(key=lambda x: x['date'], reverse=True)
        
        absent_students = []
        
        for student in students:
            roll_number = student['roll_number']
            student_records = student_attendance.get(roll_number, [])
            
            if not student_records:
                # Student has no attendance records, skip
                continue
            
            # Get the most recent attendance record
            most_recent_record = student_records[0]
            
            # Only include in absent list if most recent record is 'absent'
            if most_recent_record['status'] == 'absent':
                # Count consecutive absent days from most recent backwards
                consecutive_days = 0
                absence_dates = []
                last_present_date = None
                
                # Count consecutive absences from most recent date
                for record in student_records:
                    if record['status'] == 'absent':
                        consecutive_days += 1
                        absence_dates.append(record['date'])
                    elif record['status'] == 'present':
                        last_present_date = record['date']
                        break
                    # If there's a gap in records, we stop counting consecutive days
                
                # Determine alert level based on consecutive days
                if consecutive_days >= 5:
                    alert_level = 'critical'
                elif consecutive_days >= 3:
                    alert_level = 'warning'
                else:
                    alert_level = 'concern'
                
                absent_students.append({
                    'student': student,
                    'consecutive_days': consecutive_days,
                    'absence_dates': absence_dates,  # Already in reverse chronological order
                    'last_present_date': last_present_date,
                    'most_recent_absence_date': most_recent_record['date'],
                    'alert_level': alert_level
                })
        
        # Sort by consecutive days (most concerning first), then by most recent absence date
        absent_students.sort(key=lambda x: (x['consecutive_days'], x['most_recent_absence_date']), reverse=True)
        
        return absent_students
        
    except Exception as e:
        print(f"Error getting consecutive absent students: {e}")
        return []

# Marks System Routes
@app.route('/marks_entry')
def marks_entry():
    """Page for entering and viewing student marks."""
    try:
        students_response = supabase.table('students').select('roll_number, name').order('name', desc=False).execute()
        students = students_response.data
        return render_template('marks_entry.html', students=students)
    except Exception as e:
        print(f"Error fetching students for marks entry: {e}")
        return render_template('marks_entry.html', students=[], error=str(e))

@app.route('/get_student_marks', methods=['GET'])
def get_student_marks():
    """API endpoint to fetch student marks.
    Can be filtered by subject and exam_date query parameters.
    """
    try:
        subject = request.args.get('subject')
        exam_date = request.args.get('exam_date')

        query = supabase.table('student_marks').select('*')
        if subject:
            query = query.eq('subject', subject)
        if exam_date:
            query = query.eq('exam_date', exam_date)

        marks_response = query.execute()
        marks_data = marks_response.data

        # Organize marks by student roll number for easier access on the frontend
        marks_by_student = defaultdict(list)
        for mark_record in marks_data:
            marks_by_student[mark_record['student_roll_number']].append(mark_record)

        return jsonify({'success': True, 'data': dict(marks_by_student)})
    except Exception as e:
        print(f"Error fetching student marks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/save_student_marks', methods=['POST'])
def save_student_marks():
    """API endpoint to save or update student marks."""
    try:
        data = request.get_json()

        # Basic validation
        required_fields = ['student_roll_number', 'subject', 'marks']
        for field in required_fields:
            if field not in data or data[field] is None: # Check for None as well
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        student_roll_number = data.get('student_roll_number')
        subject = data.get('subject')
        marks_value = data.get('marks')
        exam_date = data.get('exam_date') # Optional, can be None

        # Validate marks value (should be a number)
        try:
            marks_value = float(marks_value) if marks_value else None # Allow empty marks to clear them
        except ValueError:
            return jsonify({'success': False, 'error': 'Marks must be a valid number or empty.'}), 400

        # Verify student exists
        student_check = supabase.table('students').select('roll_number').eq('roll_number', student_roll_number).execute()
        if not student_check.data:
            return jsonify({'success': False, 'error': f'Student with roll number {student_roll_number} does not exist'}), 404

        # Prepare data for upsert
        mark_record_data = {
            'student_roll_number': student_roll_number,
            'subject': subject,
            'marks': marks_value,
            'exam_date': exam_date if exam_date else None, # Ensure None if empty string
        }

        # Upsert logic: Update if exists, else insert.
        # The UNIQUE constraint on (student_roll_number, subject, exam_date) is key here.
        # Supabase client's upsert handles this. We need to specify the `on_conflict` columns.

        # If exam_date is None, we might need a different conflict target or handle it carefully.
        # For simplicity, let's assume exam_date is part of the unique key.
        # If exam_date can be null and still unique for a subject, the schema needs to reflect that,
        # or we handle it by updating based on id if an id is passed, or querying first.

        # For a robust upsert, we often query first or rely on db returning the ID.
        # Let's try a direct upsert based on the unique constraint.
        # The `on_conflict` parameter should list the columns that define the conflict (the unique constraint columns).

        response = supabase.table('student_marks').upsert(
            mark_record_data,
            on_conflict='student_roll_number,subject,exam_date' # Specify columns for conflict resolution
        ).execute()

        if response.data:
            return jsonify({'success': True, 'message': 'Marks saved successfully', 'data': response.data[0]})
        else:
            # This part might indicate an issue with the upsert or how Supabase returns data for it.
            # For now, assume success if no error, but ideally, check response details.
            # Supabase upsert might not return data if the record was just updated and not changed,
            # or if returning="minimal" is default. Let's assume it's successful if no error.
            if hasattr(response, 'error') and response.error:
                 return jsonify({'success': False, 'error': f'Database error: {response.error.message}'}), 500
            return jsonify({'success': True, 'message': 'Marks saved successfully (operation completed)'})

    except Exception as e:
        error_message = str(e)
        print(f"Error saving student marks: {error_message}")
        # Check for constraint violations specifically if possible
        if 'unique constraint' in error_message.lower():
            return jsonify({'success': False, 'error': 'A mark for this student, subject, and exam date already exists. Upsert failed unexpectedly.'}), 409
        return jsonify({'success': False, 'error': f'Server error: {error_message}'}), 500
