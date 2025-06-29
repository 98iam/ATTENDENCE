#!/bin/bash

# 🎓 Attendance System - Quick Setup Script
# This script sets up the attendance system after cloning

echo "🎓 Setting up Attendance System..."
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🛠️  IMPORTANT SETUP STEPS:"
echo "=========================="
echo ""
echo "1. 🗄️  DATABASE SETUP (REQUIRED):"
echo "   - Go to your Supabase project dashboard"
echo "   - Navigate to SQL Editor"
echo "   - Copy and paste the content from: supabase_schema.sql"
echo "   - Run the SQL script"
echo ""
echo "2. ⚙️  CONFIGURATION:"
echo "   - Update app/config.py with your Supabase URL and API key"
echo ""  
echo "3. 🧪 VERIFY SETUP:"
echo "   - Run: python test_setup.py"
echo ""
echo "4. 🚀 START APPLICATION:"
echo "   - Run: python run.py"
echo "   - Open: http://localhost:5000"
echo "   - Admin: http://localhost:5000/admin"
echo ""
echo "📝 OR use the automated database setup:"
echo "   - Run: python init_database.py"
echo ""
echo "✨ Setup completed! Follow the steps above to finish configuration."