#!/usr/bin/env python3

import sys
import os

# Add your project directory to the Python path
project_home = '/home/yourusername/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import your Flask app
from run import app as application

if __name__ == "__main__":
    application.run()