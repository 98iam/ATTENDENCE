#!/usr/bin/env python3
"""
Script to add sample students to the database
Run this script to populate your database with 12 students
"""

from app import supabase
from datetime import datetime, timedelta
import random

def add_sample_students():
    """Add 12 sample students to the database"""
    
    students = [
        {'roll_number': 'CS001', 'name': 'Alice Johnson'},
        {'roll_number': 'CS002', 'name': 'Bob Smith'},
        {'roll_number': 'CS003', 'name': 'Charlie Brown'},
        {'roll_number': 'CS004', 'name': 'Diana Prince'},
        {'roll_number': 'CS005', 'name': 'Eve Wilson'},
        {'roll_number': 'CS006', 'name': 'Frank Miller'},
        {'roll_number': 'CS007', 'name': 'Grace Lee'},
        {'roll_number': 'CS008', 'name': 'Henry Davis'},
        {'roll_number': 'CS009', 'name': 'Ivy Chen'},
        {'roll_number': 'CS010', 'name': 'Jack Thompson'},
        {'roll_number': 'CS011', 'name': 'Karen White'},
        {'roll_number': 'CS012', 'name': 'Leo Martinez'}
    ]
    
    print("Adding sample students to database...")
    
    try:
        # Clear existing students first (optional)
        clear_choice = input("Do you want to clear existing students first? (y/N): ").lower()
        if clear_choice == 'y':
            print("Clearing existing students...")
            supabase.table('attendance').delete().neq('id', 0).execute()
            supabase.table('students').delete().neq('id', 0).execute()
            print("Existing data cleared.")
        
        # Add students
        for student in students:
            try:
                response = supabase.table('students').insert(student).execute()
                print(f"✓ Added: {student['name']} ({student['roll_number']})")
            except Exception as e:
                if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                    print(f"⚠ Skipped: {student['name']} (already exists)")
                else:
                    print(f"✗ Error adding {student['name']}: {e}")
        
        print("\n" + "="*50)
        print("SAMPLE STUDENTS ADDED SUCCESSFULLY!")
        print("="*50)
        
        # Verify the additions
        response = supabase.table('students').select('*').execute()
        print(f"Total students in database: {len(response.data)}")
        
        # Ask if user wants to add sample attendance data
        add_attendance = input("\nDo you want to add sample attendance data for the past 10 days? (y/N): ").lower()
        if add_attendance == 'y':
            add_sample_attendance(response.data)
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def add_sample_attendance(students):
    """Add sample attendance data for the past 10 days"""
    print("\nAdding sample attendance data...")
    
    try:
        # Generate attendance for the past 10 days
        for i in range(10):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            print(f"Adding attendance for {date}...")
            
            for student in students:
                # Randomly assign present/absent (80% chance of being present)
                status = 'present' if random.random() < 0.8 else 'absent'
                
                try:
                    supabase.table('attendance').insert({
                        'roll_number': student['roll_number'],
                        'status': status,
                        'date': date,
                        'timestamp': datetime.now().isoformat()
                    }).execute()
                except Exception as e:
                    if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                        pass  # Skip duplicates
                    else:
                        print(f"Error adding attendance for {student['roll_number']}: {e}")
        
        print("✓ Sample attendance data added!")
        
        # Show summary
        attendance_response = supabase.table('attendance').select('*').execute()
        print(f"Total attendance records: {len(attendance_response.data)}")
        
    except Exception as e:
        print(f"Error adding attendance data: {e}")

if __name__ == "__main__":
    print("Student Database Setup")
    print("="*30)
    success = add_sample_students()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nYou can now:")
        print("1. Run your Flask app: python run.py")
        print("2. Visit the dashboard to see students")
        print("3. Click on any student name to see their attendance details")
        print("4. Use the attendance page to mark daily attendance")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")