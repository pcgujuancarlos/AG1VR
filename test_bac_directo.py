#!/usr/bin/env python3
"""
Test directo de BAC con la función real
"""

from polygon import RESTClient
import os
from app_v90b import calcular_ganancia_real_opcion
from datetime import datetime

# Configurar API
print("Ingrese su POLYGON_API_KEY:")
API_KEY = input().strip()
os.environ['POLYGON_API_KEY'] = API_KEY

client = RESTClient(api_key=API_KEY)

# Datos de prueba
ticker = 'BAC'
fecha = datetime.strptime('2024-10-28', '%Y-%m-%d')

# Obtener precio actual de BAC
try:
    stock_data = client.get_aggs(
        ticker=ticker,
        multiplier=1,
        timespan='day',
        from_='2024-10-25',
        to='2024-10-28',
        limit=5
    )
    if stock_data:
        precio_stock = stock_data[-1].close
        print(f"\nPrecio de BAC: ${precio_stock:.2f}")
    else:
        precio_stock = 41.0
        print(f"\nUsando precio estimado: ${precio_stock:.2f}")
except:
    precio_stock = 41.0
    print(f"\nUsando precio por defecto: ${precio_stock:.2f}")

print("\n" + "="*60)
print("CALCULANDO GANANCIA PARA BAC")
print("="*60)

# Llamar a la función
resultado = calcular_ganancia_real_opcion(client, ticker, fecha, precio_stock)

print("\n" + "="*60)
print("RESULTADO:")
print("="*60)
print(f"Strike: ${resultado['strike']}")
print(f"Prima entrada: ${resultado['prima_entrada']}")
print(f"Prima máxima D1: ${resultado['prima_maxima']}")
print(f"Ganancia D1: {resultado['ganancia_pct']}%")
print(f"Éxito: {resultado['exito']}")
print(f"Mensaje: {resultado['mensaje']}")

if resultado['ganancia_pct'] > 40:
    print("\n⚠️ ALERTA: Ganancia sospechosamente alta")
    print("Esto indica que:")
    print("1. La prima de entrada es muy baja")
    print("2. Hay un spike en los datos") 
    print("3. Posible error en los datos de Polygon")