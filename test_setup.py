#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión con Supabase
Ejecuta este script para asegurarte de que tu configuración está correcta
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_environment_variables():
    """Verificar que las variables de entorno estén configuradas"""
    print("🔍 Verificando variables de entorno...")
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or not value.strip():
            missing_vars.append(var)
            print(f"   ❌ {var}: NO CONFIGURADA")
        else:
            print(f"   ✅ {var}: Configurada")
    
    if missing_vars:
        print(f"\n⚠️  Faltan las siguientes variables: {', '.join(missing_vars)}")
        print("   Por favor, configura el archivo .env")
        return False
    
    print("✅ Todas las variables de entorno están configuradas\n")
    return True

def test_supabase_connection():
    """Verificar conexión con Supabase"""
    print("🔍 Probando conexión con Supabase...")
    
    try:
        from src.services.db import _get_supabase_client
        
        client = _get_supabase_client()
        print("   ✅ Cliente de Supabase creado exitosamente")
        
        # Intentar una consulta simple
        try:
            response = client.table("students").select("id").limit(1).execute()
            print("   ✅ Conexión a la base de datos exitosa")
            print(f"   📊 Tabla 'students' es accesible")
        except Exception as e:
            if "relation" in str(e).lower() and "does not exist" in str(e).lower():
                print("   ⚠️  La tabla 'students' no existe aún")
                print("   💡 Necesitas crear las tablas en Supabase")
            else:
                print(f"   ⚠️  Error al consultar la tabla: {e}")
        
        print("✅ Conexión con Supabase exitosa\n")
        return True
        
    except ValueError as e:
        print(f"   ❌ Error: {e}")
        print("   💡 Verifica que SUPABASE_URL y SUPABASE_KEY estén correctas\n")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}\n")
        return False

def test_auth_functions():
    """Verificar que las funciones de autenticación estén disponibles"""
    print("🔍 Verificando funciones de autenticación...")
    
    try:
        from src.services.auth import (
            register_user,
            login_user,
            logout_user,
            login_required,
            is_authenticated,
            get_current_user
        )
        
        functions = [
            'register_user',
            'login_user', 
            'logout_user',
            'login_required',
            'is_authenticated',
            'get_current_user'
        ]
        
        for func in functions:
            print(f"   ✅ {func}")
        
        print("✅ Todas las funciones de autenticación están disponibles\n")
        return True
        
    except ImportError as e:
        print(f"   ❌ Error al importar: {e}\n")
        return False

def test_flask_config():
    """Verificar configuración de Flask"""
    print("🔍 Verificando configuración de Flask...")
    
    try:
        from app import app
        
        if app.config.get('SECRET_KEY'):
            print("   ✅ SECRET_KEY configurada en Flask")
        else:
            print("   ❌ SECRET_KEY no configurada en Flask")
            return False
        
        if app.config.get('UPLOAD_FOLDER'):
            print("   ✅ UPLOAD_FOLDER configurada")
        else:
            print("   ⚠️  UPLOAD_FOLDER no configurada")
        
        print("✅ Configuración de Flask correcta\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*60)
    print("  🧪 PRUEBA DE CONFIGURACIÓN - NOVO AUTH SYSTEM")
    print("="*60 + "\n")
    
    tests = [
        ("Variables de Entorno", test_environment_variables),
        ("Conexión Supabase", test_supabase_connection),
        ("Funciones de Auth", test_auth_functions),
        ("Configuración Flask", test_flask_config)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en prueba '{test_name}': {e}\n")
            results.append((test_name, False))
    
    # Resumen
    print("="*60)
    print("  📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron! Tu configuración está lista.")
        print("💡 Ejecuta 'python3 app.py' para iniciar la aplicación\n")
        return 0
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
        print("💡 Consulta QUICK_START.md para ayuda con la configuración\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
