"""
Script para limpiar datos históricos con ganancias irreales
"""
import json
import os
from datetime import datetime

def limpiar_resultados_historicos():
    """Limpia el archivo de resultados históricos eliminando ganancias irreales"""
    
    archivo = 'resultados_historicos.json'
    
    # Verificar si existe
    if not os.path.exists(archivo):
        print(f"❌ No existe el archivo {archivo}")
        return
    
    # Cargar datos
    try:
        with open(archivo, 'r') as f:
            datos = json.load(f)
        print(f"📊 Cargados {len(datos)} registros")
    except Exception as e:
        print(f"❌ Error cargando archivo: {e}")
        return
    
    # Filtrar datos
    datos_limpios = []
    registros_eliminados = 0
    
    for registro in datos:
        try:
            ganancia_d1 = float(registro.get('ganancia_d1', 0))
            ganancia_d2 = float(registro.get('ganancia_d2', 0))
            prima_entrada = float(registro.get('prima_entrada', 0))
            prima_max_d1 = float(registro.get('prima_max_d1', 0))
            
            # Criterios de limpieza:
            # 1. Ganancias mayores a 500% son irreales
            # 2. Primas de entrada menores a $0.05 son sospechosas
            # 3. Primas máximas mayores a $50 son sospechosas para estos tickers
            
            if (ganancia_d1 > 500 or ganancia_d2 > 500 or 
                prima_entrada < 0.05 or prima_entrada > 50 or
                prima_max_d1 > 50):
                
                registros_eliminados += 1
                print(f"❌ Eliminando: {registro.get('ticker')} - {registro.get('fecha')} - "
                      f"Ganancia D1: {ganancia_d1}% - Prima: ${prima_entrada}")
                continue
            
            # Si pasa los filtros, agregar a datos limpios
            datos_limpios.append(registro)
            
        except Exception as e:
            # Si hay error procesando el registro, eliminarlo
            registros_eliminados += 1
            continue
    
    # Guardar backup del original
    backup_name = f'resultados_historicos_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_name, 'w') as f:
        json.dump(datos, f, indent=2)
    print(f"💾 Backup guardado como: {backup_name}")
    
    # Guardar datos limpios
    with open(archivo, 'w') as f:
        json.dump(datos_limpios, f, indent=2)
    
    print(f"\n✅ LIMPIEZA COMPLETADA:")
    print(f"   - Registros originales: {len(datos)}")
    print(f"   - Registros eliminados: {registros_eliminados}")
    print(f"   - Registros limpios: {len(datos_limpios)}")
    print(f"   - Porcentaje eliminado: {(registros_eliminados/len(datos)*100):.1f}%")

def verificar_rangos_prima():
    """Verifica y muestra estadísticas de los datos"""
    
    archivo = 'resultados_historicos.json'
    
    if not os.path.exists(archivo):
        return
    
    with open(archivo, 'r') as f:
        datos = json.load(f)
    
    print("\n📊 ESTADÍSTICAS DE DATOS:")
    print("="*60)
    
    # Analizar ganancias
    ganancias_d1 = [float(r.get('ganancia_d1', 0)) for r in datos]
    ganancias_d1 = [g for g in ganancias_d1 if g > 0]  # Solo positivas
    
    if ganancias_d1:
        print(f"\nGANANCIAS DÍA 1:")
        print(f"   - Mínima: {min(ganancias_d1):.1f}%")
        print(f"   - Máxima: {max(ganancias_d1):.1f}%")
        print(f"   - Promedio: {sum(ganancias_d1)/len(ganancias_d1):.1f}%")
        
        # Contar por rangos
        rangos = {
            '0-100%': 0,
            '100-200%': 0,
            '200-300%': 0,
            '300-400%': 0,
            '400-500%': 0,
            '>500%': 0
        }
        
        for g in ganancias_d1:
            if g <= 100:
                rangos['0-100%'] += 1
            elif g <= 200:
                rangos['100-200%'] += 1
            elif g <= 300:
                rangos['200-300%'] += 1
            elif g <= 400:
                rangos['300-400%'] += 1
            elif g <= 500:
                rangos['400-500%'] += 1
            else:
                rangos['>500%'] += 1
        
        print("\n   DISTRIBUCIÓN:")
        for rango, cantidad in rangos.items():
            porcentaje = (cantidad/len(ganancias_d1)*100)
            print(f"   - {rango}: {cantidad} ({porcentaje:.1f}%)")

if __name__ == "__main__":
    print("🧹 LIMPIADOR DE DATOS HISTÓRICOS")
    print("="*60)
    
    # Primero mostrar estadísticas actuales
    print("\n📊 ESTADO ACTUAL:")
    verificar_rangos_prima()
    
    # Ejecutar limpieza automáticamente
    print("\n🔄 INICIANDO LIMPIEZA AUTOMÁTICA...")
    limpiar_resultados_historicos()
    
    # Mostrar estadísticas después de limpiar
    print("\n📊 ESTADO DESPUÉS DE LIMPIAR:")
    verificar_rangos_prima()