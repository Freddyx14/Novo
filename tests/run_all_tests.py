"""
Script para ejecutar todos los tests automáticamente
"""

import sys
import os

# Add the parent directory to sys.path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all the test functions
from test_individual_steps import (
    test_1_gemini_connection,
    test_2_supabase_connection,
    test_3_cv_extraction,
    test_4_profile_analysis,
    test_5_opportunity_search,
    test_6_opportunity_scoring,
    test_7_database_save,
    test_8_full_pipeline
)

def run_all():
    """Run all tests in sequence"""
    tests = [
        ("Gemini Connection", test_1_gemini_connection),
        ("Supabase Connection", test_2_supabase_connection),
        ("CV Extraction", test_3_cv_extraction),
        ("Profile Analysis", test_4_profile_analysis),
        ("Opportunity Search", test_5_opportunity_search),
        ("Opportunity Scoring", test_6_opportunity_scoring),
        ("Database Save", test_7_database_save),
        ("Full Pipeline", test_8_full_pipeline)
    ]
    
    results = []
    
    print("=" * 60)
    print("  EJECUTANDO TODOS LOS TESTS AUTOMÁTICAMENTE")
    print("=" * 60)
    print()
    
    for name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"  TEST: {name}")
        print('=' * 60)
        print()
        
        try:
            test_func()
            results.append((name, "✅ PASSED"))
        except Exception as e:
            results.append((name, f"❌ FAILED: {str(e)}"))
            print(f"\n❌ Test falló: {e}")
    
    # Summary
    print("\n\n" + "=" * 60)
    print("  RESUMEN DE TESTS")
    print("=" * 60)
    
    for name, result in results:
        print(f"{name}: {result}")
    
    passed = sum(1 for _, r in results if r.startswith("✅"))
    total = len(results)
    
    print(f"\n{passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(run_all())
