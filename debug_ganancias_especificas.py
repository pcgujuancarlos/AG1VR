#!/usr/bin/env python3
"""
Debug específico para CORZ, MSFT y BAC del 24 de octubre
"""

from polygon import RESTClient
import os
from datetime import datetime, timedelta

# Obtener API key
API_KEY = input("Ingrese su POLYGON_API_KEY: ")
client = RESTClient(api_key=API_KEY)

# Casos problemáticos
casos = [
    {'ticker': 'CORZ', 'fecha': '2024-10-24', 'rango_prima': {'min': 0.10, 'max': 0.70}},
    {'ticker': 'MSFT', 'fecha': '2024-10-24', 'rango_prima': {'min': 0.50, 'max': 3.00}},
    {'ticker': 'BAC', 'fecha': '2024-10-24', 'rango_prima': {'min': 0.10, 'max': 0.50}}
]

def analizar_opciones(ticker, fecha_str, rango_prima):
    """Analizar opciones PUT para un ticker en una fecha"""
    print(f"\n{'='*80}")
    print(f"ANALIZANDO {ticker} - {fecha_str}")
    print('='*80)
    
    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
    fecha_siguiente = fecha_obj + timedelta(days=1)
    
    # Calcular fecha de vencimiento (siguiente viernes)
    dias_hasta_viernes = (4 - fecha_obj.weekday()) % 7
    if dias_hasta_viernes == 0:
        dias_hasta_viernes = 7
    fecha_vencimiento = fecha_obj + timedelta(days=dias_hasta_viernes)
    
    # Obtener precio del subyacente
    try:
        daily_data = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan='day',
            from_=fecha_str,
            to=fecha_str,
            limit=1
        )
        if daily_data:
            precio_actual = daily_data[0].close
            print(f"Precio de cierre {ticker}: ${precio_actual:.2f}")
        else:
            print(f"⚠️ No se pudo obtener precio de {ticker}")
            return
    except Exception as e:
        print(f"❌ Error obteniendo precio: {e}")
        return
    
    # Buscar contratos de opciones PUT
    strikes_cercanos = []
    for i in range(-10, 5):  # Strikes desde -10% hasta +5% del precio actual
        strike = round(precio_actual * (1 + i/100), 1)
        strikes_cercanos.append(strike)
    
    print(f"\nBuscando opciones PUT con vencimiento: {fecha_vencimiento.strftime('%Y-%m-%d')}")
    print(f"Rango de prima objetivo: ${rango_prima['min']:.2f} - ${rango_prima['max']:.2f}")
    print(f"Strikes a evaluar: {strikes_cercanos[:5]}... hasta {strikes_cercanos[-5:]}")
    
    mejores_opciones = []
    
    for strike in strikes_cercanos:
        strike_mult = int(strike * 1000)
        option_ticker = f"O:{ticker}{fecha_vencimiento.strftime('%y%m%d')}P{strike_mult:08d}"
        
        try:
            # Obtener datos del día de la señal
            option_aggs_dia1 = client.get_aggs(
                ticker=option_ticker,
                multiplier=1,
                timespan="minute",
                from_=fecha_str,
                to=fecha_str,
                limit=50000
            )
            
            if not option_aggs_dia1:
                continue
            
            # Analizar precios
            todos_precios = []
            todos_high = []
            for agg in option_aggs_dia1:
                todos_precios.extend([agg.open, agg.high, agg.low, agg.close])
                todos_high.append(agg.high)
            
            # Buscar primas en rango
            primas_en_rango = [p for p in todos_precios if rango_prima['min'] <= p <= rango_prima['max']]
            
            if primas_en_rango:
                prima_entrada = min(primas_en_rango)  # Tomar la más baja en rango
                prima_maxima_dia1 = max(todos_high)
                
                # Obtener datos del día siguiente
                fecha_sig_str = fecha_siguiente.strftime('%Y-%m-%d')
                option_aggs_dia2 = client.get_aggs(
                    ticker=option_ticker,
                    multiplier=1,
                    timespan="minute",
                    from_=fecha_sig_str,
                    to=fecha_sig_str,
                    limit=50000
                )
                
                prima_maxima_dia2 = 0
                if option_aggs_dia2:
                    prima_maxima_dia2 = max([agg.high for agg in option_aggs_dia2])
                
                ganancia_dia1 = ((prima_maxima_dia1 - prima_entrada) / prima_entrada * 100) if prima_entrada > 0 else 0
                ganancia_dia2 = ((prima_maxima_dia2 - prima_entrada) / prima_entrada * 100) if prima_entrada > 0 else 0
                
                mejores_opciones.append({
                    'strike': strike,
                    'prima_entrada': prima_entrada,
                    'prima_max_d1': prima_maxima_dia1,
                    'prima_max_d2': prima_maxima_dia2,
                    'ganancia_d1': ganancia_dia1,
                    'ganancia_d2': ganancia_dia2,
                    'num_primas_rango': len(primas_en_rango),
                    'contrato': option_ticker
                })
                
        except Exception as e:
            continue
    
    # Mostrar resultados
    if mejores_opciones:
        print(f"\n📊 OPCIONES ENCONTRADAS ({len(mejores_opciones)}):")
        mejores_opciones.sort(key=lambda x: x['ganancia_d1'], reverse=True)
        
        for i, opt in enumerate(mejores_opciones[:5]):
            print(f"\n{i+1}. Strike ${opt['strike']:.2f}")
            print(f"   Contrato: {opt['contrato']}")
            print(f"   Prima entrada: ${opt['prima_entrada']:.2f} (de {opt['num_primas_rango']} en rango)")
            print(f"   Prima máx D1: ${opt['prima_max_d1']:.2f}")
            print(f"   Prima máx D2: ${opt['prima_max_d2']:.2f}")
            print(f"   Ganancia D1: {opt['ganancia_d1']:.1f}%")
            print(f"   Ganancia D2: {opt['ganancia_d2']:.1f}%")
    else:
        print("\n❌ No se encontraron opciones con primas en el rango especificado")

# Ejecutar análisis
print("ANÁLISIS DETALLADO DE GANANCIAS")
print("================================")

for caso in casos:
    analizar_opciones(caso['ticker'], caso['fecha'], caso['rango_prima'])