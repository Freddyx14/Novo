"""
Novo - Hyper-personalized Career Agent for University Students
Main Flask application entry point
"""

from flask import Flask
from dotenv import load_dotenv
import os
import tempfile

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# Use temp directory for Vercel (serverless)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Import and initialize routes
from src.routes import init_routes
init_routes(app)

# For local development only
if __name__ == '__main__':
    # Use uploads folder for local dev
    os.makedirs('uploads', exist_ok=True)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.run(debug=True, host='0.0.0.0', port=5000)

