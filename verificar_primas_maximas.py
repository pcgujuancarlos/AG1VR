#!/usr/bin/env python3
"""
Diagnóstico: Verificar cómo se obtienen las primas máximas del día 1 y día 2
"""

from polygon import RESTClient
import os
from datetime import datetime, timedelta

# Configuración
API_KEY = os.environ.get('POLYGON_API_KEY')
client = RESTClient(api_key=API_KEY)

# Casos problemáticos mencionados por Alberto
casos = [
    {'ticker': 'CORZ', 'strike': 14, 'fecha': '2024-10-24'},
    {'ticker': 'MSFT', 'strike': 410, 'fecha': '2024-10-24'},
    {'ticker': 'BAC', 'strike': 40.5, 'fecha': '2024-10-24'}
]

def verificar_primas(ticker, strike, fecha_str):
    """Verificar las primas máximas para un caso específico"""
    print(f"\n{'='*60}")
    print(f"Verificando {ticker} Strike ${strike} - Fecha: {fecha_str}")
    print('='*60)
    
    # Fecha de señal
    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
    fecha_siguiente = fecha_obj + timedelta(days=1)
    fecha_siguiente_str = fecha_siguiente.strftime('%Y-%m-%d')
    
    # Encontrar fecha de vencimiento (siguiente viernes)
    dias_hasta_viernes = (4 - fecha_obj.weekday()) % 7
    if dias_hasta_viernes == 0:
        dias_hasta_viernes = 7
    fecha_vencimiento = fecha_obj + timedelta(days=dias_hasta_viernes)
    
    # Formato del contrato
    strike_mult = int(strike * 1000)
    option_ticker = f"O:{ticker}{fecha_vencimiento.strftime('%y%m%d')}P{strike_mult:08d}"
    print(f"Contrato: {option_ticker}")
    
    # Verificar datos con diferentes configuraciones
    configuraciones = [
        {'timespan': '30minute', 'multiplier': 1, 'desc': 'Agregados de 30 minutos'},
        {'timespan': 'minute', 'multiplier': 1, 'desc': 'Datos minuto a minuto'},
        {'timespan': 'minute', 'multiplier': 30, 'desc': 'Agregados de 30min (1min x 30)'}
    ]
    
    for config in configuraciones:
        print(f"\n\n📊 {config['desc']}:")
        print("-"*50)
        
        try:
            # Día 1
            print(f"\nDÍA 1 ({fecha_str}):")
            aggs_dia1 = client.get_aggs(
                ticker=option_ticker,
                multiplier=config['multiplier'],
                timespan=config['timespan'],
                from_=fecha_str,
                to=fecha_str,
                limit=50000
            )
            
            if aggs_dia1:
                precios = []
                print(f"Total agregados: {len(aggs_dia1)}")
                
                # Primeros 5 agregados
                print("\nPrimeros 5 agregados:")
                for i, agg in enumerate(aggs_dia1[:5]):
                    hora = datetime.fromtimestamp(agg.timestamp/1000).strftime('%H:%M:%S')
                    print(f"  {hora}: Open=${agg.open:.2f}, High=${agg.high:.2f}, Low=${agg.low:.2f}, Close=${agg.close:.2f}")
                    precios.extend([agg.open, agg.high, agg.low, agg.close])
                
                # Estadísticas
                todos_high = [agg.high for agg in aggs_dia1]
                todos_low = [agg.low for agg in aggs_dia1]
                max_high = max(todos_high)
                min_low = min(todos_low)
                
                print(f"\nEstadísticas Día 1:")
                print(f"  Prima máxima (high): ${max_high:.2f}")
                print(f"  Prima mínima (low): ${min_low:.2f}")
                print(f"  Rango: ${min_low:.2f} - ${max_high:.2f}")
                
            else:
                print("  ❌ Sin datos")
            
            # Día 2
            print(f"\n\nDÍA 2 ({fecha_siguiente_str}):")
            aggs_dia2 = client.get_aggs(
                ticker=option_ticker,
                multiplier=config['multiplier'],
                timespan=config['timespan'],
                from_=fecha_siguiente_str,
                to=fecha_siguiente_str,
                limit=50000
            )
            
            if aggs_dia2:
                print(f"Total agregados: {len(aggs_dia2)}")
                
                # Primeros 5 agregados
                print("\nPrimeros 5 agregados:")
                for i, agg in enumerate(aggs_dia2[:5]):
                    hora = datetime.fromtimestamp(agg.timestamp/1000).strftime('%H:%M:%S')
                    print(f"  {hora}: Open=${agg.open:.2f}, High=${agg.high:.2f}, Low=${agg.low:.2f}, Close=${agg.close:.2f}")
                
                # Estadísticas
                todos_high = [agg.high for agg in aggs_dia2]
                todos_low = [agg.low for agg in aggs_dia2]
                max_high = max(todos_high)
                min_low = min(todos_low)
                
                print(f"\nEstadísticas Día 2:")
                print(f"  Prima máxima (high): ${max_high:.2f}")
                print(f"  Prima mínima (low): ${min_low:.2f}")
                print(f"  Rango: ${min_low:.2f} - ${max_high:.2f}")
                
            else:
                print("  ❌ Sin datos")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Comparar con datos diarios
    print(f"\n\n📊 COMPARACIÓN CON DATOS DIARIOS:")
    print("-"*50)
    try:
        daily_aggs = client.get_aggs(
            ticker=option_ticker,
            multiplier=1,
            timespan='day',
            from_=fecha_str,
            to=fecha_siguiente_str,
            limit=50
        )
        
        if daily_aggs:
            for agg in daily_aggs:
                fecha_daily = datetime.fromtimestamp(agg.timestamp/1000).strftime('%Y-%m-%d')
                print(f"{fecha_daily}: Open=${agg.open:.2f}, High=${agg.high:.2f}, Low=${agg.low:.2f}, Close=${agg.close:.2f}")
    except Exception as e:
        print(f"Error obteniendo datos diarios: {e}")

# Ejecutar verificación
print("VERIFICACIÓN DE CÁLCULO DE PRIMAS MÁXIMAS")
print("==========================================")

for caso in casos:
    verificar_primas(caso['ticker'], caso['strike'], caso['fecha'])

print("\n\n🔍 ANÁLISIS:")
print("1. Verificar si el problema es el timespan (30minute vs minute)")
print("2. Verificar si el multiplier está funcionando correctamente")
print("3. Comparar con datos diarios para validar")