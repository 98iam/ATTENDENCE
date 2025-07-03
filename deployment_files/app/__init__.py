from flask import Flask
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY
from datetime import datetime

app = Flask(__name__)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Add custom filters
@app.template_filter('strptime')
def strptime_filter(date_string, fmt='%Y-%m-%d'):
    """Convert string to datetime object"""
    try:
        return datetime.strptime(date_string, fmt)
    except:
        return datetime.now()

@app.template_filter('format_datetime')
def format_datetime_filter(datetime_string):
    """Format datetime string for display"""
    try:
        if 'T' in datetime_string:
            dt = datetime.fromisoformat(datetime_string.replace('Z', '+00:00'))
            return dt.strftime('%I:%M %p')
        return datetime_string
    except:
        return 'N/A'

from app import routes
