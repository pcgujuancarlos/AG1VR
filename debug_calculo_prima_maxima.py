#!/usr/bin/env python3
"""
Debug: Entender cómo se calcula la prima máxima día 1
"""

from polygon import RESTClient
import os
from datetime import datetime, timedelta
import pandas as pd

API_KEY = input("Ingrese su POLYGON_API_KEY: ")
client = RESTClient(api_key=API_KEY)

# Caso de prueba
ticker = input("Ticker (ej: MSFT): ")
fecha_str = input("Fecha (YYYY-MM-DD): ")
strike_input = input("Strike (ej: 410): ")
strike = float(strike_input)

print("\n" + "="*80)
print("ANÁLISIS DEL CÁLCULO DE PRIMA MÁXIMA DÍA 1")
print("="*80)

# Calcular fecha de vencimiento
fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
dias_hasta_viernes = (4 - fecha_obj.weekday()) % 7
if dias_hasta_viernes == 0:
    dias_hasta_viernes = 7
fecha_vencimiento = fecha_obj + timedelta(days=dias_hasta_viernes)

# Construir ticker
strike_mult = int(strike * 1000)
option_ticker = f"O:{ticker}{fecha_vencimiento.strftime('%y%m%d')}P{strike_mult:08d}"

print(f"\n📋 INFORMACIÓN:")
print(f"   Contrato: {option_ticker}")
print(f"   Vencimiento: {fecha_vencimiento.strftime('%Y-%m-%d')}")

# Paso 1: Obtener TODOS los datos del día
print(f"\n1️⃣ OBTENIENDO DATOS DEL DÍA 1...")
try:
    option_aggs_dia1 = client.get_aggs(
        ticker=option_ticker,
        multiplier=1,
        timespan="minute",
        from_=fecha_str,
        to=fecha_str,
        limit=50000
    )
    
    if option_aggs_dia1 and len(option_aggs_dia1) > 0:
        print(f"✅ Obtenidos {len(option_aggs_dia1)} agregados de 1 minuto")
        
        # Paso 2: Recopilar todos los highs
        todos_high_dia1 = []
        data_for_df = []
        
        for agg in option_aggs_dia1:
            todos_high_dia1.append(agg.high)
            data_for_df.append({
                'time': datetime.fromtimestamp(agg.timestamp/1000),
                'open': agg.open,
                'high': agg.high,
                'low': agg.low,
                'close': agg.close
            })
        
        df = pd.DataFrame(data_for_df)
        
        # Paso 3: Calcular máximo
        prima_maxima_dia1 = max(todos_high_dia1)
        
        print(f"\n2️⃣ ANÁLISIS DE HIGHS:")
        print(f"   Total de highs recopilados: {len(todos_high_dia1)}")
        print(f"   HIGH MÍNIMO del día: ${min(todos_high_dia1):.2f}")
        print(f"   HIGH MÁXIMO del día: ${prima_maxima_dia1:.2f} ⬅️ ESTE ES EL QUE USA EL SISTEMA")
        
        # Análisis estadístico
        print(f"\n3️⃣ ESTADÍSTICAS DE HIGHS:")
        print(f"   Promedio: ${df['high'].mean():.2f}")
        print(f"   Mediana: ${df['high'].median():.2f}")
        print(f"   Desviación estándar: ${df['high'].std():.2f}")
        
        # Detectar outliers
        q1 = df['high'].quantile(0.25)
        q3 = df['high'].quantile(0.75)
        iqr = q3 - q1
        outlier_min = q1 - 1.5 * iqr
        outlier_max = q3 + 1.5 * iqr
        
        outliers = df[df['high'] > outlier_max]
        if len(outliers) > 0:
            print(f"\n⚠️ POSIBLES OUTLIERS DETECTADOS (highs anormalmente altos):")
            for _, row in outliers.iterrows():
                print(f"   {row['time'].strftime('%H:%M:%S')}: High=${row['high']:.2f} (O=${row['open']:.2f}, C=${row['close']:.2f})")
        
        # Top 10 highs
        print(f"\n4️⃣ TOP 10 HIGHS DEL DÍA:")
        top_10 = df.nlargest(10, 'high')
        for i, (_, row) in enumerate(top_10.iterrows(), 1):
            print(f"   {i}. {row['time'].strftime('%H:%M')}: High=${row['high']:.2f} (O=${row['open']:.2f}, L=${row['low']:.2f}, C=${row['close']:.2f})")
        
        # Verificar si hay saltos bruscos
        print(f"\n5️⃣ ANÁLISIS DE SALTOS BRUSCOS:")
        df_sorted = df.sort_values('time')
        df_sorted['high_diff'] = df_sorted['high'].diff()
        
        saltos_grandes = df_sorted[df_sorted['high_diff'].abs() > df['high'].mean() * 0.5]
        if len(saltos_grandes) > 0:
            print(f"   ⚠️ Encontrados {len(saltos_grandes)} saltos bruscos:")
            for _, row in saltos_grandes.head(5).iterrows():
                print(f"   {row['time'].strftime('%H:%M')}: Salto de ${row['high_diff']:.2f}")
        
        # Comparar con datos diarios
        print(f"\n6️⃣ COMPARACIÓN CON DATOS DIARIOS:")
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
                    print(f"   Datos diarios - High: ${d.high:.2f}")
                    if abs(d.high - prima_maxima_dia1) > 0.01:
                        print(f"   ⚠️ DISCREPANCIA: Diario=${d.high:.2f} vs Minutos=${prima_maxima_dia1:.2f}")
        except:
            print("   ❌ No se pudo obtener datos diarios")
        
    else:
        print("❌ No se obtuvieron datos")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80)
print("CONCLUSIÓN:")
print("- Verificar si hay outliers o datos anormales")
print("- Comparar con datos diarios para validar")
print("- Revisar los momentos específicos con highs muy altos")