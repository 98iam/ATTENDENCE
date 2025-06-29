# 🚀 Deployment Guide - Attendance System

## 📋 Quick Start After Cloning

When you clone this repository, follow these steps for immediate setup:

### 1. Clone and Setup
```bash
git clone https://github.com/98iam/ATTENDENCE.git
cd ATTENDENCE
chmod +x setup.sh
./setup.sh
```

### 2. Database Configuration
1. **Update your Supabase credentials in `app/config.py`:**
```python
SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"
```

2. **Set up database schema:**
   - Go to Supabase Dashboard → SQL Editor
   - Copy content from `supabase_schema.sql`
   - Run the SQL script

### 3. Initialize and Test
```bash
# Test the setup
python test_setup.py

# Start the application
python run.py
```

### 4. Access the Application
- **Main App:** http://localhost:5000
- **Dashboard:** http://localhost:5000/dashboard
- **Admin Panel:** http://localhost:5000/admin

---

**Ready to use! 🚀**