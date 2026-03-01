#!/bin/bash
# ============================================================
# NOVO - Comandos útiles para desarrollo
# Última actualización: Feb 2026
# ============================================================

# ============================================
# CONFIGURACIÓN INICIAL
# ============================================

# 1. Crear y activar entorno virtual
#    Linux / macOS:
#      python3 -m venv .venv
#      source .venv/bin/activate
#
#    Windows (PowerShell):
#      python -m venv .venv
#      .\.venv\Scripts\Activate.ps1
#
#    NOTA: Si usas Conda, desactívalo primero: conda deactivate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Generar SECRET_KEY (copia el resultado al .env)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# 4. Crear archivo .env con estas variables:
#    SUPABASE_URL=tu_supabase_url
#    SUPABASE_KEY=tu_supabase_anon_key
#    SECRET_KEY=clave_generada_arriba
#    GEMINI_API_KEY=tu_gemini_api_key
#    GOOGLE_API_KEY=tu_google_api_key
#    PERPLEXITY_API_KEY=tu_perplexity_api_key
#    STRIPE_SECRET_KEY=tu_stripe_secret_key
#    STRIPE_PRICE_ID=tu_stripe_price_id

# ============================================
# EJECUTAR APLICACIÓN
# ============================================

# Modo desarrollo (local)
python3 app.py
# → Abre http://localhost:5000

# ============================================
# GIT WORKFLOW
# ============================================

# Crear rama de trabajo
# git checkout -b rama-nombre

# Ver estado
# git status

# Commit + push
# git add .
# git commit -m "feat: descripción del cambio"
# git push origin rama-nombre

# Volver a main y actualizar
# git checkout main
# git pull origin main

# ============================================
# SUPABASE
# ============================================

# Después de crear proyecto en Supabase:
# 1. Ve a Settings → API
# 2. Copia la URL del proyecto → SUPABASE_URL
# 3. Copia la anon/public key → SUPABASE_KEY
# 4. Añádelas al archivo .env

# ============================================
# TROUBLESHOOTING
# ============================================

# Si hay problemas con las dependencias:
# pip install --upgrade pip
# pip install -r requirements.txt --force-reinstall

# Si Flask no se conecta a Supabase:
# 1. Verifica el archivo .env (que exista y tenga valores correctos)
# 2. Revisa los logs en Supabase Dashboard

# Si la aplicación no inicia:
# 1. Verifica que el puerto 5000 esté libre
# 2. Asegúrate de estar en el entorno virtual (.venv)
# 3. Verifica que todas las dependencias estén instaladas

# Si en Windows no activa el .venv:
# 1. Asegurate de no tener Conda activo (conda deactivate)
# 2. Usa: .\.venv\Scripts\Activate.ps1
# 3. Si da error de política: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# Limpiar caché de Python
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# ============================================
# INFORMACIÓN DEL PROYECTO
# ============================================

echo ""
echo "🌐 Rutas de la aplicación (http://localhost:5000):"
echo "  Públicas:"
echo "    /           → Redirige a /profile o /login"
echo "    /register   → Registro de usuario"
echo "    /login      → Login"
echo "    /logout     → Cerrar sesión"
echo "  Protegidas (@login_required):"
echo "    /profile         → Subir CV + audio"
echo "    /profile-view/id → Ver perfil analizado"
echo "    /results         → Resultados de análisis IA"
echo "    /my-profiles     → Listar perfiles"
echo "    /test-hunter/id  → Buscar oportunidades"
echo "    /dashboard/id    → Ver matches"
echo "    /upgrade         → Plan Premium"
echo ""
echo "📁 Archivos clave:"
echo "  app.py              → Entry point Flask"
echo "  src/routes.py       → Endpoints"
echo "  src/services/       → auth.py, db.py, ai_agent.py, hunter.py"
echo "  templates/          → HTML (Jinja2 + Tailwind)"
echo "  api/index.py        → Entry point Vercel (serverless)"
echo "  .env                → Variables de entorno (NO subir a Git)"

