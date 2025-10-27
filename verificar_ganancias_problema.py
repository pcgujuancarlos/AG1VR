#!/usr/bin/env python3
"""
Diagnóstico detallado de ganancias problemáticas
"""

import os
from app_v90b import HistorialManager
from datetime import datetime

# Configurar API
os.environ['POLYGON_API_KEY'] = input("Ingrese su POLYGON_API_KEY: ")

# Casos problemáticos de Alberto
casos = [
    {'ticker': 'CORZ', 'fecha': '2024-10-24', 'problema': 'ganancia incorrecta'},
    {'ticker': 'MSFT', 'fecha': '2024-10-24', 'problema': 'ganancia incorrecta'},
    {'ticker': 'BAC', 'fecha': '2024-10-24', 'problema': 'ganancia incorrecta'}
]

print("\n" + "="*80)
print("DIAGNÓSTICO DE GANANCIAS PROBLEMÁTICAS")
print("="*80)

# Crear instancia del manager
manager = HistorialManager()

for caso in casos:
    ticker = caso['ticker']
    fecha_str = caso['fecha']
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
    
    print(f"\n{'='*60}")
    print(f"ANALIZANDO: {ticker} - {fecha_str}")
    print(f"Problema reportado: {caso['problema']}")
    print('='*60)
    
    # Obtener RSI y BB del día (valores dummy para prueba)
    rsi = 50  # Valor dummy
    bb_position = 0.5  # Valor dummy
    
    print(f"\nCalculando ganancias reales para {ticker}...")
    print("-"*50)
    
    # Llamar a la función de cálculo
    resultado = manager._calcular_ganancias_reales_intraday(
        ticker, 
        fecha,
        rsi,
        bb_position
    )
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   Strike: ${resultado['strike']:.2f}")
    print(f"   Prima entrada: ${resultado['prima_entrada']:.2f}")
    print(f"   Prima máxima D1: ${resultado['prima_maxima']:.2f}")
    print(f"   Prima máxima D2: ${resultado['prima_maxima_dia2']:.2f}")
    print(f"   Ganancia D1: {resultado['ganancia_pct']:.1f}%")
    print(f"   Ganancia D2: {resultado['ganancia_dia_siguiente']:.1f}%")
    print(f"   Mensaje: {resultado['mensaje']}")

print("\n" + "="*80)
print("ANÁLISIS COMPLETADO")
print("="*80)