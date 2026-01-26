#!/bin/bash
# Comandos útiles para el proyecto Novo

# ============================================
# CONFIGURACIÓN INICIAL
# ============================================

# 1. Activar entorno virtual
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Generar SECRET_KEY (copia el resultado al .env)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# ============================================
# PRUEBAS Y DESARROLLO
# ============================================

# Probar configuración
python3 test_setup.py

# Ejecutar aplicación en modo desarrollo
python3 app.py

# Ejecutar en un puerto específico
# python3 -c "from app import app; app.run(debug=True, port=8000)"

# ============================================
# SUPABASE
# ============================================

# Después de crear proyecto en Supabase:
# 1. Ve a Settings → API
# 2. Copia la URL del proyecto
# 3. Copia la anon/public key
# 4. Añádelas al archivo .env

# Para ejecutar el script SQL:
# 1. Ve a SQL Editor en Supabase
# 2. Copia el contenido de supabase_auth_setup.sql
# 3. Pégalo y ejecuta

# ============================================
# DESARROLLO
# ============================================

# Ver errores en tiempo real
# tail -f error.log

# Limpiar caché de Python
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# ============================================
# TESTING MANUAL
# ============================================

# 1. Abrir navegador en:
echo "Abre http://localhost:5000"

# 2. Probar registro
echo "Ve a http://localhost:5000/register"

# 3. Probar login
echo "Ve a http://localhost:5000/login"

# ============================================
# TROUBLESHOOTING
# ============================================

# Si hay problemas con las dependencias:
# pip install --upgrade pip
# pip install -r requirements.txt --force-reinstall

# Si Flask no se conecta a Supabase:
# 1. Verifica el archivo .env
# 2. Ejecuta: python3 test_setup.py
# 3. Revisa los logs en Supabase Dashboard

# Si la aplicación no inicia:
# 1. Verifica que el puerto 5000 esté libre
# 2. Asegúrate de estar en el entorno virtual
# 3. Verifica que todas las dependencias estén instaladas

# ============================================
# INFORMACIÓN DEL PROYECTO
# ============================================

echo "📁 Estructura del proyecto:"
tree -I '__pycache__|.venv|.git' -L 3

echo ""
echo "📚 Documentación disponible:"
echo "  - README.md (General)"
echo "  - QUICK_START.md (Inicio rápido)"
echo "  - SUPABASE_AUTH_SETUP.md (Config Supabase)"
echo "  - IMPLEMENTATION_SUMMARY.txt (Resumen)"

echo ""
echo "🔧 Scripts disponibles:"
echo "  - test_setup.py (Verificar configuración)"
echo "  - app.py (Iniciar aplicación)"
echo "  - supabase_auth_setup.sql (Config base de datos)"

echo ""
echo "🌐 Rutas de la aplicación:"
echo "  Públicas:"
echo "    - / (Inicio)"
echo "    - /register (Registro)"
echo "    - /login (Login)"
echo "    - /logout (Logout)"
echo "  Protegidas:"
echo "    - /profile (Subir CV)"
echo "    - /results (Ver análisis)"
echo "    - /dashboard/<id> (Ver oportunidades)"
