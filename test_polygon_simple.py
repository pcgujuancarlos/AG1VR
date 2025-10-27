#!/usr/bin/env python3
"""
Test simple para verificar datos de Polygon
"""

from app_v90b import HistorialManager
from datetime import datetime

# Crear instancia del manager
manager = HistorialManager()

# Caso de prueba específico
ticker = 'BAC'
fecha = datetime.strptime('2024-10-28', '%Y-%m-%d')
rsi = 50  # dummy
bb_position = 0.5  # dummy

print("="*60)
print("TEST: Verificando cálculo de ganancias para BAC")
print("="*60)

# Llamar directamente a la función que calcula ganancias
resultado = manager._calcular_ganancias_reales_intraday(ticker, fecha, rsi, bb_position)

print("\n" + "="*60)
print("RESULTADO FINAL:")
print("="*60)
print(f"Strike: ${resultado['strike']}")
print(f"Prima entrada: ${resultado['prima_entrada']}")
print(f"Prima máxima D1: ${resultado['prima_maxima']}")
print(f"Ganancia D1: {resultado['ganancia_pct']}%")
print(f"Mensaje: {resultado['mensaje']}")

if resultado['ganancia_pct'] > 40:
    print("\n⚠️ GANANCIA SOSPECHOSA DETECTADA")
    print("Posibles causas:")
    print("1. Prima de entrada muy baja")
    print("2. Spike anormal en los datos")
    print("3. Bajo volumen/liquidez")
    print("4. Error en datos de Polygon")