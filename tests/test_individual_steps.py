"""
SCRIPTS DE TESTING - Ejecutables paso a paso
Para probar cada parte del flujo sin tener que ir por la UI

Cómo usar:
1. Desde la terminal en el root del proyecto
2. Asegúrate que .venv esté activado
3. python tests/test_individual_steps.py
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv()

def separator(title):
    """Print a nice separator"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_1_gemini_connection():
    """TEST 1: ¿Gemini está configurado correctamente?"""
    separator("TEST 1: Gemini Connection")
    
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("❌ GEMINI_API_KEY no encontrado en .env")
            return False
        
        # Initialize client
        client = genai.Client(api_key=api_key)
        model_name = "gemini-2.5-flash"
        
        # Quick test
        response = client.models.generate_content(
            model=model_name,
            contents="Responde solo con: OK"
        )
        
        if response.text and "OK" in response.text:
            print("✅ Gemini conectado y funcionando")
            print(f"   API Key: {api_key[:10]}...{api_key[-10:]}")
            print(f"   Model: {model_name}")
            return True
        else:
            print(f"⚠️ Respuesta inesperada: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_2_supabase_connection():
    """TEST 2: ¿Supabase está configurado correctamente?"""
    separator("TEST 2: Supabase Connection")
    
    try:
        from src.services.db import _get_supabase_client
        
        supabase = _get_supabase_client()
        
        # Intenta hacer una query simple (solo trae 1 row para verificar conexión)
        response = supabase.table("students").select("id").limit(1).execute()
        
        print("✅ Supabase conectado")
        print(f"   Tabla 'students' accesible: ✓")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_3_cv_extraction():
    """TEST 3: ¿Se extrae bien el texto del CV?"""
    separator("TEST 3: CV Text Extraction")
    
    try:
        from src.services.ai_agent import GeminiAgent
        
        print("📁 Buscando archivo PDF para testing...")
        
        # Buscar un PDF de test
        test_pdf = Path("tests/sample_cv.pdf")
        if not test_pdf.exists():
            print(f"❓ No se encontró {test_pdf}")
            print("   Creando un CV de test mínimo...")
            
            # Si no existe, crear uno simple para demo
            try:
                from reportlab.pdfgen import canvas
                c = canvas.Canvas(str(test_pdf))
                c.drawString(100, 750, "CV SAMPLE")
                c.drawString(100, 730, "Name: John Doe")
                c.drawString(100, 710, "Degree: Computer Science")
                c.drawString(100, 690, "Skills: Python, React, SQL")
                c.save()
                print(f"   ✓ PDF creado: {test_pdf}")
            except:
                print("   ⚠️ Instala reportlab: pip install reportlab")
                return None
        
        agent = GeminiAgent()
        cv_text = agent.extract_cv_text(str(test_pdf))
        
        if cv_text and len(cv_text) > 50:
            print("✅ CV extraído correctamente")
            print(f"   Longitud: {len(cv_text)} caracteres")
            print(f"   Primeros 200 chars:\n   {cv_text[:200]}...")
            return cv_text
        else:
            print(f"❌ CV muy corto o vacío: {len(cv_text)} chars")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_4_profile_analysis():
    """TEST 4: ¿Se analiza bien el perfil?"""
    separator("TEST 4: Profile Analysis")
    
    try:
        from src.services.ai_agent import analyze_profile
        
        # Usar CV sample del test anterior
        test_pdf = Path("tests/sample_cv.pdf")
        if not test_pdf.exists():
            print("❌ Primero ejecuta TEST 3 para crear el sample CV")
            return None
        
        print("🔄 Analizando perfil...")
        profile_dict, cv_raw_text = analyze_profile(
            cv_file_path=str(test_pdf),
            audio_file_path=None,
            brain_dump_text="Interesado en becas de IA en Europa"
        )
        
        print("✅ Perfil analizado")
        print(f"\n📋 Datos extraídos:")
        print(f"   Name: {profile_dict.get('name', 'N/A')}")
        print(f"   University: {profile_dict.get('university', 'N/A')}")
        print(f"   Career: {profile_dict.get('career', 'N/A')}")
        print(f"   Country: {profile_dict.get('country', 'N/A')}")
        print(f"   Languages: {profile_dict.get('languages', [])}")
        print(f"   Top Skills: {profile_dict.get('top_skills', [])}")
        print(f"   Interests: {profile_dict.get('interests', [])}")
        print(f"\n📄 CV Raw Text: {len(cv_raw_text)} caracteres")
        print(f"   Primeros 150 chars: {cv_raw_text[:150]}...")
        
        return profile_dict, cv_raw_text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


# Shared test data for Tests 5 & 6
TEST_CV_DATA = """
Name: John Doe
Degree: Engineering - Computer Science
University: PUCP (Pontificia Universidad Católica del Perú)
Country: Peru
GPA: 3.8/4.0

Skills:
- Python (Advanced)
- JavaScript/React (Intermediate)
- SQL (Advanced)
- Machine Learning (Intermediate)

Experience:
- Software Developer Intern (6 months)
- Research Assistant in AI lab

Languages: Spanish (Native), English (Fluent)

Interests: Artificial Intelligence, Web Development, Startups
Ambitions: Work at a top tech company in Silicon Valley or Europe
"""

TEST_BRAIN_DUMP = "Quiero una beca o pasantía en Europa o USA para aprender más sobre IA"

# Global variable to store opportunities from TEST 5 for use in TEST 6
test_opportunities = None


def test_5_opportunity_search():
    """TEST 5: ¿Genera bien las oportunidades?"""
    separator("TEST 5: Opportunity Search")
    
    global test_opportunities
    
    try:
        from src.services.hunter import search_opportunities_with_gemini
        
        print("🔄 Buscando oportunidades...")
        print(f"   CV length: {len(TEST_CV_DATA)} chars")
        print(f"   Brain dump: '{TEST_BRAIN_DUMP[:50]}...'")
        
        opportunities = search_opportunities_with_gemini(
            cv_raw_text=TEST_CV_DATA,
            brain_dump_text=TEST_BRAIN_DUMP,
            profile_data=None,
            num_results=3
        )
        
        # Store for TEST 6
        test_opportunities = opportunities
        
        print(f"✅ Se encontraron {len(opportunities)} oportunidades\n")
        
        for i, opp in enumerate(opportunities, 1):
            print(f"{i}. {opp.get('title', 'N/A')}")
            print(f"   Company: {opp.get('company', 'N/A')}")
            print(f"   Type: {opp.get('opportunity_type', 'N/A')}")
            print(f"   Location: {opp.get('location', 'N/A')}")
            print(f"   URL: {opp.get('url', 'N/A')}")
            print(f"   Deadline: {opp.get('deadline_info', 'N/A')}")
            print()
        
        return opportunities
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_6_opportunity_scoring():
    """TEST 6: ¿Puntúa bien las oportunidades?"""
    separator("TEST 6: Opportunity Scoring")
    
    global test_opportunities
    
    try:
        from src.services.hunter import evaluate_match
        
        # TEST 6 requiere que TEST 5 se haya ejecutado exitosamente
        if test_opportunities is None or len(test_opportunities) == 0:
            print("❌ TEST 6 requiere que TEST 5 se ejecute primero")
            print("   No hay oportunidades para evaluar.")
            print("   Por favor ejecuta TEST 5 antes de TEST 6.\n")
            return None
        
        opportunities = test_opportunities
        
        print(f"✅ Usando {len(opportunities)} oportunidades de TEST 5")
        
        print("🔄 Evaluando matches...\n")
        
        scores = []
        for opp in opportunities:
            evaluation = evaluate_match(
                cv_raw_text=TEST_CV_DATA,
                brain_dump_text=TEST_BRAIN_DUMP,
                opportunity=opp,
                profile_data={}
            )
            
            title = opp.get('title', 'Unknown')
            score = evaluation['score']
            reason = evaluation['reason'][:70] if evaluation.get('reason') else "N/A"
            eligible = "✓" if evaluation.get('is_eligible', False) else "✗"
            
            print(f"[{eligible}] {title}")
            print(f"    Score: {score}/100")
            print(f"    Reason: {reason}...")
            print()
            
            scores.append(score)
        
        if scores:
            avg_score = sum(scores) / len(scores)
            print(f"✅ Scoring completado")
            print(f"   Scores: {scores}")
            print(f"   Promedio: {avg_score:.1f}/100")
        else:
            print(f"❌ No se pudieron evaluar las oportunidades")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_7_database_save():
    """TEST 7: ¿Se guarda bien en la base de datos?"""
    separator("TEST 7: Database Save")
    
    try:
        from src.services.db import save_student_profile, _get_supabase_client
        
        supabase = _get_supabase_client()
        
        # Use demo account credentials (isolated from personal account)
        # Credentials should be in .env file (never hardcode in source)
        DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@novo.app")
        DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "")
        
        print("👤 Usando cuenta demo para testing...")
        print(f"   Email: {DEMO_EMAIL}")
        print(f"   ℹ️ Completamente aislado de tu cuenta personal\n")
        
        try:
            # Login with demo account to get user_id
            auth_response = supabase.auth.sign_in_with_password({
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            })
            
            test_user_id = auth_response.user.id
            print(f"✓ Autenticado como demo: {test_user_id}")
            
        except Exception as auth_error:
            print(f"❌ Error en login: {auth_error}")
            print(f"   Verifica que la cuenta demo exista: {DEMO_EMAIL}")
            return None
        
        # Now save student profile with demo user
        profile_dict = {
            "name": "Test Student",
            "university": "Test University",
            "career": "Computer Science",
            "country": "Test Country",
            "study_level": "pregrado",
            "languages": ["Spanish", "English"],
            "top_skills": ["Python", "React"],
            "interests": ["AI", "Startups"],
            "ambitions": "Work at a tech company"
        }
        
        cv_raw_text = "This is test CV text with some content to verify storage" * 10
        brain_dump_text = "This is test brain dump"
        
        print("\n💾 Guardando student profile...")
        
        saved_row = save_student_profile(
            ai_result_json=profile_dict,
            user_id=test_user_id,
            cv_raw_text=cv_raw_text,
            brain_dump_text=brain_dump_text
        )
        
        if saved_row and saved_row.get('id'):
            student_id = saved_row['id']
            print(f"✅ Guardado exitosamente")
            print(f"   Student ID: {student_id}")
            print(f"   Name: {saved_row.get('name')}")
            print(f"   CV length in DB: {len(saved_row.get('cv_raw_text', ''))} chars")
            print(f"   Brain dump in DB: {len(saved_row.get('brain_dump_text', ''))} chars")
            
            # Verificar que se puede recuperar
            print("\n🔍 Verificando recuperación de datos...")
            supabase = _get_supabase_client()
            verify = supabase.table("students").select("*").eq("id", student_id).execute()
            
            if verify.data and len(verify.data) > 0:
                print(f"✅ Recuperada 1 row de la DB")
                
                # Optional cleanup
                print(f"\n🧹 Limpieza opcional")
                cleanup = input("   ¿Eliminar student profile de test? (s/n): ").strip().lower()
                
                if cleanup == 's':
                    try:
                        # Delete student profile only (keep user in auth.users)
                        supabase.table("students").delete().eq("id", student_id).execute()
                        print("   ✓ Student profile eliminado")
                        print(f"   ℹ️ Usuario en auth.users permanece intacto")
                    except Exception as e:
                        print(f"   ⚠️ Error en cleanup: {e}")
                else:
                    print(f"   ℹ️ Student profile permanece en DB")
                    print(f"   ℹ️ Puedes usar student_id={student_id} para TEST 8")
                
                return student_id
            else:
                print(f"❌ No se pudo recuperar de la DB")
                return None
        else:
            print(f"❌ Error al guardar")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_8_full_pipeline():
    """TEST 8: Pipeline completo (Search + Score + Save)"""
    separator("TEST 8: Full Pipeline (Search → Score → Save)")
    
    try:
        from src.services.hunter import find_and_save_matches
        from src.services.db import _get_supabase_client
        
        supabase = _get_supabase_client()
        
        # Demo account credentials (same as TEST 7)
        # Credentials should be in .env file (never hardcode in source)
        DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@novo.app")
        DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "")
        
        print("🔍 Buscando último student_id de la cuenta demo...")
        
        # Login with demo account
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            })
            demo_user_id = auth_response.user.id
        except Exception as e:
            print(f"❌ Error autenticando demo account: {e}")
            return None
        
        # Get latest student profile for demo user
        students = supabase.table("students").select("*").eq("user_id", demo_user_id).order("created_at", desc=True).limit(1).execute()
        
        if not students.data or len(students.data) == 0:
            print(f"❌ No hay student profiles para la cuenta demo")
            print(f"   Ejecuta TEST 7 primero para crear un student_id")
            return None
        
        student_id = students.data[0]['id']
        student_name = students.data[0]['name']
        
        print(f"✓ Encontrado: {student_id}")
        print(f"   Nome: {student_name}")
        print(f"   User: {demo_user_id}\n")
        
        print(f"🔄 Ejecutando pipeline para student_id: {student_id}")
        
        result = find_and_save_matches(student_id=student_id, num_results=3)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return None
        
        print(f"✅ Pipeline completado")
        print(f"   Estudiante: {result.get('student_name', 'Unknown')}")
        print(f"   Oportunidades encontradas: {result.get('opportunities_count', 0)}")
        print(f"   Matches guardados: {result.get('matches_saved', 0)}")
        
        # Verificar matches en DB
        matches = supabase.table("matches").select("*").eq("student_id", student_id).execute()
        
        if matches.data:
            print(f"\n📊 Matches en la base de datos:")
            for i, match in enumerate(matches.data, 1):
                opp = match.get('opportunity', {})
                score = match.get('score', 0)
                print(f"   {i}. {opp.get('title', 'N/A')} - {score}/100")
        else:
            print(f"\n⚠️ No hay matches guardados para este student")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Ejecuta todos los tests"""
    print("\n" + "="*60)
    print("  TESTING SUITE - Novo Project")
    print("="*60)
    print("\nEste script testa cada parte del flujo independientemente")
    print("Ejecuta los tests en orden para mejor debugging\n")
    
    tests = [
        ("Gemini Connection", test_1_gemini_connection),
        ("Supabase Connection", test_2_supabase_connection),
        ("CV Extraction", test_3_cv_extraction),
        ("Profile Analysis", test_4_profile_analysis),
        ("Opportunity Search", test_5_opportunity_search),
        ("Opportunity Scoring", test_6_opportunity_scoring),
        ("Database Save", test_7_database_save),
        ("Full Pipeline", test_8_full_pipeline),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        user_input = input(f"\n¿Ejecutar TEST: {test_name}? (s/n): ").strip().lower()
        if user_input == 's':
            result = test_func()
            results[test_name] = "✅ PASS" if result else "❌ FAIL"
        else:
            print(f"⏭️ Saltado")
            results[test_name] = "⏭️ SKIPPED"
    
    # Resumen
    separator("RESUMEN DE RESULTADOS")
    for test_name, result in results.items():
        print(f"{result} - {test_name}")
    print()


if __name__ == "__main__":
    main()
