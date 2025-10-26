"""
Funciones para usar los strikes precalculados desde la base de datos
en lugar de calcularlos en tiempo real.

Esto mejora significativamente el rendimiento y la confiabilidad.
"""

import sqlite3
from datetime import datetime, timedelta

def obtener_strike_precalculado(ticker, fecha_analisis):
    """
    Obtiene el strike óptimo precalculado desde la base de datos
    
    Args:
        ticker: El símbolo del activo (ej: 'SPY')
        fecha_analisis: La fecha para la cual buscar el strike
        
    Returns:
        dict con información del strike o None si no se encuentra
    """
    try:
        conn = sqlite3.connect('strikes_precalculados.db')
        cursor = conn.cursor()
        
        fecha_str = fecha_analisis.strftime('%Y-%m-%d')
        
        # Buscar strike exacto para esa fecha
        cursor.execute('''
        SELECT strike, prima_entrada, prima_maxima_esperada, 
               ganancia_esperada, fecha_vencimiento, precio_stock
        FROM strikes_optimos
        WHERE ticker = ? AND fecha_analisis = ?
        ''', (ticker, fecha_str))
        
        resultado = cursor.fetchone()
        
        if resultado:
            strike, prima_entrada, prima_maxima, ganancia, fecha_venc, precio_stock = resultado
            
            return {
                'strike': strike,
                'prima_entrada': prima_entrada,
                'prima_maxima_esperada': prima_maxima,
                'ganancia_esperada': ganancia,
                'fecha_vencimiento': fecha_venc,
                'precio_stock': precio_stock,
                'fuente': 'precalculado'
            }
        else:
            # Si no hay datos exactos, buscar el más cercano (máximo 3 días de diferencia)
            cursor.execute('''
            SELECT strike, prima_entrada, prima_maxima_esperada, 
                   ganancia_esperada, fecha_vencimiento, precio_stock,
                   fecha_analisis
            FROM strikes_optimos
            WHERE ticker = ? 
              AND fecha_analisis BETWEEN date(?, '-3 days') AND date(?, '+3 days')
            ORDER BY ABS(julianday(fecha_analisis) - julianday(?))
            LIMIT 1
            ''', (ticker, fecha_str, fecha_str, fecha_str))
            
            resultado_cercano = cursor.fetchone()
            
            if resultado_cercano:
                strike, prima, prima_max, ganancia, fecha_venc, precio, fecha_calc = resultado_cercano
                
                return {
                    'strike': strike,
                    'prima_entrada': prima,
                    'prima_maxima_esperada': prima_max,
                    'ganancia_esperada': ganancia,
                    'fecha_vencimiento': fecha_venc,
                    'precio_stock': precio,
                    'fuente': f'precalculado_cercano ({fecha_calc})',
                    'advertencia': f'Usando datos de {fecha_calc} (no hay datos exactos para {fecha_str})'
                }
        
        conn.close()
        return None
        
    except Exception as e:
        print(f"Error consultando base de datos: {e}")
        return None

def verificar_base_datos():
    """Verifica el estado de la base de datos de strikes precalculados"""
    try:
        conn = sqlite3.connect('strikes_precalculados.db')
        cursor = conn.cursor()
        
        # Contar total de registros
        cursor.execute('SELECT COUNT(*) FROM strikes_optimos')
        total = cursor.fetchone()[0]
        
        # Contar por ticker
        cursor.execute('''
        SELECT ticker, COUNT(*) as cantidad
        FROM strikes_optimos
        GROUP BY ticker
        ORDER BY ticker
        ''')
        
        print("=" * 60)
        print("📊 ESTADO DE LA BASE DE DATOS DE STRIKES PRECALCULADOS")
        print("=" * 60)
        print(f"Total de registros: {total}")
        print("\nRegistros por ticker:")
        print(f"{'Ticker':<10} {'Cantidad':<10}")
        print("-" * 20)
        
        for ticker, cantidad in cursor.fetchall():
            print(f"{ticker:<10} {cantidad:<10}")
        
        # Rango de fechas
        cursor.execute('''
        SELECT MIN(fecha_analisis), MAX(fecha_analisis)
        FROM strikes_optimos
        ''')
        
        fecha_min, fecha_max = cursor.fetchone()
        print(f"\nRango de fechas: {fecha_min} a {fecha_max}")
        
        # Últimos 5 registros
        cursor.execute('''
        SELECT ticker, fecha_analisis, strike, ganancia_esperada
        FROM strikes_optimos
        ORDER BY fecha_calculo DESC
        LIMIT 5
        ''')
        
        print("\nÚltimos 5 registros añadidos:")
        print(f"{'Ticker':<8} {'Fecha':<12} {'Strike':<8} {'Ganancia %':<12}")
        print("-" * 40)
        
        for row in cursor.fetchall():
            ticker, fecha, strike, ganancia = row
            print(f"{ticker:<8} {fecha:<12} ${strike:<7} {ganancia:<11.1f}%")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        print("💡 Ejecuta 'python precalcular_strikes.py' para crear la base de datos")

def ejemplo_uso():
    """Ejemplo de cómo usar los strikes precalculados"""
    print("\n📝 EJEMPLO DE USO")
    print("=" * 60)
    
    # Ejemplo 1: Obtener strike para SPY hoy
    ticker = 'SPY'
    fecha = datetime.now()
    
    resultado = obtener_strike_precalculado(ticker, fecha)
    
    if resultado:
        print(f"\n✅ Strike precalculado para {ticker} - {fecha.strftime('%Y-%m-%d')}:")
        print(f"   Strike: ${resultado['strike']}")
        print(f"   Prima entrada: ${resultado['prima_entrada']:.2f}")
        print(f"   Ganancia esperada: {resultado['ganancia_esperada']:.1f}%")
        print(f"   Fuente: {resultado['fuente']}")
        if 'advertencia' in resultado:
            print(f"   ⚠️ {resultado['advertencia']}")
    else:
        print(f"\n❌ No hay datos precalculados para {ticker} - {fecha.strftime('%Y-%m-%d')}")

def integrar_en_app():
    """
    Código de ejemplo para integrar en app_v90b.py
    
    En la función calcular_ganancia_real_opcion, añadir al inicio:
    """
    codigo_ejemplo = '''
# Al inicio de calcular_ganancia_real_opcion, añadir:

# Intentar obtener strike precalculado primero
try:
    from usar_strikes_precalculados import obtener_strike_precalculado
    
    strike_precalc = obtener_strike_precalculado(ticker, fecha)
    
    if strike_precalc:
        print(f"✅ Usando strike precalculado: ${strike_precalc['strike']}")
        print(f"   Prima esperada: ${strike_precalc['prima_entrada']:.2f}")
        print(f"   Ganancia esperada: {strike_precalc['ganancia_esperada']:.1f}%")
        
        # Usar estos valores para acelerar la búsqueda
        # ... continuar con la lógica usando el strike precalculado
except:
    # Si falla, continuar con el cálculo normal
    pass
'''
    
    print("\n💡 CÓDIGO PARA INTEGRAR EN app_v90b.py:")
    print("=" * 60)
    print(codigo_ejemplo)

if __name__ == "__main__":
    # Verificar estado de la base de datos
    verificar_base_datos()
    
    # Mostrar ejemplo de uso
    ejemplo_uso()
    
    # Mostrar cómo integrar
    integrar_en_app()