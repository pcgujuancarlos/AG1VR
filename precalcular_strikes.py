"""
Rutina para pre-calcular y guardar en base de datos los strikes óptimos
para cada ticker/fecha basándose en el rango de primas configurado.

Esto asegura rapidez y fiabilidad para el trading del lunes.
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from polygon import RESTClient
from dotenv import load_dotenv
import time

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')
client = RESTClient(API_KEY)

# Configuración de rangos de primas (importado desde app_v90b.py)
RANGOS_PRIMA = {
    'SPY': {'min': 0.25, 'max': 0.30, 'vencimiento': 'siguiente_dia'},
    'QQQ': {'min': 0.25, 'max': 0.30, 'vencimiento': 'siguiente_dia'},
    'AAPL': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'AMD': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'AMZN': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'META': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'MSFT': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'GOOGL': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'NVDA': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'TSLA': {'min': 2.50, 'max': 3.00, 'vencimiento': 'viernes'},
    'NFLX': {'min': 1.50, 'max': 2.50, 'vencimiento': 'viernes'},
    'MRNA': {'min': 2.00, 'max': 2.00, 'vencimiento': 'viernes'},
    'BAC': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'SLV': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'USO': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'GLD': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'TNA': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'XOM': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'CVX': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'PLTR': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'BABA': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'CMG': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'SMCI': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'AVGO': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'CORZ': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'BBAI': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'SOUN': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'LAC': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'RKLB': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'POWI': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'CRWD': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'IREN': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'TIGO': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'RR': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'}
}

def crear_base_datos():
    """Crear la base de datos SQLite para almacenar los strikes precalculados"""
    conn = sqlite3.connect('strikes_precalculados.db')
    cursor = conn.cursor()
    
    # Crear tabla si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS strikes_optimos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        fecha_analisis DATE NOT NULL,
        fecha_vencimiento DATE NOT NULL,
        precio_stock REAL NOT NULL,
        strike INTEGER NOT NULL,
        prima_entrada REAL NOT NULL,
        prima_maxima_esperada REAL,
        ganancia_esperada REAL,
        fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ticker, fecha_analisis)
    )
    ''')
    
    conn.commit()
    return conn

def calcular_fecha_vencimiento(fecha_senal, ticker):
    """Calcula la fecha de vencimiento correcta para el ticker"""
    rango = RANGOS_PRIMA.get(ticker, {})
    tipo_vencimiento = rango.get('vencimiento', 'viernes')
    
    if tipo_vencimiento == 'siguiente_dia':
        fecha_venc = fecha_senal + timedelta(days=1)
        while fecha_venc.weekday() >= 5:
            fecha_venc += timedelta(days=1)
        return fecha_venc
    else:
        dia_semana = fecha_senal.weekday()
        if dia_semana <= 4:
            dias_hasta_viernes = 4 - dia_semana
        else:
            dias_hasta_viernes = 5 if dia_semana == 5 else 4
        fecha_venc = fecha_senal + timedelta(days=dias_hasta_viernes)
        return fecha_venc

def precalcular_strike_optimo(ticker, fecha, precio_stock, conn):
    """Pre-calcula el strike óptimo para un ticker/fecha específico"""
    try:
        rango = RANGOS_PRIMA[ticker]
        fecha_vencimiento = calcular_fecha_vencimiento(fecha, ticker)
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        print(f"\n🔍 Analizando {ticker} - {fecha_str}")
        print(f"   Precio: ${precio_stock:.2f}")
        print(f"   Rango prima: ${rango['min']:.2f} - ${rango['max']:.2f}")
        
        # Generar contratos potenciales
        contratos = []
        fecha_venc_str = fecha_vencimiento.strftime('%y%m%d')
        
        # Generar strikes desde 15% ITM hasta 5% OTM
        strike_min = int(precio_stock * 0.85)
        strike_max = int(precio_stock * 1.05)
        
        # Step según ticker
        if ticker in ['SPY', 'QQQ']:
            step = 1
        elif ticker in ['TSLA']:
            step = 5
        else:
            step = 1 if precio_stock < 100 else 5
        
        mejores_candidatos = []
        
        for strike in range(strike_min, strike_max + 1, step):
            option_ticker = f"O:{ticker}{fecha_venc_str}P{strike*1000:08d}"
            distancia_pct = ((strike - precio_stock) / precio_stock) * 100
            
            # Solo considerar strikes razonables
            if distancia_pct < -15 or distancia_pct > 5:
                continue
            
            try:
                # Obtener datos históricos para este strike
                option_aggs = client.get_aggs(
                    ticker=option_ticker,
                    multiplier=1,
                    timespan="minute",
                    from_=fecha_str,
                    to=fecha_str,
                    limit=500
                )
                
                time.sleep(0.1)  # Rate limiting
                
                if option_aggs and len(option_aggs) > 0:
                    todos_precios = []
                    for agg in option_aggs:
                        todos_precios.extend([agg.open, agg.high, agg.low, agg.close])
                    
                    max_precio = max(todos_precios)
                    
                    # Buscar primas en el rango
                    primas_en_rango = [p for p in todos_precios if rango['min'] <= p <= rango['max']]
                    
                    if primas_en_rango:
                        # Calcular ganancia potencial para cada prima
                        for prima in primas_en_rango[:1]:  # Solo la primera
                            ganancia_pct = ((max_precio - prima) / prima * 100) if prima > 0 else 0
                            
                            mejores_candidatos.append({
                                'strike': strike,
                                'prima_entrada': prima,
                                'prima_maxima': max_precio,
                                'ganancia_esperada': ganancia_pct,
                                'distancia_otm': distancia_pct
                            })
                            
                            print(f"   ✅ Strike ${strike}: Prima ${prima:.2f} → Ganancia {ganancia_pct:.1f}%")
                            break
            
            except Exception as e:
                if "NOT_AUTHORIZED" not in str(e):
                    print(f"   ❌ Error en strike ${strike}: {str(e)}")
                continue
        
        # Seleccionar el mejor candidato
        if mejores_candidatos:
            # Ordenar por mayor ganancia esperada
            mejores_candidatos.sort(key=lambda x: x['ganancia_esperada'], reverse=True)
            mejor = mejores_candidatos[0]
            
            # Guardar en base de datos
            cursor = conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO strikes_optimos 
            (ticker, fecha_analisis, fecha_vencimiento, precio_stock, strike, 
             prima_entrada, prima_maxima_esperada, ganancia_esperada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ticker,
                fecha_str,
                fecha_vencimiento.strftime('%Y-%m-%d'),
                precio_stock,
                mejor['strike'],
                mejor['prima_entrada'],
                mejor['prima_maxima'],
                mejor['ganancia_esperada']
            ))
            conn.commit()
            
            print(f"   💾 GUARDADO: Strike ${mejor['strike']} con ganancia esperada {mejor['ganancia_esperada']:.1f}%")
            return True
        else:
            print(f"   ⚠️ No se encontraron opciones viables")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR GENERAL: {str(e)}")
        return False

def ejecutar_precalculo(dias_atras=120, dias_adelante=5):
    """Ejecuta el precálculo para un rango de fechas"""
    print("🚀 INICIANDO PRECÁLCULO DE STRIKES ÓPTIMOS")
    print("=" * 80)
    
    # Crear/abrir base de datos
    conn = crear_base_datos()
    
    # Fechas a procesar
    fecha_inicio = datetime.now() - timedelta(days=dias_atras)
    fecha_fin = datetime.now() + timedelta(days=dias_adelante)
    
    print(f"📅 Rango de fechas: {fecha_inicio.strftime('%Y-%m-%d')} a {fecha_fin.strftime('%Y-%m-%d')}")
    print(f"📊 Tickers a procesar: {len(RANGOS_PRIMA)}")
    
    total_procesados = 0
    total_guardados = 0
    
    # Procesar cada ticker
    for ticker in RANGOS_PRIMA.keys():
        print(f"\n{'='*60}")
        print(f"📈 PROCESANDO: {ticker}")
        print(f"{'='*60}")
        
        ticker_guardados = 0
        
        # Procesar cada día
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            # Solo días hábiles
            if fecha_actual.weekday() < 5:
                try:
                    # Obtener precio del stock para ese día
                    fecha_str = fecha_actual.strftime('%Y-%m-%d')
                    
                    stock_aggs = client.get_aggs(
                        ticker=ticker,
                        multiplier=1,
                        timespan="day",
                        from_=fecha_str,
                        to=fecha_str,
                        limit=1
                    )
                    
                    time.sleep(0.1)  # Rate limiting
                    
                    if stock_aggs and len(stock_aggs) > 0:
                        precio_stock = stock_aggs[0].close
                        
                        # Precalcular strike óptimo
                        if precalcular_strike_optimo(ticker, fecha_actual, precio_stock, conn):
                            ticker_guardados += 1
                            total_guardados += 1
                    
                    total_procesados += 1
                    
                except Exception as e:
                    if "NOT_FOUND" not in str(e):
                        print(f"   ⚠️ Error procesando {fecha_str}: {str(e)}")
            
            fecha_actual += timedelta(days=1)
        
        print(f"\n✅ {ticker} completado: {ticker_guardados} días guardados")
    
    # Resumen final
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)
    print(f"Total días procesados: {total_procesados}")
    print(f"Total strikes guardados: {total_guardados}")
    print(f"Tasa de éxito: {(total_guardados/total_procesados*100):.1f}%" if total_procesados > 0 else "N/A")
    
    # Mostrar algunos ejemplos de la base de datos
    cursor = conn.cursor()
    cursor.execute('''
    SELECT ticker, fecha_analisis, strike, prima_entrada, ganancia_esperada
    FROM strikes_optimos
    ORDER BY fecha_analisis DESC, ganancia_esperada DESC
    LIMIT 10
    ''')
    
    print("\n📋 Últimos 10 registros guardados:")
    print(f"{'Ticker':<8} {'Fecha':<12} {'Strike':<8} {'Prima':<8} {'Ganancia':<10}")
    print("-" * 50)
    
    for row in cursor.fetchall():
        ticker, fecha, strike, prima, ganancia = row
        print(f"{ticker:<8} {fecha:<12} ${strike:<7} ${prima:<7.2f} {ganancia:<9.1f}%")
    
    conn.close()
    print("\n✅ Base de datos 'strikes_precalculados.db' creada exitosamente")

if __name__ == "__main__":
    # Ejecutar precálculo
    # Por defecto: 120 días hacia atrás y 5 días hacia adelante
    ejecutar_precalculo(dias_atras=120, dias_adelante=5)