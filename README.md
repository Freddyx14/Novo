# Novo - Hyper-personalized Career Agent

Aplicación web Flask para estudiantes universitarios. Analiza tu CV y audio con IA (Google Gemini) y te recomienda oportunidades personalizadas de prácticas y fellowships.

**Stack:** Python/Flask · Supabase (Auth + PostgreSQL) · Google Gemini · Perplexity API · Stripe · TailwindCSS  
**Deploy:** Vercel (serverless via `api/index.py`)

## Quick Start (Desarrollo Local)

### Handoff Rápido

Si vas a retomar este proyecto después de un tiempo o se lo vas a pasar a otra persona, empieza por leer en este orden:

1. Este README para instalación, rutas y modelo actual.
2. `FLUJO_COMPLETO.md` para entender el recorrido funcional.
3. `ARQUITECTURA_VISUAL.txt` para ver la estructura general.
4. `commands.sh` para comandos útiles de desarrollo.

Si vas a tocar una parte concreta, revisa también `src/routes.py`, `src/services/db.py`, `src/services/hunter.py`, `templates/matches.html` y `templates/my_profiles.html`.

### Requisitos previos
- Python 3.11+
- Git
- Credenciales de: Supabase, Google Gemini, Perplexity, Stripe (pedir al admin del proyecto)

### 1. Clonar y crear environment

```bash
git clone https://github.com/Freddyx14/University_Opportunities.git
cd University_Opportunities

# Crear y activar virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_anon_key
SECRET_KEY=una_clave_secreta_larga
GEMINI_API_KEY=tu_gemini_api_key
GOOGLE_API_KEY=tu_google_api_key
PERPLEXITY_API_KEY=tu_perplexity_api_key
STRIPE_SECRET_KEY=tu_stripe_secret_key
STRIPE_PRICE_ID=tu_stripe_price_id
```

> **Nota:** El archivo `.env` está en `.gitignore` y NUNCA debe subirse a GitHub.

### 4. Ejecutar la aplicación

```bash
python app.py
```

Abre tu navegador en: **http://localhost:5000**

## Flujo de la Aplicación

```
/register → Crear cuenta (Supabase Auth)
/login    → Iniciar sesión (JWT + Flask session)
/profile  → Subir CV (PDF) + audio brain dump (MP3/WAV/M4A/OGG)
/results  → Ver análisis IA de tu perfil (Gemini)
/my-profiles → Gestionar perfiles base y objetivos
/profiles/<id> → Ver un perfil base concreto y sus objetivos
/dashboard/<id> → Ver oportunidades recomendadas para el objetivo activo
```

## Modelo de Producto

Novo separa dos conceptos:

- **Perfil base**: CV, habilidades, experiencia y resumen general.
- **Objetivo de búsqueda**: intención concreta reutilizable sobre un mismo perfil base.

Un usuario puede tener hasta **5 perfiles base** en su cuenta. Cada perfil puede contener varios objetivos y uno de ellos puede quedar activo para orientar la búsqueda y la vista de resultados.

## Estructura del Proyecto

```
University_Opportunities/
├── app.py                      # Entry point Flask (puerto 5000)
├── api/
│   └── index.py                # Entry point para Vercel (serverless)
├── vercel.json                 # Configuración de deploy Vercel
├── requirements.txt            # Dependencias Python
├── runtime.txt                 # Versión Python para Vercel (3.11)
├── .env                        # Variables de entorno (NO se sube a Git)
├── .gitignore                  # Archivos ignorados por Git
│
├── src/                        # Código fuente backend
│   ├── __init__.py
│   ├── routes.py               # Rutas/endpoints con auth, perfiles base y objetivos
│   └── services/
│       ├── __init__.py
│       ├── auth.py             # Autenticación Supabase (register, login, @login_required)
│       ├── ai_agent.py         # Integración Google Gemini (análisis CV + audio)
│       ├── db.py               # Operaciones CRUD y helpers de perfiles/objetivos contra Supabase
│       └── hunter.py           # Búsqueda oportunidades (Perplexity) + ranking (Gemini)
│
├── templates/                  # Vistas HTML (Jinja2 + TailwindCSS CDN)
│   ├── base_styles.html        # Estilos base compartidos
│   ├── login.html              # Página de login
│   ├── register.html           # Página de registro
│   ├── confirmacion_auth.html  # Confirmación de registro
│   ├── profile.html            # Subir CV + audio
│   ├── profile_view.html       # Ver perfil analizado
│   ├── profile_edit.html       # Editar perfil
│   ├── my_profiles.html        # Gestionar perfiles base y objetivos
│   ├── results.html            # Resultados de análisis IA
│   ├── matches.html            # Oportunidades recomendadas
│   ├── upgrade.html            # Página de upgrade a Premium
│   ├── premium_activation.html # Activación Premium (Stripe)
│   └── components/
│       └── upgrade_badge.html  # Badge de upgrade reutilizable
│
├── static/images/users/        # Imágenes de perfil de usuarios
│
├── client/                     # (Legacy) Utilidades JS auxiliares, NO es frontend principal
│   ├── package.json
│   └── src/services/api.js     # Helper de llamadas API (no usado actualmente)
│
├── db/connection.py            # (Legacy) Conexión PostgreSQL directa con psycopg2
├── prisma/schema.prisma        # (Legacy) Schema Prisma (no usado, BD es Supabase)
├── next.config.ts              # (Legacy) Config Next.js (no usada)
│
├── ARQUITECTURA_VISUAL.txt     # Diagrama de arquitectura del sistema
├── commands.sh                 # Comandos útiles para desarrollo
└── README.md                   # Este archivo
```

> **Nota sobre carpetas Legacy:** `client/`, `db/`, `prisma/`, `next.config.ts` son archivos residuales
> de versiones anteriores del proyecto. No se usan en la aplicación actual. El frontend se sirve
> directamente desde Flask (`templates/` + TailwindCSS CDN).

## Arquitectura

La aplicación es un **monolito Flask** que sirve HTML server-side (Jinja2):

```
Navegador ──HTTP──► Flask (routes.py) ──► Servicios ──► APIs externas
    ▲                    │                    │
    │                    ▼                    ├─ Supabase Auth (JWT)
    │              templates/                 ├─ Supabase DB (PostgreSQL)
    │              (HTML+Tailwind)            ├─ Google Gemini (análisis IA)
    └──HTML────────────────                   ├─ Perplexity (búsqueda web)
                                              └─ Stripe (pagos Premium)
```

## Rutas

| Ruta | Método | Auth | Descripción |
|------|--------|------|-------------|
| `/` | GET | No | Redirige a `/profile` o `/login` |
| `/register` | GET/POST | No | Registro de usuario |
| `/login` | GET/POST | No | Login de usuario |
| `/forgot-password` | GET/POST | No | Solicitar correo de recuperación |
| `/reset-password` | GET/POST | No | Crear nueva contraseña desde el enlace del correo |
| `/reset-password/session` | POST | No | Validar la sesión de recuperación enviada por Supabase |
| `/logout` | GET | No | Cierra sesión |
| `/profile` | GET/POST | Sí | Crear o editar el perfil base más reciente |
| `/results` | GET | Sí | Ver análisis IA |
| `/my-profiles` | GET | Sí | Ver perfiles base, objetivos y resultados por perfil |
| `/profiles/<id>` | GET | Sí | Ver un perfil base concreto y administrar objetivos |
| `/objectives/<student_id>/create` | POST | Sí | Crear un objetivo de búsqueda para un perfil base |
| `/objectives/<student_id>/activate/<objective_id>` | POST | Sí | Activar un objetivo de búsqueda existente |
| `/test-hunter/<id>` | GET | Sí | Buscar oportunidades |
| `/dashboard/<id>` | GET | Sí | Ver matches |
| `/upgrade` | GET | Sí | Página Premium |

## Seguridad

1. **Autenticación**: Supabase Auth (email/password + JWT)
2. **Sesiones**: Flask session con tokens JWT
3. **Protección de rutas**: Decorador `@login_required`
4. **Ownership**: `verify_student_ownership()` verifica que cada usuario solo vea sus datos
5. **RLS**: Row Level Security en Supabase filtra queries por `user_id`
6. **Límite de perfiles base**: la aplicación rechaza nuevos perfiles cuando el usuario llega a 5
7. **Recuperación de contraseña**: agrega estas URLs permitidas en Supabase Auth > URL Configuration:
    - `http://localhost:5000/reset-password`
    - `https://university-opportunities.vercel.app/reset-password`

## Deploy en Vercel

El proyecto despliega en Vercel como serverless function:
- `vercel.json` → Enruta todo a `api/index.py`
- `api/index.py` → Importa `app` de `app.py` y lo expone
- `runtime.txt` → Define Python 3.11
- Variables de entorno se configuran en el dashboard de Vercel

## Testing

La suite de tests valida cada etapa del pipeline de forma independiente:

### Ejecutar Tests Individuales

```bash
# Interactive mode (selecciona qué tests correr)
python tests/test_individual_steps.py

# Tests automáticos (todos en secuencia)
python tests/run_all_tests.py
```

### Descripción de Tests

| Test | Descripción |
|------|-------------|
| TEST 1 | Verificar conexión a Google Gemini API |
| TEST 2 | Verificar conexión a Supabase (BD + Auth) |
| TEST 3 | Extraer texto raw de PDF del CV |
| TEST 4 | Analizar perfil del estudiante (JSON estructurado) |
| TEST 5 | Generar 3 oportunidades basadas en perfil |
| TEST 6 | Puntuar oportunidades (0-100) y elegibilidad |
| TEST 7 | Guardar perfil de estudiante en BD |
| TEST 8 | Pipeline completo: búsqueda → scoring → guardar |

**Notas:**
- Tests 5-6 comparten datos (TEST 6 depende de TEST 5)
- Tests 7-8 usan cuenta demo (`demo@novo.app`) aislada de usuarios personales
- Credenciales de demo en `.env` (nunca en código)

## Credenciales & Seguridad

**CRÍTICO:** Nunca commitear `.env` ni archivos con API keys

```bash
# Crear archivo .env desde el template
cp .env.example .env

# Completar con tus credenciales reales
# (pedir al admin del proyecto)
```

**API Keys necesarias:**
- `GEMINI_API_KEY` - Google Gemini (análisis IA)
- `SUPABASE_URL`, `SUPABASE_KEY` - Database + Auth
- `PERPLEXITY_API_KEY` - Búsqueda web
- `STRIPE_SECRET_KEY` - Pagos Premium
- `DEMO_EMAIL`, `DEMO_PASSWORD` - Cuenta de testing

## Git Workflow

```bash
# Crear rama de trabajo
git checkout -b rama-nombre

# Hacer cambios + commit
git add .
git commit -m "feat: descripción del cambio"
git push origin rama-nombre

# Crear Pull Request en GitHub → Review → Merge a main
# Vercel despliega automáticamente al mergear a main
```

## License

MIT
