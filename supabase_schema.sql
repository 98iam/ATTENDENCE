-- Attendance System Database Schema for Supabase
-- Run this SQL in your Supabase SQL Editor to set up the proper database structure

-- 1. Create or update the Students Table
DO $$ 
BEGIN
    -- Create the students table if it doesn't exist
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        roll_number TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Add columns if they don't exist
    BEGIN
        ALTER TABLE students 
        ADD COLUMN IF NOT EXISTS roll_number TEXT UNIQUE;
    EXCEPTION WHEN duplicate_column THEN
        -- Column already exists, do nothing
    END;
END $$;

-- 2. Create or update the Attendance Table
DO $$ 
BEGIN
    -- Create the attendance table if it doesn't exist
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        roll_number TEXT NOT NULL,
        date DATE NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('present', 'absent')),
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Add foreign key if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'attendance_roll_number_fkey'
    ) THEN
        ALTER TABLE attendance
        ADD CONSTRAINT attendance_roll_number_fkey 
        FOREIGN KEY (roll_number) REFERENCES students(roll_number) ON DELETE CASCADE;
    END IF;

    -- Add unique constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'attendance_roll_number_date_key'
    ) THEN
        ALTER TABLE attendance
        ADD CONSTRAINT attendance_roll_number_date_key 
        UNIQUE(roll_number, date);
    END IF;
END $$;

-- 3. Create or update indexes
DO $$ 
BEGIN
    -- Create indexes if they don't exist
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_attendance_roll_number') THEN
        CREATE INDEX idx_attendance_roll_number ON attendance(roll_number);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_attendance_date') THEN
        CREATE INDEX idx_attendance_date ON attendance(date);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_attendance_roll_date') THEN
        CREATE INDEX idx_attendance_roll_date ON attendance(roll_number, date);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_students_roll_number') THEN
        CREATE INDEX idx_students_roll_number ON students(roll_number);
    END IF;
END $$;

-- 4. Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 5. Create or update triggers
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

-- 6. Create or update the Student Marks Table
DO $$ 
BEGIN
    -- Create the student_marks table if it doesn't exist with minimal structure
    CREATE TABLE IF NOT EXISTS student_marks (
        id SERIAL PRIMARY KEY,
        roll_number TEXT NOT NULL,
        date DATE NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Add missing columns if they don't exist
    BEGIN
        ALTER TABLE student_marks ADD COLUMN IF NOT EXISTS subject TEXT NOT NULL DEFAULT 'default_subject';
    EXCEPTION WHEN duplicate_column THEN
        -- Column already exists, do nothing
    END;

    BEGIN
        ALTER TABLE student_marks ADD COLUMN IF NOT EXISTS marks REAL;
    EXCEPTION WHEN duplicate_column THEN
        -- Column already exists, do nothing
    END;

    BEGIN
        ALTER TABLE student_marks ADD COLUMN IF NOT EXISTS exam_date DATE;
    EXCEPTION WHEN duplicate_column THEN
        -- Column already exists, do nothing
    END;

    -- Remove the default value from subject column after creation
    ALTER TABLE student_marks ALTER COLUMN subject DROP DEFAULT;

    -- Add foreign key if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'student_marks_roll_number_fkey'
    ) THEN
        ALTER TABLE student_marks
        ADD CONSTRAINT student_marks_roll_number_fkey 
        FOREIGN KEY (roll_number) REFERENCES students(roll_number) ON DELETE CASCADE;
    END IF;

    -- Add unique constraint only after ensuring all required columns exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'student_marks_roll_number_subject_exam_date_key'
    ) AND EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'student_marks' 
        AND column_name IN ('roll_number', 'subject', 'exam_date')
    ) THEN
        ALTER TABLE student_marks
        ADD CONSTRAINT student_marks_roll_number_subject_exam_date_key 
        UNIQUE(roll_number, subject, exam_date);
    END IF;
END $$;

-- 7. Create indexes for student_marks table
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_student_marks_roll_number') THEN
        CREATE INDEX idx_student_marks_roll_number ON student_marks(roll_number);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_student_marks_subject') 
    AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'student_marks' AND column_name = 'subject'
    ) THEN
        CREATE INDEX idx_student_marks_subject ON student_marks(subject);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_student_marks_exam_date')
    AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'student_marks' AND column_name = 'exam_date'
    ) THEN
        CREATE INDEX idx_student_marks_exam_date ON student_marks(exam_date);
    END IF;
END $$;

-- 8. Create trigger for student_marks updated_at
DROP TRIGGER IF EXISTS update_student_marks_updated_at ON student_marks;
CREATE TRIGGER update_student_marks_updated_at
    BEFORE UPDATE ON student_marks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 9. Create attendance_summary view
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

-- 10. Create attendance stats function
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

-- 11. Create function to clean up duplicate attendance records
CREATE OR REPLACE FUNCTION clean_duplicate_attendance()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
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
