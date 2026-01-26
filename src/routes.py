"""
Route handlers for Novo application
"""

from flask import request, render_template, jsonify, redirect, url_for, current_app, session, flash
from werkzeug.utils import secure_filename
import os
from src.services.hunter import find_and_save_matches
from src.services.db import _get_supabase_client
from src.services.auth import (
    register_user, 
    login_user, 
    logout_user, 
    login_required,
    is_authenticated,
    get_current_user
)

ALLOWED_EXTENSIONS = {
    'pdf': {'pdf'},
    'audio': {'mp3', 'wav', 'm4a', 'ogg'}
}

def allowed_file(filename, file_type='pdf'):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(file_type, set())

def init_routes(app):
    """Initialize routes for the Flask app"""
    
    @app.route('/')
    def index():
        """Home page - redirect based on authentication"""
        if is_authenticated():
            return redirect(url_for('profile'))
        return redirect(url_for('login'))
    
    # =====================
    # Authentication Routes
    # =====================
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration page"""
        # Redirect if already logged in
        if is_authenticated():
            return redirect(url_for('profile'))
            
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            password_confirm = request.form.get('password_confirm')
            full_name = request.form.get('full_name')
            
            # Validate passwords match
            if password != password_confirm:
                return render_template('register.html', error='Las contraseñas no coinciden')
            
            # Register user
            result = register_user(email, password, full_name)
            
            if result['success']:
                return render_template('login.html', success=result['message'])
            else:
                return render_template('register.html', error=result['error'])
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login page"""
        # Redirect if already logged in
        if is_authenticated():
            return redirect(url_for('profile'))
            
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Attempt login
            result = login_user(email, password)
            
            if result['success']:
                return redirect(url_for('profile'))
            else:
                return render_template('login.html', error=result.get('error', 'Credenciales inválidas'))
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """Log out the current user"""
        logout_user()
        return redirect(url_for('login'))
    
    # =====================
    # Protected Routes
    # =====================
    
    @app.route('/profile', methods=['GET'])
    @login_required
    def profile():
        """Render the profile page with file upload form"""
        user = get_current_user()
        return render_template('profile.html', user=user)
    
    @app.route('/profile', methods=['POST'])
    @login_required
    def upload_profile():
        """Handle profile upload (CV PDF and optional audio brain dump)"""
        try:
            # Check if CV file is present
            if 'cv_file' not in request.files:
                return jsonify({'error': 'CV file is required'}), 400
            
            cv_file = request.files['cv_file']
            
            # Check if CV file is selected
            if cv_file.filename == '':
                return jsonify({'error': 'No CV file selected'}), 400
            
            # Validate CV file type
            if not allowed_file(cv_file.filename, 'pdf'):
                return jsonify({'error': 'CV must be a PDF file'}), 400
            
            # Secure CV filename
            cv_filename = secure_filename(cv_file.filename)
            cv_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cv_filename)
            cv_file.save(cv_path)
            
            # Handle optional audio file
            audio_path = None
            audio_file = request.files.get('audio_file')
            
            if audio_file and audio_file.filename != '':
                # Validate audio file type
                if not allowed_file(audio_file.filename, 'audio'):
                    return jsonify({'error': 'Audio must be mp3, wav, m4a, or ogg'}), 400
                
                audio_filename = secure_filename(audio_file.filename)
                audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], audio_filename)
                audio_file.save(audio_path)
            
            # Import and call AI agent analyzer
            from src.services.ai_agent import analyze_profile
            from src.services.db import save_student_profile
            
            # Get current user
            user = get_current_user()
            
            # Analyze profile
            result = analyze_profile(cv_path, audio_path)

            # Persist result to Supabase with user_id
            saved_row = save_student_profile(result, user_id=user['id'] if user else None)
            session["student_row"] = saved_row
            
            # Store result in session for results page
            session['analysis_result'] = result
            session['cv_filename'] = cv_filename
            
            # Redirect to results page
            return redirect(url_for('results'))
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/results', methods=['GET'])
    @login_required
    def results():
        """Display analysis results"""
        result = session.get('analysis_result')
        cv_filename = session.get('cv_filename')
        student_row = session.get("student_row")
        
        if not result:
            return redirect(url_for('profile'))
        
        user = get_current_user()
        return render_template('results.html', result=result, cv_filename=cv_filename, student_row=student_row, user=user)

    @app.route('/test-hunter/<student_id>')
    @login_required
    def run_hunter(student_id):
        try:
            # 1. Run the Hunter logic
            find_and_save_matches(student_id)
            
            # 2. Redirect to the Dashboard immediately!
            return redirect(url_for('dashboard', student_id=student_id))
            
        except Exception as e:
            return f"Error running hunter: {str(e)}"
    
    @app.route('/dashboard/<student_id>')
    @login_required
    def dashboard(student_id):
        """Display matches dashboard for a student"""
        try:
            user = get_current_user()
            supabase = _get_supabase_client()
            response = supabase.table("matches").select("*").eq("student_id", student_id).execute()
            matches = response.data
            return render_template('matches.html', matches=matches, student_id=student_id, user=user)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
