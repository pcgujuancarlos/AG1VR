#!/usr/bin/env python3
"""
Cálculo SIMPLE y DIRECTO de ganancias
"""

from polygon import RESTClient
import os
from datetime import datetime, timedelta

def calcular_ganancia_simple(ticker, fecha_str, strike):
    """Cálculo directo: prima inicial vs máxima del día"""
    
    API_KEY = os.environ.get('POLYGON_API_KEY')
    if not API_KEY:
        API_KEY = input("API Key: ")
    
    client = RESTClient(api_key=API_KEY)
    
    # Fecha de vencimiento
    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
    dias_hasta_viernes = (4 - fecha_obj.weekday()) % 7
    if dias_hasta_viernes == 0:
        dias_hasta_viernes = 7
    fecha_vencimiento = fecha_obj + timedelta(days=dias_hasta_viernes)
    
    # Construir ticker
    strike_mult = int(strike * 1000)
    option_ticker = f"O:{ticker}{fecha_vencimiento.strftime('%y%m%d')}P{strike_mult:08d}"
    
    print(f"\nContrato: {option_ticker}")
    
    try:
        # Obtener TODOS los datos del día
        aggs = client.get_aggs(
            ticker=option_ticker,
            multiplier=1,
            timespan='minute',
            from_=fecha_str,
            to=fecha_str,
            limit=50000
        )
        
        if aggs and len(aggs) > 0:
            # Prima inicial = primer precio del día (open del primer minuto)
            prima_inicial = aggs[0].open
            
            # Prima máxima = máximo high de todo el día
            prima_maxima = max([agg.high for agg in aggs])
            
            # Cálculo simple
            ganancia = ((prima_maxima - prima_inicial) / prima_inicial * 100) if prima_inicial > 0 else 0
            
            print(f"\n📊 RESULTADO SIMPLE:")
            print(f"Prima inicial (primer open): ${prima_inicial:.2f}")
            print(f"Prima máxima del día: ${prima_maxima:.2f}")
            print(f"GANANCIA: {ganancia:.1f}%")
            
            # Mostrar primeros y últimos datos para verificar
            print(f"\nPrimeros 3 minutos:")
            for i in range(min(3, len(aggs))):
                hora = datetime.fromtimestamp(aggs[i].timestamp/1000).strftime('%H:%M')
                print(f"  {hora}: O=${aggs[i].open:.2f} H=${aggs[i].high:.2f}")
            
            return prima_inicial, prima_maxima, ganancia
            
    except Exception as e:
        print(f"Error: {e}")
        return 0, 0, 0

# Probar con los casos problemáticos
casos = [
    ('CORZ', '2024-10-24', 14.0),
    ('MSFT', '2024-10-24', 410.0),
    ('BAC', '2024-10-24', 40.5)
]

print("CÁLCULO SIMPLE DE GANANCIAS")
print("="*60)

for ticker, fecha, strike in casos:
    print(f"\n{ticker} - Strike ${strike}")
    calcular_ganancia_simple(ticker, fecha, strike)
    print("-"*60)