#!/usr/bin/env python3
"""
Diagnóstico completo de la API de Polygon
"""

from polygon import RESTClient
import os
from datetime import datetime, timedelta
import json

API_KEY = input("Ingrese su POLYGON_API_KEY: ")
client = RESTClient(api_key=API_KEY)

print("="*80)
print("DIAGNÓSTICO DE API DE POLYGON")
print("="*80)

# 1. Verificar estado de la API
print("\n1️⃣ VERIFICANDO ESTADO DE LA API:")
try:
    # Intentar obtener datos de SPY (siempre tiene datos)
    test_data = client.get_aggs(
        ticker='SPY',
        multiplier=1,
        timespan='day',
        from_='2024-10-25',
        to='2024-10-25'
    )
    if test_data:
        print("   ✅ API funcionando correctamente")
        print(f"   Datos de prueba (SPY): ${test_data[0].close:.2f}")
    else:
        print("   ⚠️ API responde pero sin datos")
except Exception as e:
    print(f"   ❌ Error de API: {e}")

# 2. Verificar límites del plan
print("\n2️⃣ VERIFICANDO LÍMITES Y PLAN:")
print("   Plan Developer incluye:")
print("   - Datos históricos de opciones")
print("   - Agregados de 1 minuto")
print("   - Sin límite de requests por minuto")

# 3. Probar diferentes tipos de datos
casos_test = [
    {
        'descripcion': 'Stock BAC (diario)',
        'ticker': 'BAC',
        'tipo': 'stock',
        'timespan': 'day',
        'multiplier': 1,
        'fecha': '2024-10-28'
    },
    {
        'descripcion': 'Opción BAC PUT $40.5 venc Nov 1',
        'ticker': 'O:BAC241101P00040500',
        'tipo': 'option',
        'timespan': 'day',
        'multiplier': 1,
        'fecha': '2024-10-28'
    },
    {
        'descripcion': 'Misma opción - datos minuto',
        'ticker': 'O:BAC241101P00040500',
        'tipo': 'option',
        'timespan': 'minute',
        'multiplier': 1,
        'fecha': '2024-10-28'
    }
]

print("\n3️⃣ PROBANDO DIFERENTES TIPOS DE DATOS:")
print("-"*60)

for caso in casos_test:
    print(f"\n➤ {caso['descripcion']}")
    print(f"   Ticker: {caso['ticker']}")
    
    try:
        data = client.get_aggs(
            ticker=caso['ticker'],
            multiplier=caso['multiplier'],
            timespan=caso['timespan'],
            from_=caso['fecha'],
            to=caso['fecha'],
            limit=1000
        )
        
        if data:
            print(f"   ✅ Datos obtenidos: {len(data)} agregados")
            
            if caso['tipo'] == 'option' and caso['timespan'] == 'minute':
                # Analizar datos de opciones
                opens = [agg.open for agg in data if agg.open > 0]
                highs = [agg.high for agg in data if agg.high > 0]
                volumes = [agg.volume for agg in data]
                
                if opens and highs:
                    print(f"   Primer open: ${opens[0]:.2f}")
                    print(f"   Rango opens: ${min(opens):.2f} - ${max(opens):.2f}")
                    print(f"   Rango highs: ${min(highs):.2f} - ${max(highs):.2f}")
                    print(f"   Volumen total: {sum(volumes)}")
                    
                    # Verificar si hay datos sospechosos
                    if max(highs) / min(opens) > 1.5:
                        print(f"   ⚠️ VARIACIÓN SOSPECHOSA: {((max(highs) / min(opens) - 1) * 100):.1f}%")
                
                # Mostrar primeros 5 agregados
                print(f"\n   Primeros agregados:")
                for i in range(min(5, len(data))):
                    agg = data[i]
                    hora = datetime.fromtimestamp(agg.timestamp/1000).strftime('%H:%M')
                    print(f"   {hora}: O=${agg.open:.2f} H=${agg.high:.2f} L=${agg.low:.2f} C=${agg.close:.2f} Vol={agg.volume}")
            
            elif caso['tipo'] == 'option' and caso['timespan'] == 'day':
                agg = data[0]
                print(f"   Open: ${agg.open:.2f}")
                print(f"   High: ${agg.high:.2f}")
                print(f"   Low: ${agg.low:.2f}")
                print(f"   Close: ${agg.close:.2f}")
                print(f"   Volume: {agg.volume}")
                
        else:
            print(f"   ❌ Sin datos disponibles")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

# 4. Verificar formato de contratos
print("\n4️⃣ VERIFICANDO FORMATO DE CONTRATOS:")
print("-"*60)

# BAC precio actual aproximado
precio_bac = 41.0
strikes_bac = [40.0, 40.5, 41.0, 41.5, 42.0]

print(f"\nOpciones PUT de BAC (precio ~${precio_bac:.2f}):")
fecha_hoy = datetime.strptime('2024-10-28', '%Y-%m-%d')
viernes = fecha_hoy + timedelta(days=(4 - fecha_hoy.weekday()) % 7 or 7)

for strike in strikes_bac:
    strike_mult = int(strike * 1000)
    ticker_v1 = f"O:BAC{viernes.strftime('%y%m%d')}P{strike_mult:08d}"
    ticker_v2 = f"O:BAC{viernes.strftime('%y%m%d')}P00{strike_mult:06d}"
    
    print(f"\nStrike ${strike}:")
    print(f"  Formato 1: {ticker_v1}")
    print(f"  Formato 2: {ticker_v2}")
    
    # Probar ambos formatos
    for formato, ticker in [("F1", ticker_v1), ("F2", ticker_v2)]:
        try:
            data = client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan='day',
                from_='2024-10-28',
                to='2024-10-28',
                limit=1
            )
            if data:
                print(f"  {formato} ✅: High=${data[0].high:.2f}")
            else:
                print(f"  {formato} ❌: Sin datos")
        except:
            print(f"  {formato} ❌: Error")

print("\n" + "="*80)
print("CONCLUSIONES:")
print("1. Verificar si la API devuelve datos para las opciones")
print("2. Verificar el formato correcto del ticker de opciones")
print("3. Verificar si los datos tienen sentido (no hay saltos enormes)")
print("4. Si no hay datos, puede ser que no haya habido trading ese día")