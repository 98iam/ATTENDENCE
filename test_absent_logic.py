#!/usr/bin/env python3
"""
Test script to verify the absent students logic works correctly
"""

from collections import defaultdict
from datetime import datetime, timedelta

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

# Test scenario based on your requirements
def test_scenario():
    print("Testing absent students logic...")
    
    # Test students
    students = [
        {'roll_number': 'A001', 'name': 'Student A'},
        {'roll_number': 'B002', 'name': 'Student B'},
        {'roll_number': 'C003', 'name': 'Student C'},
    ]
    
    # Test attendance records - Student A scenario from your example
    attendance_records = [
        # Student A: Present Jan 19, Absent Jan 20, Present Jan 21, Absent Jan 22-23, Present Jan 27
        {'roll_number': 'A001', 'date': '2024-01-19', 'status': 'present'},
        {'roll_number': 'A001', 'date': '2024-01-20', 'status': 'absent'},
        {'roll_number': 'A001', 'date': '2024-01-21', 'status': 'present'},
        {'roll_number': 'A001', 'date': '2024-01-22', 'status': 'absent'},
        {'roll_number': 'A001', 'date': '2024-01-23', 'status': 'absent'},
        {'roll_number': 'A001', 'date': '2024-01-27', 'status': 'present'},
        
        # Student B: Present Jan 19, Absent Jan 20-22 (still absent)
        {'roll_number': 'B002', 'date': '2024-01-19', 'status': 'present'},
        {'roll_number': 'B002', 'date': '2024-01-20', 'status': 'absent'},
        {'roll_number': 'B002', 'date': '2024-01-21', 'status': 'absent'},
        {'roll_number': 'B002', 'date': '2024-01-22', 'status': 'absent'},
        
        # Student C: Only present records
        {'roll_number': 'C003', 'date': '2024-01-19', 'status': 'present'},
        {'roll_number': 'C003', 'date': '2024-01-20', 'status': 'present'},
        {'roll_number': 'C003', 'date': '2024-01-21', 'status': 'present'},
    ]
    
    # Test the function
    absent_students = get_consecutive_absent_students(students, attendance_records)
    
    print(f"\nFound {len(absent_students)} students in absent list:")
    for student_info in absent_students:
        print(f"- {student_info['student']['name']} ({student_info['student']['roll_number']})")
        print(f"  Consecutive days absent: {student_info['consecutive_days']}")
        print(f"  Most recent absence: {student_info['most_recent_absence_date']}")
        print(f"  Alert level: {student_info['alert_level']}")
        print(f"  Last present date: {student_info['last_present_date']}")
        print()
    
    # Expected results:
    # - Student A should NOT be in absent list (most recent record is present on Jan 27)
    # - Student B should be in absent list (most recent record is absent on Jan 22)
    # - Student C should NOT be in absent list (most recent record is present on Jan 21)
    
    print("Expected results:")
    print("- Student A: NOT in absent list (last record is present)")
    print("- Student B: IN absent list (last record is absent with 3 consecutive days)")
    print("- Student C: NOT in absent list (last record is present)")

if __name__ == "__main__":
    test_scenario()