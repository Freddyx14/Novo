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
    get_current_user,
    request_password_reset,
    store_recovery_session,
    has_recovery_session,
    complete_password_reset
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

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        """Request a password reset email."""
        if is_authenticated():
            return redirect(url_for('profile'))

        if request.method == 'POST':
            email = (request.form.get('email') or '').strip().lower()

            if not email:
                return render_template('forgot_password.html', error='Ingresa tu correo electrónico')

            redirect_to = url_for('reset_password', _external=True)
            result = request_password_reset(email, redirect_to)

            if result['success']:
                return render_template('forgot_password.html', success=result['message'])

            return render_template('forgot_password.html', error=result['error'])

        return render_template('forgot_password.html')

    @app.route('/reset-password', methods=['GET', 'POST'])
    def reset_password():
        """Allow users to set a new password after following the recovery email."""
        if is_authenticated():
            return redirect(url_for('profile'))

        if request.method == 'POST':
            password = request.form.get('password') or ''
            password_confirm = request.form.get('password_confirm') or ''

            if not has_recovery_session():
                return render_template(
                    'reset_password.html',
                    error='Tu enlace de recuperación no es válido o expiró. Vuelve a solicitar uno nuevo.',
                    recovery_ready=False,
                )

            if len(password) < 6:
                return render_template(
                    'reset_password.html',
                    error='La contraseña debe tener al menos 6 caracteres',
                    recovery_ready=True,
                )

            if password != password_confirm:
                return render_template(
                    'reset_password.html',
                    error='Las contraseñas no coinciden',
                    recovery_ready=True,
                )

            result = complete_password_reset(password)

            if result['success']:
                return render_template('login.html', success=result['message'])

            return render_template('reset_password.html', error=result['error'], recovery_ready=has_recovery_session())

        return render_template('reset_password.html', recovery_ready=has_recovery_session())

    @app.route('/reset-password/session', methods=['POST'])
    def reset_password_session():
        """Store recovery tokens from the email redirect in the Flask session."""
        data = request.get_json(silent=True) or {}
        access_token = (data.get('access_token') or '').strip()
        refresh_token = (data.get('refresh_token') or '').strip()

        if not access_token or not refresh_token:
            return jsonify({'success': False, 'error': 'Faltan tokens de recuperación'}), 400

        try:
            supabase = _get_supabase_client()
            supabase.auth.set_session(access_token, refresh_token)
            store_recovery_session(access_token, refresh_token)
            return jsonify({'success': True, 'message': 'Sesión de recuperación validada'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        
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
        import shutil
        from datetime import datetime
        
        cv_path = None
        audio_path = None
        cv_permanent_path = None
        
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
            
            # Save PDF permanently in uploads/cvs/user_id/
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            user_cv_dir = os.path.join('uploads', 'cvs', user['id'])
            os.makedirs(user_cv_dir, exist_ok=True)
            cv_permanent_filename = f"{timestamp}_{cv_filename}"
            cv_permanent_path = os.path.join(user_cv_dir, cv_permanent_filename)
            
            # Copy file to permanent location
            shutil.copy2(cv_path, cv_permanent_path)
            print(f"CV saved permanently at: {cv_permanent_path}")
            
            # Analyze profile with either audio or text brain dump
            # Returns (profile_dict, cv_raw_text) tuple
            result, cv_raw_text = analyze_profile(cv_path, audio_path, brain_dump_text)
            
            # Add CV file path to result
            result['cv_file_path'] = cv_permanent_path
            
            # Clean up temporary files immediately after processing
            try:
                if cv_path and os.path.exists(cv_path):
                    os.unlink(cv_path)
                if audio_path and os.path.exists(audio_path):
                    os.unlink(audio_path)
            except Exception as cleanup_error:
                print(f"Warning: Failed to cleanup temp files: {cleanup_error}")

            # Persist result to Supabase with user_id + raw texts + cv_file_path
            saved_row = save_student_profile(
                result, 
                user_id=user['id'] if user else None,
                cv_raw_text=cv_raw_text,
                brain_dump_text=brain_dump_text or "",
                cv_file_path=cv_permanent_path
            )
            
            # Clean up matches from old profiles to avoid mixing results
            from src.services.db import delete_old_matches_for_user
            delete_old_matches_for_user(user['id'], saved_row['id'])
            print(f"Cleaned up old matches for user {user['id']}, keeping matches for profile {saved_row['id']}")
            
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
        """Edit profile (top_skills, ambitions, and optionally CV)"""
        try:
            from src.services.db import get_student_profile_by_id, update_student_profile_data
            from src.services.ai_agent import GeminiAgent
            import os
            from werkzeug.utils import secure_filename
            
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

                # Handle CV upload (optional)
                cv_raw_text = profile.get('cv_raw_text', '')  # Keep existing by default
                cv_permanent_path = profile.get('profile_data', {}).get('cv_file_path', '')
                cv_file = request.files.get('cv_file')
                
                if cv_file and cv_file.filename:
                    # Validate file
                    if not cv_file.filename.endswith('.pdf'):
                        flash("Solo se permiten archivos PDF.", "error")
                        return redirect(url_for('edit_profile', student_id=student_id))
                    
                    # Save file temporarily
                    filename = secure_filename(cv_file.filename)
                    temp_cv_path = os.path.join('uploads', f"temp_{user['id']}_{filename}")
                    os.makedirs('uploads', exist_ok=True)
                    cv_file.save(temp_cv_path)
                    
                    try:
                        # Extract text from new CV
                        agent = GeminiAgent()
                        cv_raw_text = agent.extract_cv_text(temp_cv_path)
                        print(f"New CV extracted: {len(cv_raw_text)} chars")
                        
                        # Save PDF permanently BEFORE deleting temp file
                        from datetime import datetime
                        import shutil
                        
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        user_cv_dir = os.path.join('uploads', 'cvs', user['id'])
                        os.makedirs(user_cv_dir, exist_ok=True)
                        cv_filename_secure = secure_filename(cv_file.filename)
                        cv_permanent_filename = f"{timestamp}_{cv_filename_secure}"
                        cv_permanent_path = os.path.join(user_cv_dir, cv_permanent_filename)
                        
                        # Copy temp file to permanent location
                        shutil.copy2(temp_cv_path, cv_permanent_path)
                        print(f"CV updated and saved at: {cv_permanent_path}")
                        
                    except Exception as e:
                        print(f"Error extracting/saving CV: {e}")
                        import traceback
                        traceback.print_exc()
                        flash("Error al procesar el CV. Inténtalo de nuevo.", "error")
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_cv_path):
                            os.remove(temp_cv_path)

                # Call update service with new CV text (if updated)
                from src.services.db import _get_supabase_client
                supabase = _get_supabase_client()
                
                # Add cv_file_path to profile_data
                if cv_permanent_path:
                    current_profile_data['cv_file_path'] = cv_permanent_path
                
                update_data = {
                    'profile_data': current_profile_data,
                    'cv_raw_text': cv_raw_text
                }
                
                result = supabase.table('students').update(update_data).eq('id', student_id).eq('user_id', user['id']).execute()
                
                if result.data:
                    # If CV was updated, clear old matches since profile has changed significantly
                    if cv_file and cv_file.filename:
                        try:
                            supabase.table('matches').delete().eq('student_id', student_id).execute()
                            print(f"Cleared matches for updated profile: {student_id}")
                        except Exception as e:
                            print(f"Error clearing matches after profile update: {e}")
                    
                    flash("Perfil actualizado correctamente.", "success")
                    return redirect(url_for('profile'))
                else:
                    flash("Error al actualizar el perfil.", "error")
            
            is_premium = is_user_premium(user['id'])
            return render_template('profile_edit.html', profile=profile, is_premium=is_premium, user=user)
            
        except Exception as e:
            print(f"Error in edit_profile: {e}")
            import traceback
            traceback.print_exc()
            flash("Ocurrió un error inesperado.", "error")
            return redirect(url_for('profile'))

    @app.route('/cv/<student_id>')
    @login_required
    def serve_cv(student_id):
        """Serve CV PDF file"""
        try:
            from src.services.db import get_student_profile_by_id
            from flask import send_file
            
            user = get_current_user()
            
            # Verify ownership
            profile = get_student_profile_by_id(student_id, user['id'])
            if not profile:
                return "CV no encontrado o no tienes permiso", 404
            
            # Get CV file path from profile_data
            cv_file_path = profile.get('profile_data', {}).get('cv_file_path')
            
            if not cv_file_path or not os.path.exists(cv_file_path):
                return "CV no disponible", 404
            
            # Serve the PDF file
            return send_file(cv_file_path, mimetype='application/pdf')
            
        except Exception as e:
            print(f"Error serving CV: {e}")
            import traceback
            traceback.print_exc()
            return "Error al cargar CV", 500

    @app.route('/cv/delete/<student_id>', methods=['POST'])
    @login_required
    def delete_cv(student_id):
        """Delete CV file and clear from database"""
        try:
            from src.services.db import get_student_profile_by_id, _get_supabase_client
            
            user = get_current_user()
            
            # Verify ownership
            profile = get_student_profile_by_id(student_id, user['id'])
            if not profile:
                flash("No tienes permiso para eliminar este CV.", "error")
                return redirect(url_for('profile'))
            
            # Get CV file path
            cv_file_path = profile.get('profile_data', {}).get('cv_file_path')
            
            # Delete physical file if exists
            if cv_file_path and os.path.exists(cv_file_path):
                try:
                    os.remove(cv_file_path)
                    print(f"CV file deleted: {cv_file_path}")
                except Exception as e:
                    print(f"Error deleting file: {e}")
            
            # Update database: remove cv_file_path from profile_data and clear cv_raw_text
            current_profile_data = profile.get('profile_data', {})
            if 'cv_file_path' in current_profile_data:
                del current_profile_data['cv_file_path']
            
            supabase = _get_supabase_client()
            update_data = {
                'profile_data': current_profile_data,
                'cv_raw_text': ''
            }
            
            result = supabase.table('students').update(update_data).eq('id', student_id).eq('user_id', user['id']).execute()
            
            # Delete all matches for this profile since CV is being removed
            if result.data:
                try:
                    supabase.table('matches').delete().eq('student_id', student_id).execute()
                    print(f"Deleted all matches for student profile: {student_id}")
                except Exception as e:
                    print(f"Error deleting matches: {e}")
                
                flash("CV eliminado correctamente.", "success")
            else:
                flash("Error al eliminar el CV de la base de datos.", "error")
                
        except Exception as e:
            print(f"Error deleting CV: {e}")
            import traceback
            traceback.print_exc()
            flash("Ocurrió un error al eliminar el CV.", "error")
        
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

    @app.route('/matches/clear/<student_id>', methods=['POST'])
    @login_required
    def clear_matches_history(student_id):
        """Clear all matches for a student profile"""
        try:
            from src.services.db import get_student_profile_by_id, _get_supabase_client
            
            user = get_current_user()
            
            # Verify ownership
            profile = get_student_profile_by_id(student_id, user['id'])
            if not profile:
                flash("No tienes permiso para borrar este historial.", "error")
                return redirect(url_for('profile'))
            
            # Delete all matches for this student
            supabase = _get_supabase_client()
            result = supabase.table('matches').delete().eq('student_id', student_id).execute()
            
            print(f"Cleared all matches for student {student_id}")
            flash("Historial de oportunidades eliminado correctamente.", "success")
                
        except Exception as e:
            print(f"Error clearing matches: {e}")
            import traceback
            traceback.print_exc()
            flash("Ocurrió un error al eliminar el historial.", "error")
        
        return redirect(url_for('dashboard', student_id=student_id))

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
                
                limit = 3 # Limitar a 3 oportunidades por búsqueda
            # ------------------------

            find_and_save_matches(student_id, num_results=limit)
            
            # Actualizar timestamp
            update_last_search_date(student_id)
            
            return redirect(url_for('dashboard', student_id=student_id))
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500