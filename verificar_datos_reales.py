#!/usr/bin/env python3
"""
Verificar datos REALES de Polygon para casos problemáticos
"""

from polygon import RESTClient
import os
from datetime import datetime, timedelta
import pandas as pd

# API Key
API_KEY = input("Ingrese su POLYGON_API_KEY: ")
client = RESTClient(api_key=API_KEY)

# Casos específicos de Alberto
casos = [
    {'ticker': 'CORZ', 'fecha': '2024-10-24', 'strike': 14},
    {'ticker': 'MSFT', 'fecha': '2024-10-24', 'strike': 410}, 
    {'ticker': 'BAC', 'fecha': '2024-10-24', 'strike': 40.5}
]

def verificar_opcion_real(ticker, fecha_str, strike):
    """Verificar datos reales de una opción en Polygon"""
    print(f"\n{'='*80}")
    print(f"VERIFICANDO: {ticker} Strike ${strike} - Fecha: {fecha_str}")
    print('='*80)
    
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
    print(f"Fecha vencimiento: {fecha_vencimiento.strftime('%Y-%m-%d')}")
    
    # Intentar diferentes formas de obtener datos
    print("\n1️⃣ DATOS DIARIOS (1 día):")
    print("-"*40)
    try:
        daily = client.get_aggs(
            ticker=option_ticker,
            multiplier=1,
            timespan='day',
            from_=fecha_str,
            to=fecha_str
        )
        if daily:
            for d in daily:
                print(f"   Open: ${d.open:.2f}")
                print(f"   High: ${d.high:.2f} ⬅️ MÁXIMO DEL DÍA")
                print(f"   Low:  ${d.low:.2f}")
                print(f"   Close: ${d.close:.2f}")
                print(f"   Volume: {d.volume}")
        else:
            print("   ❌ Sin datos diarios")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2️⃣ DATOS POR MINUTO:")
    print("-"*40)
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
            df = pd.DataFrame([{
                'time': datetime.fromtimestamp(agg.timestamp/1000),
                'open': agg.open,
                'high': agg.high,
                'low': agg.low,
                'close': agg.close
            } for agg in minute_data])
            
            print(f"   Total minutos: {len(minute_data)}")
            print(f"   Hora inicio: {df['time'].min()}")
            print(f"   Hora fin: {df['time'].max()}")
            print(f"   MÁXIMO del día (high): ${df['high'].max():.2f} ⬅️")
            print(f"   MÍNIMO del día (low): ${df['low'].min():.2f}")
            
            # Mostrar los 5 momentos con precio más alto
            top_5 = df.nlargest(5, 'high')[['time', 'high', 'low', 'open', 'close']]
            print("\n   Top 5 momentos con precio más alto:")
            for idx, row in top_5.iterrows():
                print(f"     {row['time'].strftime('%H:%M')} - High: ${row['high']:.2f}, Open: ${row['open']:.2f}, Close: ${row['close']:.2f}")
        else:
            print("   ❌ Sin datos por minuto")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3️⃣ DATOS DE 30 MINUTOS:")
    print("-"*40)
    try:
        thirty_min = client.get_aggs(
            ticker=option_ticker,
            multiplier=30,
            timespan='minute',
            from_=fecha_str,
            to=fecha_str
        )
        
        if thirty_min:
            print(f"   Total agregados 30min: {len(thirty_min)}")
            max_high = max([agg.high for agg in thirty_min])
            print(f"   MÁXIMO (high): ${max_high:.2f}")
        else:
            print("   ❌ Sin datos de 30 minutos")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Verificar día siguiente
    fecha_siguiente = fecha_obj + timedelta(days=1)
    fecha_siguiente_str = fecha_siguiente.strftime('%Y-%m-%d')
    
    print(f"\n4️⃣ DÍA SIGUIENTE ({fecha_siguiente_str}):")
    print("-"*40)
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
                print(f"   High D2: ${d.high:.2f} ⬅️ MÁXIMO DÍA 2")
        else:
            print("   ❌ Sin datos del día 2")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Ejecutar verificación
print("VERIFICACIÓN DE DATOS REALES EN POLYGON")
print("="*80)
print("Comparando diferentes métodos de obtención de datos")

for caso in casos:
    verificar_opcion_real(caso['ticker'], caso['fecha'], caso['strike'])

print("\n\n📊 CONCLUSIÓN:")
print("Los datos diarios deberían mostrar el HIGH real del día")
print("Verificar si hay discrepancia entre datos diarios y por minuto")