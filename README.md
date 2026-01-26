# Novo - Hyper-personalized Career Agent

A Flask-based application for university students to get personalized career guidance through AI analysis of their CV and audio "brain dump." Now with **Supabase authentication** to protect user data and personalize the experience.

## Features

- 🔐 **User Authentication:** Secure registration and login with Supabase
- 📄 **Profile Upload:** Upload CV (PDF) and audio brain dump (MP3/WAV/M4A/OGG)
- 🤖 **AI Analysis:** Gemini-powered multimodal analysis of your profile
- 🎯 **Personalized Matches:** Get tailored internship and fellowship opportunities
- 🔒 **Protected Routes:** Only authenticated users can access the application
- 🎨 **Modern UI:** Beautiful interface built with TailwindCSS

## Setup

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure Supabase:**
   - Create a project at [https://supabase.com](https://supabase.com)
   - Run the SQL script in `supabase_auth_setup.sql` in your Supabase SQL Editor
   - See detailed instructions in [SUPABASE_AUTH_SETUP.md](SUPABASE_AUTH_SETUP.md)

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your credentials:
   ```
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   SECRET_KEY=your_secret_key_here
   GOOGLE_API_KEY=your_google_api_key
   ```

5. **Run the application:**
   ```bash
   python3 app.py
   ```

6. **Access the application:**
   Open your browser and navigate to `http://localhost:5000`

## Application Flow

1. **Register/Login** → Create an account or sign in at `/register` or `/login`
2. **Upload Profile** → Submit your CV and optional audio at `/profile`
3. **View Analysis** → See your AI-powered profile analysis at `/results`
4. **Browse Opportunities** → Explore personalized matches at `/dashboard`
5. **Logout** → Click "Cerrar Sesión" in the navigation bar

## Project Structure

```
University_Opportunities/
├── app.py                      # Flask application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore rules
├── SUPABASE_AUTH_SETUP.md     # Supabase authentication guide
├── supabase_auth_setup.sql    # SQL script for database setup
├── uploads/                   # Temporary file storage
├── src/
│   ├── __init__.py
│   ├── routes.py              # Route handlers with auth protection
│   └── services/
│       ├── __init__.py
│       ├── auth.py            # Supabase authentication service
│       ├── ai_agent.py        # Gemini API integration
│       ├── db.py              # Supabase database operations
│       └── hunter.py          # Opportunity matching service
└── templates/
    ├── login.html             # Login page
    ├── register.html          # Registration page
    ├── profile.html           # Profile upload page (protected)
    ├── results.html           # Analysis results page (protected)
    └── matches.html           # Opportunities dashboard (protected)
```

## Authentication

This application uses **Supabase Auth** for secure user management:

- Email/password authentication
- Session management with JWT tokens
- Protected routes with `@login_required` decorator
- User data isolation with Row Level Security (RLS)

All main routes require authentication. Users must register and login to access the application.

## Protected Routes

- `/profile` - Upload CV and audio
- `/results` - View profile analysis
- `/dashboard/<student_id>` - View matched opportunities

## Public Routes

- `/` - Redirects to login or profile based on auth status
- `/login` - User login
- `/register` - User registration
- `/logout` - User logout

## Features

- **Profile Upload:** Upload CV (PDF) and audio brain dump (MP3/WAV/M4A/OGG)
- **Gemini Integration:** Ready for multimodal AI analysis
- **Modern UI:** Beautiful interface built with TailwindCSS

## Tech Stack

- **Backend:** Python 3, Flask
- **Authentication:** Supabase Auth
- **Database:** Supabase (PostgreSQL)
- **AI:** Google Gemini 1.5 Pro
- **Frontend:** HTML5, TailwindCSS (CDN)
- **Environment:** python-dotenv

## Security Features

- Passwords stored securely with Supabase (bcrypt hashing)
- JWT-based session management
- Row Level Security (RLS) in database
- CSRF protection via Flask sessions
- Protected routes with authentication middleware

## Documentation

- [Supabase Auth Setup Guide](SUPABASE_AUTH_SETUP.md) - Detailed authentication configuration
- [SQL Setup Script](supabase_auth_setup.sql) - Database schema and security policies

## License

MIT
