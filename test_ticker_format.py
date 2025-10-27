#!/usr/bin/env python3
"""
Test: Verificar formato correcto del ticker de opciones
"""

# Casos problemáticos
casos = [
    {'ticker': 'CORZ', 'strike': 14.0},
    {'ticker': 'MSFT', 'strike': 410.0},
    {'ticker': 'BAC', 'strike': 40.5}
]

from datetime import datetime, timedelta

fecha = datetime.strptime('2024-10-24', '%Y-%m-%d')
dias_hasta_viernes = (4 - fecha.weekday()) % 7
if dias_hasta_viernes == 0:
    dias_hasta_viernes = 7
fecha_vencimiento = fecha + timedelta(days=dias_hasta_viernes)

print("FORMATO DE TICKERS DE OPCIONES")
print("="*60)
print(f"Fecha señal: {fecha.strftime('%Y-%m-%d')}")
print(f"Fecha vencimiento: {fecha_vencimiento.strftime('%Y-%m-%d')}")
print()

for caso in casos:
    ticker = caso['ticker']
    strike = caso['strike']
    
    # Formato actual (multiplicando por 1000)
    strike_mult = int(strike * 1000)
    option_ticker = f"O:{ticker}{fecha_vencimiento.strftime('%y%m%d')}P{strike_mult:08d}"
    
    print(f"\n{ticker} Strike ${strike}:")
    print(f"  Formato actual: {option_ticker}")
    print(f"  Strike * 1000 = {strike_mult}")
    
    # Verificar si el strike tiene decimales
    if strike != int(strike):
        print(f"  ⚠️ AVISO: Strike tiene decimales (${strike})")
        
        # Alternativas
        strike_int = int(strike)
        strike_int_mult = strike_int * 1000
        option_ticker_int = f"O:{ticker}{fecha_vencimiento.strftime('%y%m%d')}P{strike_int_mult:08d}"
        print(f"  Alternativa entero: {option_ticker_int} (strike ${strike_int})")

print("\n\n📊 OBSERVACIONES:")
print("1. BAC tiene strike 40.5 que se convierte a 40500")
print("2. Verificar si Polygon espera el formato con o sin decimales")
print("3. El problema puede estar en la generación de contratos que usa solo enteros")