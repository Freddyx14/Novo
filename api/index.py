import sys
import os
import traceback
from flask import Flask

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# Top-level app declaration so Vercel can find it
app = None

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(root_dir, '.env'))
    from app import app as _app
    app = _app
except Exception as e:
    error_msg = traceback.format_exc()
    app = Flask(__name__)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all_error(path):
        return f"""
        <html>
            <body style="font-family: monospace; padding: 20px; background: #FFF0F0;">
                <h1 style="color: #D8000C;">Error de Importación</h1>
                <pre>{error_msg}</pre>
            </body>
        </html>
        """
