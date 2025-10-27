#!/usr/bin/env python3
"""
Debug: Verificar cálculo de prima máxima día 1
"""

from polygon import RESTClient
import os
from datetime import datetime, timedelta

API_KEY = input("Ingrese su POLYGON_API_KEY: ")
client = RESTClient(api_key=API_KEY)

# Caso específico para debug
ticker = 'CORZ'
fecha_str = '2024-10-24'
strike = 14.0

# Calcular fecha de vencimiento
fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
dias_hasta_viernes = (4 - fecha_obj.weekday()) % 7
if dias_hasta_viernes == 0:
    dias_hasta_viernes = 7
fecha_vencimiento = fecha_obj + timedelta(days=dias_hasta_viernes)

# Contrato
strike_mult = int(strike * 1000)
option_ticker = f"O:{ticker}{fecha_vencimiento.strftime('%y%m%d')}P{strike_mult:08d}"

print(f"Analizando: {option_ticker}")
print(f"Fecha: {fecha_str}")
print("="*60)

# Obtener TODOS los datos del día
try:
    option_aggs = client.get_aggs(
        ticker=option_ticker,
        multiplier=1,
        timespan="minute",
        from_=fecha_str,
        to=fecha_str,
        limit=50000
    )
    
    if option_aggs:
        print(f"\nTotal de agregados: {len(option_aggs)}")
        
        # Analizar los primeros y últimos datos
        print("\nPrimeros 5 minutos:")
        for i, agg in enumerate(option_aggs[:5]):
            hora = datetime.fromtimestamp(agg.timestamp/1000).strftime('%H:%M:%S')
            print(f"  {hora}: O=${agg.open:.2f} H=${agg.high:.2f} L=${agg.low:.2f} C=${agg.close:.2f}")
        
        print("\nÚltimos 5 minutos:")
        for i, agg in enumerate(option_aggs[-5:]):
            hora = datetime.fromtimestamp(agg.timestamp/1000).strftime('%H:%M:%S')
            print(f"  {hora}: O=${agg.open:.2f} H=${agg.high:.2f} L=${agg.low:.2f} C=${agg.close:.2f}")
        
        # Estadísticas generales
        todos_open = [agg.open for agg in option_aggs]
        todos_high = [agg.high for agg in option_aggs]
        todos_low = [agg.low for agg in option_aggs]
        todos_close = [agg.close for agg in option_aggs]
        
        print("\nESTADÍSTICAS DEL DÍA:")
        print(f"  Open: min=${min(todos_open):.2f}, max=${max(todos_open):.2f}")
        print(f"  High: min=${min(todos_high):.2f}, max=${max(todos_high):.2f}")
        print(f"  Low:  min=${min(todos_low):.2f}, max=${max(todos_low):.2f}")
        print(f"  Close: min=${min(todos_close):.2f}, max=${max(todos_close):.2f}")
        
        print(f"\n📊 PRIMA MÁXIMA DEL DÍA: ${max(todos_high):.2f}")
        
        # Buscar primas en rango típico
        rango = {'min': 0.10, 'max': 0.70}  # Rango para CORZ
        
        # Solo open y close para entrada
        precios_entrada = []
        for agg in option_aggs:
            precios_entrada.extend([agg.open, agg.close])
        
        primas_en_rango = [p for p in precios_entrada if rango['min'] <= p <= rango['max']]
        
        if primas_en_rango:
            print(f"\nPrimas de entrada en rango ({len(primas_en_rango)} encontradas):")
            # Mostrar las primeras 10
            for i, prima in enumerate(sorted(set(primas_en_rango))[:10]):
                print(f"  ${prima:.2f}")
            
            prima_entrada_min = min(primas_en_rango)
            prima_entrada_max = max(primas_en_rango)
            
            print(f"\nRango de primas entrada: ${prima_entrada_min:.2f} - ${prima_entrada_max:.2f}")
            
            # Calcular ganancias potenciales
            max_high = max(todos_high)
            print(f"\nGANANCIAS POTENCIALES:")
            print(f"  Con prima entrada ${prima_entrada_min:.2f}: {((max_high - prima_entrada_min) / prima_entrada_min * 100):.1f}%")
            print(f"  Con prima entrada ${prima_entrada_max:.2f}: {((max_high - prima_entrada_max) / prima_entrada_max * 100):.1f}%")
        
    else:
        print("❌ No hay datos disponibles")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)
print("ANÁLISIS:")
print("1. Verificar que el max(high) es correcto")
print("2. Verificar que las primas de entrada son realistas")
print("3. Confirmar que no hay datos anómalos")