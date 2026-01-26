# 🚀 Guía Rápida de Inicio - Sistema de Autenticación

## ✅ Lo que se ha implementado

### 1. **Servicio de Autenticación** (`src/services/auth.py`)
   - ✓ Registro de usuarios con Supabase
   - ✓ Inicio de sesión
   - ✓ Cierre de sesión
   - ✓ Verificación de sesión
   - ✓ Decorador `@login_required` para proteger rutas

### 2. **Templates de Autenticación**
   - ✓ `templates/login.html` - Página de inicio de sesión
   - ✓ `templates/register.html` - Página de registro

### 3. **Rutas de Autenticación** (en `src/routes.py`)
   - ✓ `/register` - Registro de nuevos usuarios
   - ✓ `/login` - Inicio de sesión
   - ✓ `/logout` - Cierre de sesión

### 4. **Protección de Rutas Existentes**
   - ✓ `/profile` - Requiere autenticación
   - ✓ `/results` - Requiere autenticación
   - ✓ `/dashboard/<student_id>` - Requiere autenticación

### 5. **Actualización de Templates**
   - ✓ Barra de navegación con nombre de usuario
   - ✓ Botón de "Cerrar Sesión" en todas las páginas protegidas
   - ✓ Templates actualizados: profile.html, results.html, matches.html

### 6. **Integración con Base de Datos**
   - ✓ Modificado `save_student_profile()` para incluir `user_id`
   - ✓ Script SQL para configurar la base de datos (`supabase_auth_setup.sql`)

### 7. **Documentación**
   - ✓ Guía detallada de configuración (`SUPABASE_AUTH_SETUP.md`)
   - ✓ README actualizado con información de autenticación
   - ✓ Archivo `.env.example` con variables necesarias

## 📋 Pasos para Activar el Sistema

### Paso 1: Configurar Supabase

1. Ve a [https://supabase.com](https://supabase.com)
2. Crea un nuevo proyecto (o usa uno existente)
3. Copia la URL del proyecto y la clave anónima (anon key)

### Paso 2: Configurar Variables de Entorno

```bash
# Si no tienes un archivo .env, créalo:
cp .env.example .env

# Edita el archivo .env con tus credenciales:
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_clave_anon_key
SECRET_KEY=genera_una_clave_secreta_aleatoria
GOOGLE_API_KEY=tu_clave_de_google_si_la_tienes
```

Para generar una SECRET_KEY segura, puedes usar:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Paso 3: Configurar la Base de Datos en Supabase

1. Ve a tu proyecto en Supabase
2. Navega a **SQL Editor** en el menú lateral
3. Crea una nueva query
4. Copia y pega el contenido del archivo `supabase_auth_setup.sql`
5. Ejecuta el script (haz clic en "Run")

Este script:
- Agrega la columna `user_id` a las tablas
- Habilita Row Level Security (RLS)
- Crea políticas de seguridad para proteger los datos

### Paso 4: Habilitar Autenticación por Email en Supabase

1. Ve a **Authentication** → **Providers** en Supabase
2. Asegúrate de que **Email** esté habilitado
3. (Opcional) Desactiva "Confirm email" para desarrollo más rápido

### Paso 5: Ejecutar la Aplicación

```bash
# Asegúrate de estar en el entorno virtual
source .venv/bin/activate

# Ejecuta la aplicación
python3 app.py
```

### Paso 6: Probar el Sistema

1. Abre tu navegador en `http://localhost:5000`
2. Serás redirigido a `/login`
3. Haz clic en "Regístrate aquí"
4. Completa el formulario de registro
5. Inicia sesión con tus credenciales
6. ¡Listo! Ahora puedes usar la aplicación

## 🔍 Flujo de Usuario

```
┌─────────────┐
│   Inicio    │
│     /       │
└──────┬──────┘
       │
       ├─ No autenticado → /login
       │
       └─ Autenticado → /profile
                          │
                          ├─ Subir CV y audio
                          │
                          ├─ Ver resultados → /results
                          │
                          └─ Ver oportunidades → /dashboard
```

## 🛡️ Características de Seguridad

✅ Contraseñas hasheadas con bcrypt (manejado por Supabase)
✅ Sesiones JWT seguras
✅ Row Level Security en la base de datos
✅ Rutas protegidas con decorador @login_required
✅ Validación de formularios
✅ Datos de usuario aislados por user_id

## 🐛 Troubleshooting

### "SUPABASE_URL or SUPABASE_KEY not set"
- Verifica que el archivo `.env` existe en la raíz del proyecto
- Asegúrate de que las variables estén configuradas correctamente

### "Invalid login credentials"
- Verifica email y contraseña
- Si usas confirmación de email, revisa tu bandeja de entrada

### No puedo registrarme
- Verifica que Email Auth esté habilitado en Supabase
- Revisa los logs en Supabase → Authentication → Logs

### Error al guardar perfil
- Verifica que ejecutaste el script SQL en Supabase
- Asegúrate de que la columna `user_id` existe en la tabla `students`

## 📚 Recursos Adicionales

- [Documentación de Supabase Auth](https://supabase.com/docs/guides/auth)
- [Flask Sessions](https://flask.palletsprojects.com/en/3.0.x/quickstart/#sessions)
- [Guía completa de configuración](SUPABASE_AUTH_SETUP.md)

## ✨ Próximos Pasos (Opcional)

- [ ] Implementar "Olvidé mi contraseña"
- [ ] Agregar autenticación con Google/GitHub
- [ ] Agregar perfil de usuario editable
- [ ] Implementar cambio de contraseña
- [ ] Agregar verificación de email obligatoria
- [ ] Dashboard de administración

---

**¡Todo listo!** El sistema de autenticación está completamente implementado y listo para usar. 🎉
