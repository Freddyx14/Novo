# Novo - Hyper-personalized Career Agent

Aplicación web Flask para estudiantes universitarios. Analiza tu CV y audio con IA (Google Gemini) y te recomienda oportunidades personalizadas de prácticas y fellowships.

**Stack:** Python/Flask · Supabase (Auth + PostgreSQL) · Google Gemini · Perplexity API · Stripe · TailwindCSS  
**Deploy:** Vercel (serverless via `api/index.py`)

## Quick Start (Desarrollo Local)

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
/matches  → Ver oportunidades recomendadas (Perplexity + Gemini)
```

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
│   ├── routes.py               # Rutas/endpoints con protección auth
│   └── services/
│       ├── __init__.py
│       ├── auth.py             # Autenticación Supabase (register, login, @login_required)
│       ├── ai_agent.py         # Integración Google Gemini (análisis CV + audio)
│       ├── db.py               # Operaciones CRUD contra Supabase (PostgreSQL)
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
│   ├── my_profiles.html        # Listar perfiles del usuario
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
| `/logout` | GET | No | Cierra sesión |
| `/profile` | GET/POST | Sí | Subir CV + audio |
| `/results` | GET | Sí | Ver análisis IA |
| `/my-profiles` | GET | Sí | Listar perfiles |
| `/test-hunter/<id>` | GET | Sí | Buscar oportunidades |
| `/dashboard/<id>` | GET | Sí | Ver matches |
| `/upgrade` | GET | Sí | Página Premium |

## Seguridad

1. **Autenticación**: Supabase Auth (email/password + JWT)
2. **Sesiones**: Flask session con tokens JWT
3. **Protección de rutas**: Decorador `@login_required`
4. **Ownership**: `verify_student_ownership()` verifica que cada usuario solo vea sus datos
5. **RLS**: Row Level Security en Supabase filtra queries por `user_id`

## Deploy en Vercel

El proyecto despliega en Vercel como serverless function:
- `vercel.json` → Enruta todo a `api/index.py`
- `api/index.py` → Importa `app` de `app.py` y lo expone
- `runtime.txt` → Define Python 3.11
- Variables de entorno se configuran en el dashboard de Vercel

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
