import sys
import os

# Add your project directory to the sys.path
project_home = u'/home/YOUR_USERNAME/public_html/flask_app'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables
os.environ['PYTHON_EGG_CACHE'] = '/home/Atharva_Patil/.python-eggs'
os.environ['FLASK_ENV'] = 'production'

# Import flask app but need to call it "application" for WSGI to work
from app import app as application  # Change "app" to the name of your main file if it's different
