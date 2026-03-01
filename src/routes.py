"""
Route handlers for Novo application
"""

from flask import request, render_template, jsonify, redirect, url_for, current_app, session, flash
from werkzeug.utils import secure_filename
import os
import stripe
from datetime import datetime, timezone
from src.services.hunter import find_and_save_matches
from src.services.db import _get_supabase_client, set_student_premium, is_user_premium
from src.services.auth import (
    register_user, 
    login_user, 
    logout_user, 
    login_required,
    is_authenticated,
    get_current_user
)

# Stripe Configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PRICE_ID = os.getenv('STRIPE_PRICE_ID')

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
        
    @app.route('/confirmacion-exitosa')
    def confirmacion_exitosa():
        """Public route for successful account confirmation"""
        return render_template('confirmacion_auth.html')
    
    # =====================
    # Protected Routes
    # =====================
    
    @app.route('/my-profiles')
    @login_required
    def my_profiles():
        """Display all profiles for the current user"""
        from src.services.db import get_student_profiles_by_user
        
        user = get_current_user()
        profiles = get_student_profiles_by_user(user['id'])
        is_premium = is_user_premium(user['id'])
        
        return render_template('my_profiles.html', profiles=profiles, user=user, is_premium=is_premium)
    
    @app.route('/profile', methods=['GET'])
    @login_required
    def profile():
        """Render the profile page with file upload form"""
        from src.services.db import get_latest_student_profile_by_user
        
        user = get_current_user()
        is_premium = is_user_premium(user['id'])
        # Check if the user has an existing profile
        latest_profile = get_latest_student_profile_by_user(user['id'])
        
        if latest_profile:
            return render_template('profile_view.html', user=user, latest_profile=latest_profile, is_premium=is_premium)
            
        return render_template('profile.html', user=user, is_premium=is_premium)
    
    @app.route('/profile', methods=['POST'])
    @login_required
    def upload_profile():
        """Handle profile upload (CV PDF and optional audio brain dump)"""
        import tempfile
        
        cv_path = None
        audio_path = None
        
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
            
            # Use temporary files for Vercel (serverless)
            cv_suffix = '.pdf'
            cv_fd, cv_path = tempfile.mkstemp(suffix=cv_suffix)
            os.close(cv_fd)  # Close file descriptor
            cv_file.save(cv_path)
            
            cv_filename = secure_filename(cv_file.filename)
            
            # Handle brain dump - either text OR recorded audio (mutually exclusive)
            brain_dump_text = request.form.get('brain_dump_text', '').strip()
            audio_file = request.files.get('audio_file')
            
            # Check if we have recorded audio (from microphone)
            if audio_file and audio_file.filename != '':
                # Get content type to determine extension
                content_type = audio_file.content_type or 'audio/webm'
                ext_map = {
                    'audio/webm': '.webm',
                    'audio/mp4': '.mp4',
                    'audio/mpeg': '.mp3',
                    'audio/wav': '.wav',
                    'audio/ogg': '.ogg',
                    'audio/x-m4a': '.m4a'
                }
                audio_ext = ext_map.get(content_type, '.webm')
                
                audio_fd, audio_path = tempfile.mkstemp(suffix=audio_ext)
                os.close(audio_fd)
                audio_file.save(audio_path)
                # Clear text since audio takes precedence
                brain_dump_text = None
            
            # Import and call AI agent analyzer
            from src.services.ai_agent import analyze_profile
            from src.services.db import save_student_profile
            
            # Get current user
            user = get_current_user()
            
            # Analyze profile with either audio or text brain dump
            # Returns (profile_dict, cv_raw_text) tuple
            result, cv_raw_text = analyze_profile(cv_path, audio_path, brain_dump_text)
            
            # Clean up temporary files immediately after processing
            try:
                if cv_path and os.path.exists(cv_path):
                    os.unlink(cv_path)
                if audio_path and os.path.exists(audio_path):
                    os.unlink(audio_path)
            except Exception as cleanup_error:
                print(f"Warning: Failed to cleanup temp files: {cleanup_error}")

            # Persist result to Supabase with user_id + raw texts
            saved_row = save_student_profile(
                result, 
                user_id=user['id'] if user else None,
                cv_raw_text=cv_raw_text,
                brain_dump_text=brain_dump_text or ""
            )
            session["student_row"] = saved_row
            
            # Store result in session for results page
            session['analysis_result'] = result
            session['cv_filename'] = cv_filename
            
            # Redirect to results page
            return redirect(url_for('results'))
            
        except Exception as e:
            # Clean up temp files on error
            try:
                if cv_path and os.path.exists(cv_path):
                    os.unlink(cv_path)
                if audio_path and os.path.exists(audio_path):
                    os.unlink(audio_path)
            except:
                pass
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
        is_premium = is_user_premium(user['id'])
        
        # Verificar que el student_row pertenece al usuario actual
        if student_row and student_row.get('user_id') != user['id']:
            # Si el perfil no pertenece al usuario, limpiar sesión y redirigir
            session.pop('analysis_result', None)
            session.pop('student_row', None)
            return redirect(url_for('profile'))
        
        return render_template('results.html', result=result, cv_filename=cv_filename, student_row=student_row, user=user, is_premium=is_premium)



    
    @app.route('/profile/edit/<student_id>', methods=['GET', 'POST'])
    @login_required
    def edit_profile(student_id):
        """Edit profile (top_skills and ambitions)"""
        try:
            from src.services.db import get_student_profile_by_id, update_student_profile_data
            
            user = get_current_user()
            
            # Verify ownership
            profile = get_student_profile_by_id(student_id, user['id'])
            if not profile:
                 flash("No tienes permiso para editar este perfil.", "error")
                 return redirect(url_for('profile'))
            
            if request.method == 'POST':
                # Get data from form
                top_skills_raw = request.form.get('top_skills', '')
                ambitions = request.form.get('ambitions', '')
                
                # Process skills (comma separated to list)
                top_skills = [s.strip() for s in top_skills_raw.split(',') if s.strip()]
                
                # Update existing profile_data
                current_profile_data = profile.get('profile_data', {})
                current_profile_data['top_skills'] = top_skills
                current_profile_data['ambitions'] = ambitions

                # Call update service
                if update_student_profile_data(student_id, current_profile_data, user['id']):
                    flash("Perfil actualizado correctamente.", "success")
                    return redirect(url_for('profile'))
                else:
                    flash("Error al actualizar el perfil.", "error")
            
            is_premium = is_user_premium(user['id'])
            return render_template('profile_edit.html', profile=profile, is_premium=is_premium, user=user)
            
        except Exception as e:
            print(f"Error in edit_profile: {e}")
            flash("Ocurrió un error inesperado.", "error")
            return redirect(url_for('profile'))

    @app.route('/dashboard/<student_id>')

    @login_required
    def dashboard(student_id):
        """Display matches dashboard for a student"""
        try:
            from src.services.db import get_matches_for_student, get_student_profile_by_id
            
            user = get_current_user()
            
            # Verificar que el perfil pertenece al usuario y obtener matches
            student_profile = get_student_profile_by_id(student_id, user['id'])
            
            if not student_profile:
                return jsonify({'error': 'No tienes permiso para acceder a este perfil'}), 403
            
            # Obtener matches del estudiante
            matches = get_matches_for_student(student_id, user['id'])
            is_premium = is_user_premium(user['id'])
            
            return render_template('matches.html', matches=matches, student_id=student_id, user=user, student_profile=student_profile, is_premium=is_premium)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


    # === RUTAS DE PAGO Y SUSCRIPCIÓN ===

    @app.route('/upgrade')
    @app.route('/upgrade/<student_id>')
    @login_required
    def upgrade(student_id=None):
        """Muestra la página de upgrade a Pro (Fake Door)"""
        user = session.get("user")
        
        # Si no hay student_id, intentar obtenerlo de la sesión
        if not student_id:
            student_row = session.get("student_row")
            student_id = student_row.get('id') if student_row else None
        
        # Calcular búsquedas del día para mostrar al usuario
        searches_today = 0
        search_limit = 20
        if student_id:
            from datetime import datetime, timezone
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            
            supabase = _get_supabase_client()
            searches_result = supabase.table("matches").select("id", count="exact").eq("student_id", student_id).gte("created_at", today_start).execute()
            searches_today = searches_result.count if searches_result.count else 0
        
        # Calcular porcentaje para la barra de progreso (evita división por cero)
        progress_percentage = (searches_today / search_limit * 100) if search_limit > 0 else 0
        
        return render_template('upgrade.html', 
                             user=user, 
                             student_id=student_id,
                             searches_today=searches_today,
                             search_limit=search_limit,
                             progress_percentage=progress_percentage)

    @app.route('/checkout', methods=['POST', 'GET'])
    @app.route('/checkout/<student_id>', methods=['POST', 'GET'])
    @login_required
    def checkout(student_id=None):
        """Crea sesión de Checkout en Stripe"""
        try:
            # Obtener el student_id
            if not student_id:
                student_row = session.get("student_row")
                student_id = student_row.get('id') if student_row else None

            if not student_id:
                return redirect(url_for('profile'))

            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                    'price': STRIPE_PRICE_ID,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=url_for('premium_activation', student_id=student_id, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=url_for('dashboard', student_id=student_id, _external=True),
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            return str(e)

    @app.route('/premium-activation/<student_id>')
    def premium_activation(student_id):
        """Página de éxito estilo 'Concierge'"""
        
        # Validar pago con Stripe (opcional pero recomendado)
        # Activar flag en DB
        set_student_premium(student_id, True)
        
        return render_template('premium_activation.html', email=session.get('user', {}).get('email', 'tu correo'))

    # === RUTAS EXISTENTES MODIFICADAS ===

    @app.route('/test-hunter/<student_id>')
    @login_required
    def run_hunter(student_id):
        try:
            from src.services.db import verify_student_ownership, get_student_usage_info, update_last_search_date
            
            user = get_current_user()
            if not verify_student_ownership(student_id, user['id']):
                return jsonify({'error': 'Permiso denegado'}), 403
            
            # --- LÓGICA FREEMIUM ---
            usage = get_student_usage_info(student_id)
            is_premium = usage['is_premium']
            
            # Determinar límite y contar búsquedas de hoy
            if is_premium:
                limit = 3 # O más para Premium
            else:
                # Contar búsquedas realizadas hoy (desde medianoche UTC)
                from datetime import datetime, timezone
                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                
                supabase = _get_supabase_client()
                searches_today = supabase.table("matches").select("id", count="exact").eq("student_id", student_id).gte("created_at", today_start).execute()
                count_today = searches_today.count if searches_today.count else 0
                
                # Límite: 20 búsquedas por día para usuarios gratuitos
                if count_today >= 20:
                    # Ya alcanzó el límite -> Fake Door Upgrade
                    return redirect(url_for('upgrade', student_id=student_id))
                
                limit = 20 # Usuario Gratis: 20 búsquedas por día
            # ------------------------

            find_and_save_matches(student_id, num_results=limit)
            
            # Actualizar timestamp
            update_last_search_date(student_id)
            
            return redirect(url_for('dashboard', student_id=student_id))
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500