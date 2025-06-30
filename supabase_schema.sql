-- Attendance System Database Schema for Supabase
-- Run this SQL in your Supabase SQL Editor to set up the proper database structure

-- Enable Row Level Security (recommended for Supabase)
-- You can adjust these policies based on your security requirements

-- 1. Create Students Table
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    roll_number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create Attendance Table with proper constraints
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    roll_number TEXT NOT NULL,
    date DATE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('present', 'absent')),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Foreign key constraint
    FOREIGN KEY (roll_number) REFERENCES students(roll_number) ON DELETE CASCADE,
    
    -- UNIQUE constraint to prevent duplicate entries for same student on same date
    UNIQUE(roll_number, date)
);

-- 3. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_attendance_roll_number ON attendance(roll_number);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
CREATE INDEX IF NOT EXISTS idx_attendance_roll_date ON attendance(roll_number, date);
CREATE INDEX IF NOT EXISTS idx_students_roll_number ON students(roll_number);

-- 4. Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 5. Create triggers to automatically update updated_at column
DROP TRIGGER IF EXISTS update_students_updated_at ON students;
CREATE TRIGGER update_students_updated_at 
    BEFORE UPDATE ON students 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_attendance_updated_at ON attendance;
CREATE TRIGGER update_attendance_updated_at 
    BEFORE UPDATE ON attendance 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 6. Insert sample students (you can modify or remove this section)
INSERT INTO students (roll_number, name) VALUES
    ('CS001', 'Alice Johnson'),
    ('CS002', 'Bob Smith'),
    ('CS003', 'Charlie Brown'),
    ('CS004', 'Diana Prince'),
    ('CS005', 'Eve Wilson'),
    ('CS006', 'Frank Miller'),
    ('CS007', 'Grace Lee'),
    ('CS008', 'Henry Davis'),
    ('CS009', 'Ivy Chen'),
    ('CS010', 'Jack Thompson'),
    ('CS011', 'Karen White'),
    ('CS012', 'Leo Martinez')
ON CONFLICT (roll_number) DO NOTHING;

-- 7. Create a view for attendance summary
CREATE OR REPLACE VIEW attendance_summary AS
SELECT 
    s.roll_number,
    s.name,
    a.date,
    a.status,
    a.timestamp
FROM students s
LEFT JOIN attendance a ON s.roll_number = a.roll_number
ORDER BY s.roll_number, a.date DESC;

-- 8. Create function to get attendance statistics for a date
CREATE OR REPLACE FUNCTION get_attendance_stats(target_date DATE DEFAULT CURRENT_DATE)
RETURNS TABLE (
    total_students INTEGER,
    present_count INTEGER,
    absent_count INTEGER,
    not_marked_count INTEGER,
    attendance_percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM students) as total_students,
        (SELECT COUNT(*)::INTEGER FROM attendance WHERE date = target_date AND status = 'present') as present_count,
        (SELECT COUNT(*)::INTEGER FROM attendance WHERE date = target_date AND status = 'absent') as absent_count,
        (SELECT COUNT(*)::INTEGER FROM students s 
         WHERE NOT EXISTS (SELECT 1 FROM attendance a WHERE a.roll_number = s.roll_number AND a.date = target_date)
        ) as not_marked_count,
        CASE 
            WHEN (SELECT COUNT(*) FROM students) = 0 THEN 0
            ELSE ROUND(
                (SELECT COUNT(*)::NUMERIC FROM attendance WHERE date = target_date AND status = 'present') * 100.0 / 
                (SELECT COUNT(*) FROM students), 2
            )
        END as attendance_percentage;
END;
$$ LANGUAGE plpgsql;

-- 9. Create function to clean up duplicate attendance records (if any exist)
CREATE OR REPLACE FUNCTION clean_duplicate_attendance()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Delete duplicate records, keeping only the latest one for each student-date combination
    WITH ranked_attendance AS (
        SELECT id, 
               ROW_NUMBER() OVER (PARTITION BY roll_number, date ORDER BY timestamp DESC) as rn
        FROM attendance
    )
    DELETE FROM attendance 
    WHERE id IN (
        SELECT id FROM ranked_attendance WHERE rn > 1
    );
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 10. Enable Row Level Security (optional - uncomment if needed)
-- ALTER TABLE students ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;

-- Create policies for RLS (optional - uncomment and modify as needed)
-- CREATE POLICY "Students are viewable by everyone" ON students FOR SELECT USING (true);
-- CREATE POLICY "Students are insertable by everyone" ON students FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Students are updatable by everyone" ON students FOR UPDATE USING (true);
-- CREATE POLICY "Students are deletable by everyone" ON students FOR DELETE USING (true);

-- CREATE POLICY "Attendance is viewable by everyone" ON attendance FOR SELECT USING (true);
-- CREATE POLICY "Attendance is insertable by everyone" ON attendance FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Attendance is updatable by everyone" ON attendance FOR UPDATE USING (true);
-- CREATE POLICY "Attendance is deletable by everyone" ON attendance FOR DELETE USING (true);

-- 11. Grant necessary permissions (adjust as needed)
-- GRANT ALL ON students TO anon, authenticated;
-- GRANT ALL ON attendance TO anon, authenticated;
-- GRANT USAGE ON SEQUENCE students_id_seq TO anon, authenticated;
-- GRANT USAGE ON SEQUENCE attendance_id_seq TO anon, authenticated;

-- 12. Create Student Marks Table
CREATE TABLE IF NOT EXISTS student_marks (
    id SERIAL PRIMARY KEY,
    student_roll_number TEXT NOT NULL,
    subject TEXT NOT NULL,
    marks REAL, -- Using REAL for marks to allow for decimal values
    exam_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    FOREIGN KEY (student_roll_number) REFERENCES students(roll_number) ON DELETE CASCADE,
    UNIQUE(student_roll_number, subject, exam_date) -- Ensure a student has unique marks for a subject on a specific exam_date
);

-- 13. Create indexes for student_marks table
CREATE INDEX IF NOT EXISTS idx_student_marks_roll_number ON student_marks(student_roll_number);
CREATE INDEX IF NOT EXISTS idx_student_marks_subject ON student_marks(subject);
CREATE INDEX IF NOT EXISTS idx_student_marks_exam_date ON student_marks(exam_date);

-- 14. Create trigger for student_marks updated_at
DROP TRIGGER IF EXISTS update_student_marks_updated_at ON student_marks;
CREATE TRIGGER update_student_marks_updated_at
    BEFORE UPDATE ON student_marks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Adjust sequence permissions if RLS is used for the new table
-- GRANT USAGE ON SEQUENCE student_marks_id_seq TO anon, authenticated;

-- Verification queries - run these to check your setup
-- SELECT * FROM students LIMIT 5;
-- SELECT * FROM attendance LIMIT 5;
-- SELECT * FROM student_marks LIMIT 5;
-- SELECT * FROM get_attendance_stats();
-- SELECT clean_duplicate_attendance(); -- This will clean any existing duplicates