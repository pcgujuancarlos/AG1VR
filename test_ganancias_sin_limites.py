#!/usr/bin/env python3
"""
Test para verificar que las ganancias se calculan sin límites artificiales
"""

from polygon import RESTClient
import os
from datetime import datetime

API_KEY = input("Ingrese su POLYGON_API_KEY: ")
client = RESTClient(api_key=API_KEY)

# Casos problemáticos reportados por Alberto
casos = [
    ('CORZ', '2024-10-25'),
    ('MSFT', '2024-10-25'), 
    ('BAC', '2024-10-28')
]

for ticker, fecha_str in casos:
    print(f"\n{'='*60}")
    print(f"VERIFICANDO {ticker} - {fecha_str}")
    print('='*60)
    
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
    
    # Obtener precio del stock
    try:
        stock_data = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan='day',
            from_=fecha_str,
            to=fecha_str
        )
        if stock_data:
            precio_stock = stock_data[0].close
            print(f"Precio stock: ${precio_stock:.2f}")
    except Exception as e:
        print(f"Error obteniendo precio: {e}")
        continue
    
    # Buscar opciones PUT cercanas al dinero
    strikes = [
        round(precio_stock - 1.5, 1),
        round(precio_stock - 1.0, 1),
        round(precio_stock - 0.5, 1),
        round(precio_stock, 1),
        round(precio_stock + 0.5, 1)
    ]
    
    print(f"\nBuscando opciones PUT con strikes: {strikes}")
    
    # Fecha de vencimiento (siguiente viernes)
    dias_hasta_viernes = (4 - fecha.weekday()) % 7
    if dias_hasta_viernes == 0:
        dias_hasta_viernes = 7
    from datetime import timedelta
    fecha_venc = fecha + timedelta(days=dias_hasta_viernes)
    
    for strike in strikes:
        # Formato del ticker de opción
        strike_mult = int(strike * 1000)
        option_ticker = f"O:{ticker}{fecha_venc.strftime('%y%m%d')}P{strike_mult:08d}"
        
        print(f"\n  Strike ${strike} ({option_ticker}):")
        
        try:
            # Obtener datos del día
            option_data = client.get_aggs(
                ticker=option_ticker,
                multiplier=1,
                timespan='minute',
                from_=fecha_str,
                to=fecha_str,
                limit=50000
            )
            
            if option_data:
                # Prima inicial (primeros 30 min)
                primeros_30 = option_data[:30]
                opens = [agg.open for agg in primeros_30 if agg.open > 0]
                prima_inicial = opens[0] if opens else 0
                
                # Prima máxima del día (sin percentiles)
                highs = [agg.high for agg in option_data if agg.high > 0]
                prima_maxima = max(highs) if highs else 0
                
                if prima_inicial > 0:
                    ganancia = ((prima_maxima - prima_inicial) / prima_inicial * 100)
                    print(f"    Prima inicial: ${prima_inicial:.2f}")
                    print(f"    Prima máxima: ${prima_maxima:.2f}")
                    print(f"    GANANCIA REAL: {ganancia:.1f}%")
                    
                    if ganancia > 100:
                        print(f"    ⚠️ Ganancia alta - DATOS REALES sin filtros")
                else:
                    print(f"    Sin datos de prima inicial")
                    
        except Exception as e:
            print(f"    Error: {e}")

print("\n" + "="*60)
print("NOTA: Todas las ganancias mostradas son REALES")
print("basadas en datos de Polygon sin ningún filtro artificial")