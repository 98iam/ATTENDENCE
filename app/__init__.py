from flask import Flask
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY

app = Flask(__name__)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

from app import routes
