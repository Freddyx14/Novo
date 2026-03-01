# 🔄 Diagrama de Flujo Completo del Proyecto - Novo

## 📊 Diagrama del Proceso

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: UPLOAD CV + BRAIN DUMP                                  │
├─────────────────────────────────────────────────────────────────┤
│ 📁 Usuario sube:                                                │
│   • CV (PDF) → Guardado en temp file                           │
│   • Brain Dump (texto O audio) → Convertido a texto por Gemini│
│                                                                  │
│ 📍 Ubicación: /src/routes.py - def upload_profile() [línea 144]│
│ 📁 Archivos temp: Windows TEMP dir (AutoDelete)                │
│ 🔑 Endpoint: POST /upload_profile                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: ANALYZE CV + EXTRACT PROFILE DATA                       │
├─────────────────────────────────────────────────────────────────┤
│ 🤖 Gemini hace:                                                 │
│   1. Extract CV raw text (PDF → Texto plano)                   │
│   2. Transcribe audio (si aplica)                              │
│   3. Extract profile data:                                      │
│      - Name, University, Career, Country                       │
│      - Languages, Skills, Interests, Ambitions                 │
│   4. Retorna: (profile_dict, cv_raw_text)                      │
│                                                                  │
│ 📍 Ubicación: /src/services/ai_agent.py                        │
│ 🎯 Función: analyze_profile() y extract_cv_text()              │
│ 📤 Input: CV file path, Audio path, Brain dump text            │
│ 📥 Output: Tuple de (profile_dict, cv_raw_text)                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: SAVE TO DATABASE                                        │
├─────────────────────────────────────────────────────────────────┤
│ 💾 Se guarda en Supabase tabla "students":                      │
│                                                                  │
│ Columnas principales:                                           │
│   • id (UUID)                                                   │
│   • user_id (FK a auth.users)                                  │
│   • name                                                        │
│   • university                                                  │
│   • career                                                      │
│   • cv_raw_text ⭐ TEXTO COMPLETO SIN PROCESAR                 │
│   • brain_dump_text ⭐ CONTEXTO ADICIONAL                       │
│   • profile_data (JSON con skills, languages, etc)             │
│   • created_at                                                  │
│   • updated_at                                                  │
│                                                                  │
│ 📍 Ubicación: /src/services/db.py - save_student_profile()     │
│ 🔗 Supabase: supabase.table("students").insert()               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: SEARCH OPPORTUNITIES                                    │
├─────────────────────────────────────────────────────────────────┤
│ 🔍 Se ejecuta en: /results route [línea 240+]                  │
│                                                                  │
│ ⚙️ ACTUAL (TEMPORAL CON GEMINI):                               │
│   📍 Ubicación: /src/services/hunter.py                         │
│   🎯 Función: search_opportunities_with_gemini()               │
│   🔧 Toggle: USE_GEMINI_FOR_SEARCH = True [línea 16]           │
│                                                                  │
│   📤 INPUTS:                                                    │
│      • cv_raw_text: Texto COMPLETO del CV                      │
│      • brain_dump_text: Contexto adicional                     │
│      • profile_data: Datos estructurados (fallback)            │
│      • num_results: Cantidad de oportunidades (default 3)      │
│                                                                  │
│   🧠 PROMPT (líneas 46-67):                                     │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │ "Basándote en este perfil de estudiante, genera         │  │
│   │ {num_results} oportunidades REALISTAS Y RELEVANTES...   │  │
│   │                                                          │  │
│   │ IMPORTANTE:                                              │  │
│   │ - Adecuadas para nivel de estudios, país y perfil       │  │
│   │ - Variedad: becas, pasantías, investigación, etc        │  │
│   │ - Usa nombres realistas                                 │  │
│   │ - URLs realistas (pueden ser ficticias)                 │  │
│   │                                                          │  │
│   │ Devuelve SOLO un array JSON válido"                     │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                  │
│ 📥 OUTPUT:                                                      │
│   [                                                             │
│     {                                                           │
│       "title": "Nombre del programa",                          │
│       "company": "Organización",                              │
│       "location": "País/Ciudad o Remoto",                     │
│       "url": "https://ejemplo.com/programa",                 │
│       "description": "Descripción breve",                     │
│       "opportunity_type": "beca|pasantía|investigación|..",  │
│       "eligibility_level": "pregrado|maestría|doctorado",    │
│       "deadline_info": "Plazo de aplicación"                 │
│     }                                                          │
│   ]                                                            │
│                                                                  │
│ ⚠️ NOTA: Son sintéticas (para testing). Cuando Perplexity     │
│    funcione, serán datos reales verificados.                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: SCORE EACH MATCH                                        │
├─────────────────────────────────────────────────────────────────┤
│ 📊 Se ejecuta por cada oportunidad encontrada                   │
│                                                                  │
│ 📍 Ubicación: /src/services/hunter.py                           │
│ 🎯 Función: evaluate_match() [línea 160+]                       │
│                                                                  │
│ 📤 INPUTS:                                                      │
│   • cv_raw_text: Texto COMPLETO del estudiante                │
│   • brain_dump_text: Contexto adicional                        │
│   • opportunity: JSON de la oportunidad                        │
│   • profile_data: Datos estructurados                          │
│                                                                  │
│ 🧠 PROMPT (línea 185-210):                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ "Evalúa qué tan buena es esta oportunidad para el          │ │
│ │ siguiente estudiante en una escala 0-100:                  │ │
│ │                                                             │ │
│ │ Profesor: {profile_data}                                   │ │
│ │ CV Texto: {cv_raw_text[:2000]}                             │ │
│ │ Contexto: {brain_dump_text}                                │ │
│ │                                                             │ │
│ │ Oportunidad: {opportunity}                                 │ │
│ │                                                             │ │
│ │ IMPORTANTE:                                                 │ │
│ │ - Sé muy realista en el puntaje                            │ │
│ │ - Si no es elegible, score=0 e is_eligible=false           │ │
│ │                                                             │ │
│ │ Devuelve JSON: {score, reason, description, is_eligible}   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ 📥 OUTPUT:                                                      │
│ {                                                               │
│   "score": 75,        # 0-100 match score                      │
│   "reason": "Tu CV coincide bien porque...",                  │
│   "is_eligible": true,                                         │
│   "description": "Detalles de por qué es bueno",              │
│   "eligibility_notes": "Notas si hay restricciones"           │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: SAVE MATCHES TO DATABASE                                │
├─────────────────────────────────────────────────────────────────┤
│ 💾 Se guarda en Supabase tabla "matches":                       │
│                                                                  │
│ Columnas:                                                       │
│   • id (UUID)                                                   │
│   • student_id (FK a students)                                 │
│   • opportunity (JSON con toda la oportunidad)                 │
│   • score (0-100)                                              │
│   • reason (string)                                            │
│   • description (string)                                       │
│   • is_eligible (boolean)                                      │
│   • created_at                                                 │
│                                                                  │
│ 📍 Ubicación: /src/services/hunter.py [línea 330+]             │
│ 🔗 Supabase: supabase.table("matches").insert()                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: DISPLAY RESULTS                                         │
├─────────────────────────────────────────────────────────────────┤
│ 🖥️ Se muestra en template: results.html                         │
│                                                                  │
│ 📍 Ubicación: /src/routes.py - def results() [línea 240+]      │
│ 🎯 Query: Fetch matches de la DB para mostrar al usuario       │
│                                                                  │
│ Datos mostrados:                                                │
│   • Nombre de oportunidad                                       │
│   • Puntaje de match (visualizado como barra)                  │
│   • Razón del puntaje                                          │
│   • Link a oportunidad                                         │
│   • "Apply Now" button (lleva a URL externa)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 GUÍA DE TESTING POR PASO

### **TEST 1: Verificar que el CV se carga y extrae correctamente**
```python
# Ubicación: /src/services/ai_agent.py

# Punto de entrada
from src.services.ai_agent import GeminiAgent

agent = GeminiAgent()
cv_text = agent.extract_cv_text("/ruta/a/cv.pdf")
print(f"✓ CV extraído: {len(cv_text)} caracteres")
print(f"Primeros 500 chars: {cv_text[:500]}")
```

**Qué validar:**
- [ ] CV_text no está vacío
- [ ] Tiene al menos 100 caracteres
- [ ] Contiene palabras clave esperadas (nombre, carrera, universidad)
- [ ] Mantiene el formato original (sin resumir)

---

### **TEST 2: Verificar que Gemini extrae bien el perfil**
```python
from src.services.ai_agent import GeminiAgent

agent = GeminiAgent()
profile_dict, cv_raw_text = agent.analyze_profile(
    cv_file_path="/ruta/a/cv.pdf",
    audio_file_path=None,
    brain_dump_text="Soy muy interesado en becas en Europa"
)

print("Profile Extraído:")
print(f"Name: {profile_dict.get('name')}")
print(f"University: {profile_dict.get('university')}")
print(f"Career: {profile_dict.get('career')}")
print(f"Languages: {profile_dict.get('languages')}")
print(f"Skills: {profile_dict.get('top_skills')}")
print(f"Interests: {profile_dict.get('interests')}")
print(f"\nCV Raw Text (primeros 300 chars): {cv_raw_text[:300]}")
```

**Qué validar:**
- [ ] Todos los campos están presentes (no None)
- [ ] Name es una cadena no vacía
- [ ] Languages es una lista con al menos 1 idioma
- [ ] Top_skills es una lista con habilidades
- [ ] cv_raw_text es el texto completo sin procesar

---

### **TEST 3: Verificar búsqueda de oportunidades**
```python
from src.services.hunter import search_opportunities_with_gemini

cv_raw_text = """
Manuel García
Estudiante de Ingeniería Informática
Universidad Nacional de Ingeniería (UNI) - Perú
Skills: Python, JavaScript, React, SQL
Intereses: AI, Web Development
Ambiciones: Trabajar en startups tecnológicas
"""

brain_dump_text = "Me interesa mucho hacer un intercambio en Europa o América del Norte"

opportunities = search_opportunities_with_gemini(
    cv_raw_text=cv_raw_text,
    brain_dump_text=brain_dump_text,
    profile_data=None,
    num_results=3
)

print(f"✓ Gemini encontró {len(opportunities)} oportunidades\n")
for i, opp in enumerate(opportunities, 1):
    print(f"{i}. {opp.get('title')}")
    print(f"   Empresa: {opp.get('company')}")
    print(f"   Tipo: {opp.get('opportunity_type')}")
    print(f"   Ubicación: {opp.get('location')}")
    print(f"   Deadline: {opp.get('deadline_info')}\n")
```

**Qué validar:**
- [ ] Se retornan exactamente N oportunidades
- [ ] Cada oportunidad tiene: title, company, location, url, description, opportunity_type, eligibility_level, deadline_info
- [ ] Las URLs parecen válidas (formato https://)
- [ ] El tipo es uno de: beca|pasantía|investigación|intercambio|concurso
- [ ] El nivel es uno de: pregrado|maestría|doctorado|todos
- [ ] Las oportunidades son relevantes al perfil del CV

---

### **TEST 4: Verificar evaluación/scoring de matches**
```python
from src.services.hunter import evaluate_match

cv_raw_text = """
Ingeniero de software con 2 años experiencia
Skills: Python, Django, React, PostgreSQL
Idiomas: Español, Inglés
Intereses: Startups, IA
"""

opportunity = {
    "title": "Software Engineer Internship",
    "company": "Google",
    "description": "Python development role for undergraduates",
    "opportunity_type": "pasantía",
    "eligibility_level": "pregrado"
}

evaluation = evaluate_match(
    cv_raw_text=cv_raw_text,
    brain_dump_text="Quiero una pasantía en Google",
    opportunity=opportunity,
    profile_data={}
)

print(f"Score: {evaluation['score']}/100")
print(f"Is Eligible: {evaluation['is_eligible']}")
print(f"Reason: {evaluation['reason']}")
print(f"Description: {evaluation['description']}")
print(f"Eligibility Notes: {evaluation['eligibility_notes']}")
```

**Qué validar:**
- [ ] Score está entre 0-100
- [ ] Cuando is_eligible=false, score=0
- [ ] Reason tiene una explicación clara
- [ ] Description es específico (no genérico)
- [ ] Los resultados son realistas para el match

---

### **TEST 5: Verificar guardado en DB**
```python
from src.services.db import save_student_profile
import json

profile_dict = {
    "name": "Juan Pérez",
    "university": "PUCP",
    "career": "Computer Science",
    "country": "Peru",
    "study_level": "pregrado",
    "languages": ["Spanish", "English"],
    "top_skills": ["Python", "React"],
    "interests": ["AI", "Startups"],
    "ambitions": "Work at a tech startup"
}

cv_raw_text = "Full CV text here..."
brain_dump_text = "Some additional context..."

saved_row = save_student_profile(
    profile=profile_dict,
    user_id="some-uuid",
    cv_raw_text=cv_raw_text,
    brain_dump_text=brain_dump_text
)

print(f"✓ Guardado en DB")
print(f"Student ID: {saved_row['id']}")
print(f"Name: {saved_row['name']}")
print(f"CV text guardado: {len(saved_row['cv_raw_text'])} chars")
print(f"Brain dump guardado: {len(saved_row['brain_dump_text'])} chars")

# Verificar que se guardó
from src.services.db import _get_supabase_client
supabase = _get_supabase_client()
verify = supabase.table("students").select("*").eq("id", saved_row['id']).execute()
print(f"\n✓ Verificación DB: {len(verify.data)} row encontrado")
```

**Qué validar:**
- [ ] Retorna una fila guardada con ID
- [ ] cv_raw_text en DB tiene la longitud correcta
- [ ] brain_dump_text se guarda correctamente
- [ ] El profile_data JSON es válido
- [ ] Se puede recuperar de la DB

---

### **TEST 6: Verificar búsqueda y scoring juntos (END-TO-END)**
```python
from src.services.hunter import find_and_save_matches

# Asumiendo que already existe un student_id en la DB
student_id = "some-student-uuid"

result = find_and_save_matches(student_id=student_id, num_results=3)

if "error" in result:
    print(f"❌ Error: {result['error']}")
else:
    print(f"✓ Proceso completado")
    print(f"  - Estudiante: {result['student_name']}")
    print(f"  - Oportunidades encontradas: {result['opportunities_count']}")
    print(f"  - Matches guardados: {result['matches_saved']}")
    
    # Verificar matches en DB
    from src.services.db import _get_supabase_client
    supabase = _get_supabase_client()
    matches = supabase.table("matches").select("*").eq("student_id", student_id).execute()
    
    print(f"\n  Matches en DB:")
    for match in matches.data:
        print(f"    • {match['opportunity']['title']}: {match['score']}/100")
```

**Qué validar:**
- [ ] No hay errores
- [ ] Se encontraron oportunidades
- [ ] Todos los matches tienen scores válidos
- [ ] Los matches aparecen en la DB
- [ ] Los datos se pueden recuperar

---

## 📐 Resumen de Datos por Etapa

| Etapa | Cantidad | Formato | Ubicación |
|-------|----------|---------|-----------|
| **Upload** | 1 base | PDF (CV) + Audio/Text | Temp disk |
| **Extract** | 1 CV + 1 Profile | Text (5K+ chars) + JSON | Memory |
| **Save Student** | 1 Row | JSON en Supabase | DB: `students` |
| **Search Opps** | 3-N | Array JSON | Memory (Gemini) |
| **Score** | 3-N | score + reason + desc | Memory |
| **Save Matches** | 3-N Rows | JSON + score | DB: `matches` |
| **Display** | 3-N Items | HTML+CSS | Browser |

---

## 🔐 Flujo de Autenticación

```
Usuario login → Crea session (JWT en cookie)
     ↓
/upload_profile access → check session
     ↓
Si válido → continúa
Si no → redirect /login
```

**Test de auth:**
```python
# En browser console después de login:
document.cookie  # Debe mostrar session cookies

# O en Python:
import requests
session = requests.Session()
# Login primero...
response = session.get('/upload_profile')
print(response.status_code)  # 200 = OK, 401 = Not auth
```

---

## ⚡ Puntos Clave para Debugging

1. **CV no se extrae bien** → Check `ai_agent.py extract_cv_text()` prompt
2. **Perfil vacío** → Check `analyze_profile()` parsing JSON
3. **Oportunidades repetidas** → Gemini generando, no filtrando
4. **Scores muy bajos/altos** → Revisar prompt en `evaluate_match()`
5. **No se guardan matches** → Check DB connection en `hunter.py line 330`

---

## 🎯 Próximos Pasos de Testing

```bash
# 1. Test unitario: Extract CV
pytest tests/test_cv_extraction.py

# 2. Test integración: Analyze Profile
pytest tests/test_profile_analysis.py

# 3. Test E2E: Full flow
pytest tests/test_end_to_end.py

# 4. Test manual: Login + Upload
# Ir a http://localhost:5000/ → Register → Upload CV
```
