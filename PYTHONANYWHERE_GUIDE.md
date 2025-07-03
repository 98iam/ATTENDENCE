# PythonAnywhere Deployment Guide

## Step 1: Sign Up
1. Go to https://pythonanywhere.com
2. Click "Create a Beginner account" (FREE)
3. Sign up with your email

## Step 2: Upload Your Files
1. Go to "Files" tab in your dashboard
2. Click "Upload a file"
3. Upload these files:
   - app/ folder (entire folder)
   - run.py
   - wsgi.py
   - requirements.txt
   - students_data.csv
   - All other files from your project

## Step 3: Create Web App
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Flask"
4. Choose Python 3.8 or 3.9
5. Set source code path to: /home/yourusername/mysite
6. Set WSGI file path to: /home/yourusername/mysite/wsgi.py

## Step 4: Install Requirements
1. Go to "Consoles" tab
2. Start a "Bash" console
3. Run: pip3.8 install --user -r requirements.txt

## Step 5: Configure WSGI
1. Edit the WSGI file and change "yourusername" to your actual username
2. Save the file

## Step 6: Reload
1. Go back to "Web" tab
2. Click "Reload yourusername.pythonanywhere.com"

Your app will be live at: https://yourusername.pythonanywhere.com