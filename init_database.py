#!/usr/bin/env python3
"""
Database initialization script for the Attendance System
This script sets up the required tables and constraints in Supabase
"""

from app import supabase
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY
from supabase import create_client
import sys

def init_database():
    """Initialize database tables and constraints"""
    
    print("🚀 Initializing Attendance System Database...")
    
    try:
        # Note: Since Supabase doesn't directly support DDL operations through the Python client,
        # we'll need to create the tables in the Supabase dashboard or use SQL commands.
        # This script will focus on clearing existing data and setting up sample data.
        
        print("📋 Database Schema Information:")
        print("=" * 50)
        print("Required Tables:")
        print("1. students (roll_number TEXT PRIMARY KEY, name TEXT NOT NULL)")
        print("2. attendance (")
        print("   id SERIAL PRIMARY KEY,")
        print("   roll_number TEXT NOT NULL,")
        print("   date DATE NOT NULL,")
        print("   status TEXT NOT NULL CHECK (status IN ('present', 'absent')),")
        print("   timestamp TIMESTAMPTZ DEFAULT NOW(),")
        print("   FOREIGN KEY (roll_number) REFERENCES students(roll_number),")
        print("   UNIQUE(roll_number, date) -- This prevents duplicate entries per day")
        print("   )")
        print("3. student_marks (")
        print("   id SERIAL PRIMARY KEY,")
        print("   student_roll_number TEXT NOT NULL,")
        print("   subject TEXT NOT NULL,")
        print("   marks REAL,")
        print("   exam_date DATE,")
        print("   created_at TIMESTAMPTZ DEFAULT NOW(),")
        print("   updated_at TIMESTAMPTZ DEFAULT NOW(),")
        print("   FOREIGN KEY (student_roll_number) REFERENCES students(roll_number) ON DELETE CASCADE,")
        print("   UNIQUE(student_roll_number, subject, exam_date)")
        print("   )")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def clear_all_attendance():
    """Clear all attendance records"""
    try:
        print("🧹 Clearing all attendance records...")
        response = supabase.table('attendance').delete().neq('id', 0).execute()
        print(f"✅ Cleared attendance records")
        return True
    except Exception as e:
        print(f"❌ Error clearing attendance records: {e}")
        return False

def clear_all_marks():
    """Clear all student marks records"""
    try:
        print("🧹 Clearing all student marks records...")
        response = supabase.table('student_marks').delete().neq('id', 0).execute()
        print(f"✅ Cleared student marks records")
        return True
    except Exception as e:
        print(f"❌ Error clearing student marks records: {e}")
        return False

def setup_sample_students():
    """Setup sample students if the table is empty"""
    try:
        print("👥 Checking for existing students...")
        response = supabase.table('students').select('*').execute()
        
        if not response.data:
            print("📝 Adding sample students...")
            sample_students = [
                {"roll_number": "CS001", "name": "Alice Johnson"},
                {"roll_number": "CS002", "name": "Bob Smith"},
                {"roll_number": "CS003", "name": "Charlie Brown"},
                {"roll_number": "CS004", "name": "Diana Prince"},
                {"roll_number": "CS005", "name": "Eve Wilson"},
                {"roll_number": "CS006", "name": "Frank Miller"},
                {"roll_number": "CS007", "name": "Grace Lee"},
                {"roll_number": "CS008", "name": "Henry Davis"},
                {"roll_number": "CS009", "name": "Ivy Chen"},
                {"roll_number": "CS010", "name": "Jack Thompson"}
            ]
            
            for student in sample_students:
                try:
                    supabase.table('students').insert(student).execute()
                    print(f"  ➕ Added: {student['name']} ({student['roll_number']})")
                except Exception as e:
                    print(f"  ⚠️  Student {student['roll_number']} might already exist: {e}")
        else:
            print(f"✅ Found {len(response.data)} existing students")
            
        return True
    except Exception as e:
        print(f"❌ Error setting up students: {e}")
        return False

def test_database_constraints():
    """Test that the database constraints work properly"""
    try:
        print("🧪 Testing database constraints...")
        
        # Try to insert duplicate attendance record
        test_data = {
            "roll_number": "CS001",
            "date": "2024-01-01",
            "status": "present",
            "timestamp": "2024-01-01T10:00:00Z"
        }
        
        # First insertion should succeed
        try:
            response1 = supabase.table('attendance').insert(test_data).execute()
            print("  ✅ First insertion successful")
        except Exception as e:
            print(f"  ℹ️  First insertion failed (might already exist): {e}")
        
        # Second insertion should fail due to unique constraint
        try:
            response2 = supabase.table('attendance').insert(test_data).execute()
            print("  ❌ ERROR: Duplicate insertion succeeded - constraint not working!")
            return False
        except Exception as e:
            print("  ✅ Duplicate insertion properly rejected by database constraint")
        
        # Clean up test data
        try:
            supabase.table('attendance').delete().eq('roll_number', 'CS001').eq('date', '2024-01-01').execute()
            print("  🧹 Test data cleaned up")
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing constraints: {e}")
        return False

def main():
    """Main function"""
    print("🎯 Attendance System Database Setup")
    print("=" * 40)
    
    # Initialize database
    if not init_database():
        sys.exit(1)
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Clear all attendance records")
    print("2. Clear all student marks records")
    print("3. Setup sample students")
    print("4. Test database constraints (attendance)")
    # Placeholder for future marks constraint test
    # print("5. Test database constraints (marks)")
    print("5. All cleanup & setup (Clear all data, setup samples, test constraints)")
    print("6. Exit")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice == "1":
        clear_all_attendance()
    elif choice == "2":
        clear_all_marks()
    elif choice == "3":
        setup_sample_students()
    elif choice == "4":
        test_database_constraints()
    # elif choice == "5": # Placeholder for future marks constraint test
        # test_marks_constraints()
    elif choice == "5":
        clear_all_attendance()
        clear_all_marks()
        setup_sample_students()
        test_database_constraints()
        # test_marks_constraints() # Placeholder
    elif choice == "6":
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")
        return
    
    print("\n✨ Database setup completed!")
    print("\n📝 IMPORTANT NOTES:")
    print("- Make sure your Supabase tables have the proper constraints")
    print("- The 'attendance' table should have a UNIQUE constraint on (roll_number, date)")
    print("- This prevents duplicate attendance entries for the same student on the same day")

if __name__ == "__main__":
    main()