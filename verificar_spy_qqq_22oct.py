#!/usr/bin/env python3
"""
Verificar específicamente SPY y QQQ del 22 de octubre
"""

from polygon import RESTClient
import os
from datetime import datetime, timedelta
import pytz

API_KEY = input("Ingrese su POLYGON_API_KEY: ")
client = RESTClient(api_key=API_KEY)

fecha_str = '2024-10-22'
fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
et_tz = pytz.timezone('America/New_York')

for ticker in ['SPY', 'QQQ']:
    print(f"\n{'='*60}")
    print(f"VERIFICANDO {ticker} - {fecha_str}")
    print('='*60)
    
    # 1. Datos diarios
    print(f"\n1️⃣ DATOS DIARIOS:")
    try:
        daily = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan='day',
            from_=fecha_str,
            to=fecha_str
        )
        if daily:
            d = daily[0]
            es_vela_roja_diaria = d.close < d.open
            print(f"   Open: ${d.open:.2f}")
            print(f"   Close: ${d.close:.2f}")
            print(f"   Vela roja diaria: {'SÍ' if es_vela_roja_diaria else 'NO'} ({'↓' if es_vela_roja_diaria else '↑'})")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Datos de minutos 9:30-10:00
    print(f"\n2️⃣ DATOS 9:30-10:00 AM ET:")
    try:
        # Obtener todos los datos del día
        minute_data = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan='minute',
            from_=fecha_str,
            to=fecha_str,
            limit=1000
        )
        
        if minute_data:
            # Timestamps para 9:30 y 10:00 AM ET
            fecha_et = et_tz.localize(datetime.combine(fecha, datetime.strptime('09:30', '%H:%M').time()))
            inicio_930 = int(fecha_et.timestamp() * 1000)
            fin_1000 = int((fecha_et + timedelta(minutes=30)).timestamp() * 1000)
            
            # Filtrar datos 9:30-10:00
            datos_930_1000 = [agg for agg in minute_data if inicio_930 <= agg.timestamp < fin_1000]
            
            if datos_930_1000:
                datos_ordenados = sorted(datos_930_1000, key=lambda x: x.timestamp)
                precio_apertura = datos_ordenados[0].open
                precio_cierre = datos_ordenados[-1].close
                
                es_primera_vela_roja = precio_cierre < precio_apertura
                
                print(f"   Total minutos 9:30-10:00: {len(datos_ordenados)}")
                print(f"   Precio 9:30 AM: ${precio_apertura:.2f}")
                print(f"   Precio 10:00 AM: ${precio_cierre:.2f}")
                print(f"   Primera vela roja (9:30-10:00): {'SÍ ✅' if es_primera_vela_roja else 'NO ❌'}")
                print(f"   Cambio: ${precio_cierre - precio_apertura:.2f} ({((precio_cierre/precio_apertura - 1) * 100):.2f}%)")
                
                # Mostrar algunos puntos clave
                print("\n   Detalle por minutos:")
                for i in [0, 10, 20, -1]:  # Primero, minuto 10, 20 y último
                    if 0 <= i < len(datos_ordenados):
                        agg = datos_ordenados[i]
                        hora = datetime.fromtimestamp(agg.timestamp/1000).strftime('%H:%M')
                        print(f"     {hora}: O=${agg.open:.2f} C=${agg.close:.2f}")
            else:
                print("   ❌ No hay datos entre 9:30-10:00 AM")
                
                # Buscar primeros 30 minutos disponibles
                if minute_data:
                    primeros_30 = minute_data[:30]
                    precio_apertura = primeros_30[0].open
                    precio_cierre = primeros_30[-1].close
                    es_vela_roja = precio_cierre < precio_apertura
                    
                    hora_inicio = datetime.fromtimestamp(primeros_30[0].timestamp/1000).strftime('%H:%M')
                    hora_fin = datetime.fromtimestamp(primeros_30[-1].timestamp/1000).strftime('%H:%M')
                    
                    print(f"\n   Primeros 30 minutos disponibles ({hora_inicio}-{hora_fin}):")
                    print(f"   Primera vela roja: {'SÍ ✅' if es_vela_roja else 'NO ❌'}")
                    
    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "="*60)
print("CONCLUSIÓN:")
print("Si Alberto dice que son velas rojas y el sistema no las detecta, verificar:")
print("1. Si hay datos entre 9:30-10:00 AM")
print("2. Si el precio realmente bajó en ese período")
print("3. Si los datos de Polygon son correctos")