"""
Authentication service using Supabase Auth
"""

from flask import session, redirect, url_for
from functools import wraps
from src.services.db import _get_supabase_client
import os


def register_user(email, password, full_name=None):
    """
    Register a new user with Supabase Auth
    
    Args:
        email: User's email
        password: User's password
        full_name: Optional full name
        
    Returns:
        dict: Response with user data or error
    """
    try:
        supabase = _get_supabase_client()
        
        # Create user with Supabase Auth
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                },
                # Redirect to confirmation route
                "email_redirect_to": "https://university-opportunities.vercel.app/confirmacion-exitosa"
            }
        })
        
        if response.user:
            return {
                'success': True,
                'user': response.user,
                'message': 'Registration successful! Please check your email to verify your account.'
            }
        else:
            return {
                'success': False,
                'error': 'Registration failed'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def login_user(email, password):
    """
    Log in a user with Supabase Auth
    
    Args:
        email: User's email
        password: User's password
        
    Returns:
        dict: Response with session data or error
    """
    try:
        supabase = _get_supabase_client()
        
        # Sign in with Supabase Auth
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Store user info in Flask session
            session['user_id'] = response.user.id
            session['user_email'] = response.user.email
            session['access_token'] = response.session.access_token
            session['refresh_token'] = response.session.refresh_token
            
            # Store user metadata if available
            if response.user.user_metadata:
                session['user_name'] = response.user.user_metadata.get('full_name', email.split('@')[0])
            
            return {
                'success': True,
                'user': response.user,
                'message': 'Login successful!'
            }
        else:
            return {
                'success': False,
                'error': 'Login failed'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def request_password_reset(email, redirect_to):
    """
    Send a password reset email using Supabase Auth.

    Args:
        email: User's email address
        redirect_to: URL that Supabase should redirect to after recovery

    Returns:
        dict: Success/error response
    """
    try:
        supabase = _get_supabase_client()
        supabase.auth.reset_password_for_email(
            email,
            {
                'redirect_to': redirect_to,
            }
        )

        return {
            'success': True,
            'message': 'Te enviamos un correo para restablecer tu contraseña. Revisa tu bandeja de entrada y spam.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def store_recovery_session(access_token, refresh_token):
    """Store password recovery tokens in the Flask session."""
    session['recovery_access_token'] = access_token
    session['recovery_refresh_token'] = refresh_token


def has_recovery_session():
    """Return True when a recovery session is available."""
    return bool(session.get('recovery_access_token') and session.get('recovery_refresh_token'))


def clear_recovery_session():
    """Remove password recovery tokens from the Flask session."""
    session.pop('recovery_access_token', None)
    session.pop('recovery_refresh_token', None)


def complete_password_reset(new_password):
    """
    Update the authenticated Supabase user's password using the recovery session.

    Args:
        new_password: New password provided by the user

    Returns:
        dict: Success/error response
    """
    try:
        access_token = session.get('recovery_access_token')
        refresh_token = session.get('recovery_refresh_token')

        if not access_token or not refresh_token:
            return {
                'success': False,
                'error': 'No se encontró una sesión de recuperación válida. Vuelve a abrir el enlace del correo.'
            }

        supabase = _get_supabase_client()
        supabase.auth.set_session(access_token, refresh_token)
        supabase.auth.update_user({'password': new_password})
        clear_recovery_session()

        return {
            'success': True,
            'message': 'Tu contraseña fue actualizada correctamente. Ya puedes iniciar sesión.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def logout_user():
    """
    Log out the current user
    """
    try:
        supabase = _get_supabase_client()
        
        # Sign out from Supabase
        if 'access_token' in session:
            supabase.auth.sign_out()
        
        # Clear Flask session
        session.clear()
        
        return {'success': True, 'message': 'Logged out successfully'}
    except Exception as e:
        # Clear session even if Supabase call fails
        session.clear()
        return {'success': False, 'error': str(e)}


def get_current_user():
    """
    Get the current logged-in user from session
    
    Returns:
        dict: User data or None if not logged in
    """
    if 'user_id' in session:
        return {
            'id': session.get('user_id'),
            'email': session.get('user_email'),
            'name': session.get('user_name', session.get('user_email', '').split('@')[0])
        }
    return None


def is_authenticated():
    """
    Check if user is authenticated
    
    Returns:
        bool: True if user is logged in, False otherwise
    """
    return 'user_id' in session and 'access_token' in session


def login_required(f):
    """
    Decorator to protect routes that require authentication
    
    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return 'Protected content'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def refresh_session():
    """
    Refresh the user's session token
    
    Returns:
        bool: True if refresh successful, False otherwise
    """
    try:
        if 'refresh_token' not in session:
            return False
            
        supabase = _get_supabase_client()
        
        # Refresh the session
        response = supabase.auth.refresh_session(session['refresh_token'])
        
        if response.session:
            session['access_token'] = response.session.access_token
            session['refresh_token'] = response.session.refresh_token
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error refreshing session: {e}")
        return False
