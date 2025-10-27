#!/usr/bin/env python3
"""
Verificación ESPECÍFICA: MSFT Oct 24, 2024 Strike $410 PUT
"""

from polygon import RESTClient
import os
from datetime import datetime, timedelta
import pandas as pd

# API Key
API_KEY = input("Ingrese su POLYGON_API_KEY: ")
client = RESTClient(api_key=API_KEY)

# Datos específicos
ticker = 'MSFT'
fecha_str = '2024-10-24'
strike = 410.0

print("="*80)
print(f"VERIFICACIÓN DETALLADA: {ticker} PUT ${strike} - {fecha_str}")
print("="*80)

# Calcular fecha de vencimiento (siguiente viernes)
fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
dias_hasta_viernes = (4 - fecha_obj.weekday()) % 7
if dias_hasta_viernes == 0:
    dias_hasta_viernes = 7
fecha_vencimiento = fecha_obj + timedelta(days=dias_hasta_viernes)

# Construir ticker de la opción
strike_mult = int(strike * 1000)
option_ticker = f"O:{ticker}{fecha_vencimiento.strftime('%y%m%d')}P{strike_mult:08d}"

print(f"\nContrato: {option_ticker}")
print(f"Fecha vencimiento: {fecha_vencimiento.strftime('%Y-%m-%d')} (Viernes)")

# 1. Verificar precio del subyacente
print(f"\n1️⃣ PRECIO DEL SUBYACENTE {ticker}:")
print("-"*50)
try:
    stock_data = client.get_aggs(
        ticker=ticker,
        multiplier=1,
        timespan='day',
        from_=fecha_str,
        to=fecha_str
    )
    if stock_data:
        for d in stock_data:
            print(f"   Precio cierre: ${d.close:.2f}")
            print(f"   Rango del día: ${d.low:.2f} - ${d.high:.2f}")
except Exception as e:
    print(f"   Error: {e}")

# 2. Datos DIARIOS de la opción
print(f"\n2️⃣ DATOS DIARIOS DE LA OPCIÓN:")
print("-"*50)
try:
    daily_option = client.get_aggs(
        ticker=option_ticker,
        multiplier=1,
        timespan='day',
        from_=fecha_str,
        to=fecha_str
    )
    if daily_option:
        for d in daily_option:
            print(f"   Open:  ${d.open:.2f}")
            print(f"   High:  ${d.high:.2f} ⬅️ MÁXIMO REAL DEL DÍA")
            print(f"   Low:   ${d.low:.2f}")
            print(f"   Close: ${d.close:.2f}")
            print(f"   Volume: {d.volume}")
    else:
        print("   ❌ Sin datos diarios")
except Exception as e:
    print(f"   Error: {e}")

# 3. Datos por MINUTO
print(f"\n3️⃣ ANÁLISIS DETALLADO POR MINUTO:")
print("-"*50)
try:
    minute_data = client.get_aggs(
        ticker=option_ticker,
        multiplier=1,
        timespan='minute',
        from_=fecha_str,
        to=fecha_str,
        limit=50000
    )
    
    if minute_data:
        # Crear DataFrame para análisis
        data = []
        for agg in minute_data:
            data.append({
                'time': datetime.fromtimestamp(agg.timestamp/1000),
                'open': agg.open,
                'high': agg.high,
                'low': agg.low,
                'close': agg.close
            })
        
        df = pd.DataFrame(data)
        
        print(f"   Total minutos con datos: {len(df)}")
        print(f"   Hora inicio: {df['time'].min().strftime('%H:%M:%S')}")
        print(f"   Hora fin: {df['time'].max().strftime('%H:%M:%S')}")
        print(f"\n   ESTADÍSTICAS:")
        print(f"   - HIGH máximo del día: ${df['high'].max():.2f} ⬅️ ESTE ES EL VERDADERO MÁXIMO")
        print(f"   - LOW mínimo del día: ${df['low'].min():.2f}")
        print(f"   - Rango completo: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        
        # Buscar primas típicas de entrada (0.50-3.00 para MSFT)
        rango_min, rango_max = 0.50, 3.00
        print(f"\n   PRIMAS EN RANGO ${rango_min:.2f}-${rango_max:.2f}:")
        
        # Revisar opens y closes
        precios_entrada = []
        for _, row in df.iterrows():
            if rango_min <= row['open'] <= rango_max:
                precios_entrada.append(row['open'])
            if rango_min <= row['close'] <= rango_max:
                precios_entrada.append(row['close'])
        
        if precios_entrada:
            prima_min = min(precios_entrada)
            prima_max = max(precios_entrada)
            print(f"   - Encontradas {len(precios_entrada)} primas en rango")
            print(f"   - Prima más baja en rango: ${prima_min:.2f}")
            print(f"   - Prima más alta en rango: ${prima_max:.2f}")
            
            # Calcular ganancia con prima más baja
            max_high = df['high'].max()
            ganancia = ((max_high - prima_min) / prima_min * 100)
            print(f"\n   📊 CÁLCULO DE GANANCIA:")
            print(f"   - Prima entrada: ${prima_min:.2f}")
            print(f"   - Prima máxima D1: ${max_high:.2f}")
            print(f"   - Ganancia: {ganancia:.1f}%")
            
            if ganancia > 90:
                print(f"\n   ⚠️ GANANCIA SOSPECHOSA!")
                print(f"   Verificar si los datos son correctos")
        
        # Mostrar top 5 momentos con precio más alto
        print(f"\n   TOP 5 MOMENTOS CON PRECIO MÁS ALTO:")
        top_5 = df.nlargest(5, 'high')
        for _, row in top_5.iterrows():
            print(f"   - {row['time'].strftime('%H:%M')}: High=${row['high']:.2f}, O=${row['open']:.2f}, C=${row['close']:.2f}")
            
    else:
        print("   ❌ Sin datos por minuto")
        
except Exception as e:
    print(f"   Error: {e}")

# 4. Verificar día siguiente
fecha_siguiente = fecha_obj + timedelta(days=1)
fecha_siguiente_str = fecha_siguiente.strftime('%Y-%m-%d')

print(f"\n4️⃣ DÍA SIGUIENTE ({fecha_siguiente_str}):")
print("-"*50)
try:
    daily_d2 = client.get_aggs(
        ticker=option_ticker,
        multiplier=1,
        timespan='day',
        from_=fecha_siguiente_str,
        to=fecha_siguiente_str
    )
    if daily_d2:
        for d in daily_d2:
            print(f"   High día 2: ${d.high:.2f}")
    else:
        print("   ❌ Sin datos del día 2")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*80)
print("CONCLUSIÓN: Verificar si el HIGH mostrado arriba coincide con lo que reporta el sistema")