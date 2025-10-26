"""
Setup rápido para preparar el sistema antes del lunes

Ejecuta precálculos esenciales para asegurar que el sistema
funcione rápidamente en la apertura del mercado.
"""

import os
import subprocess
import time
from datetime import datetime, timedelta

print("🚀 PREPARACIÓN RÁPIDA PARA EL LUNES")
print("=" * 60)
print("Este script preparará el sistema para funcionar óptimamente")
print("en la apertura del mercado del lunes.")
print("=" * 60)

# Paso 1: Verificar que tenemos las credenciales
if not os.getenv('POLYGON_API_KEY'):
    print("❌ ERROR: No se encuentra POLYGON_API_KEY")
    print("Por favor configura tu API key en el archivo .env")
    exit(1)

print("\n✅ API Key configurada correctamente")

# Paso 2: Instalar dependencias si es necesario
print("\n📦 Verificando dependencias...")
try:
    import polygon
    import pandas
    import streamlit
    print("✅ Todas las dependencias instaladas")
except ImportError as e:
    print(f"⚠️ Instalando dependencias faltantes...")
    subprocess.run([f"{os.sys.executable}", "-m", "pip", "install", "-r", "requirements.txt"])

# Paso 3: Precalcular strikes para los próximos días
print("\n🔄 Iniciando precálculo de strikes óptimos...")
print("Esto tomará aproximadamente 5-10 minutos")
print("Por favor espera...\n")

try:
    # Calcular solo los últimos 30 días y próximos 5 días
    from precalcular_strikes import ejecutar_precalculo
    
    print("Procesando últimos 30 días + próximos 5 días...")
    ejecutar_precalculo(dias_atras=30, dias_adelante=5)
    
    print("\n✅ Precálculo completado exitosamente")
    
except Exception as e:
    print(f"❌ Error durante el precálculo: {e}")
    print("El sistema funcionará pero más lento")

# Paso 4: Verificar que todo está listo
print("\n🔍 VERIFICACIÓN FINAL:")
print("-" * 40)

# Verificar archivos necesarios
archivos_necesarios = [
    'app_v90b.py',
    'historial_operaciones.json',
    'resultados_historicos.json',
    'strikes_precalculados.db'
]

todos_presentes = True
for archivo in archivos_necesarios:
    if os.path.exists(archivo):
        print(f"✅ {archivo}")
    else:
        print(f"❌ {archivo} - FALTANTE")
        todos_presentes = False

# Verificar base de datos
if os.path.exists('strikes_precalculados.db'):
    from usar_strikes_precalculados import verificar_base_datos
    print("\n📊 Estado de la base de datos:")
    verificar_base_datos()

# Instrucciones finales
print("\n" + "="*60)
print("🎯 INSTRUCCIONES PARA EL LUNES:")
print("="*60)
print("\n1. Para iniciar el sistema:")
print("   streamlit run app_v90b.py")
print("\n2. El sistema ahora:")
print("   - Busca automáticamente la opción con MAYOR % de ganancia")
print("   - Respeta los rangos de prima configurados") 
print("   - Muestra las mejores 3 alternativas")
print("   - Los detalles históricos se ven al hacer click")
print("\n3. Si necesitas actualizar datos históricos:")
print("   - Usa el botón en la interfaz para cargar 4 meses")
print("\n4. La base de datos de strikes acelera las búsquedas")
print("   - Se actualiza automáticamente cada vez que usas el sistema")

if todos_presentes:
    print("\n✅ ¡SISTEMA LISTO PARA EL LUNES!")
else:
    print("\n⚠️ Hay archivos faltantes, revisa los mensajes arriba")

print("\n🚀 ¡Éxito en el trading del lunes! 📈")