"""
Cálculo de P&L (Ganancias y Pérdidas) - MÓDULO INDEPENDIENTE
"""
from typing import Tuple, Optional, List, Dict
from datetime import datetime, timedelta
from polygon import RESTClient
from .types import OptionResult
from .filters import validar_prima_en_rango, validar_ganancia_realista

def calcular_ganancia_opcion(
    prima_entrada: float,
    prima_salida: float
) -> float:
    """
    Calcula el porcentaje de ganancia de una opción
    
    Args:
        prima_entrada: Prima de entrada
        prima_salida: Prima de salida
        
    Returns:
        Porcentaje de ganancia
    """
    if prima_entrada <= 0:
        return 0.0
    
    ganancia = ((prima_salida - prima_entrada) / prima_entrada) * 100
    
    # Limitar a valores realistas
    if ganancia > 400:
        print(f"⚠️ Ganancia limitada de {ganancia:.1f}% a 400%")
        return 400.0
    
    return ganancia

def obtener_precios_opcion_dia(
    client: RESTClient,
    option_ticker: str,
    fecha: str,
    multiplier: int = 1
) -> Dict[str, float]:
    """
    Obtiene todos los precios de una opción para un día
    
    Args:
        client: Cliente de Polygon
        option_ticker: Ticker de la opción
        fecha: Fecha en formato YYYY-MM-DD
        multiplier: Multiplicador de tiempo
        
    Returns:
        Dict con min, max, open, close del día
    """
    try:
        aggs = client.get_aggs(
            ticker=option_ticker,
            multiplier=multiplier,
            timespan="minute",
            from_=fecha,
            to=fecha,
            limit=5000
        )
        
        if not aggs:
            return {'min': 0, 'max': 0, 'open': 0, 'close': 0}
        
        todos_precios = []
        for agg in aggs:
            todos_precios.extend([agg.open, agg.high, agg.low, agg.close])
        
        if not todos_precios:
            return {'min': 0, 'max': 0, 'open': 0, 'close': 0}
        
        return {
            'min': min(todos_precios),
            'max': max(todos_precios),
            'open': aggs[0].open if aggs else 0,
            'close': aggs[-1].close if aggs else 0
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo precios: {e}")
        return {'min': 0, 'max': 0, 'open': 0, 'close': 0}

def buscar_prima_en_rango(
    precios_dia: Dict[str, float],
    prima_min: float,
    prima_max: float
) -> Optional[float]:
    """
    Busca una prima dentro del rango especificado
    
    Args:
        precios_dia: Diccionario con precios del día
        prima_min: Prima mínima del rango
        prima_max: Prima máxima del rango
        
    Returns:
        Prima encontrada o None
    """
    # Buscar en orden: open, min, max, close
    for precio in [precios_dia['open'], precios_dia['min'], 
                   precios_dia['max'], precios_dia['close']]:
        if prima_min <= precio <= prima_max:
            return precio
    
    # Si no hay ninguna en rango exacto, buscar la más cercana
    todos_precios = [precios_dia['open'], precios_dia['min'], 
                     precios_dia['max'], precios_dia['close']]
    rango_medio = (prima_min + prima_max) / 2
    
    precio_mas_cercano = min(todos_precios, key=lambda x: abs(x - rango_medio))
    
    # Solo aceptar si está dentro del 50% de distancia
    if abs(precio_mas_cercano - rango_medio) <= rango_medio * 0.5:
        return precio_mas_cercano
    
    return None

def calcular_pnl_completo(
    client: RESTClient,
    option_ticker: str,
    fecha_entrada: datetime,
    prima_entrada: float,
    dias_holding: int = 2
) -> Dict[str, float]:
    """
    Calcula P&L completo para una opción
    
    Args:
        client: Cliente de Polygon
        option_ticker: Ticker de la opción
        fecha_entrada: Fecha de entrada
        prima_entrada: Prima de entrada
        dias_holding: Días de holding (1 o 2)
        
    Returns:
        Dict con ganancias día 1 y día 2
    """
    resultado = {
        'ganancia_d1': 0.0,
        'ganancia_d2': 0.0,
        'prima_max_d1': prima_entrada,
        'prima_max_d2': prima_entrada
    }
    
    # Día 1
    fecha_str = fecha_entrada.strftime('%Y-%m-%d')
    multiplier = 1 if fecha_entrada.year < 2025 else 5
    
    precios_d1 = obtener_precios_opcion_dia(client, option_ticker, fecha_str, multiplier)
    resultado['prima_max_d1'] = precios_d1['max']
    resultado['ganancia_d1'] = calcular_ganancia_opcion(prima_entrada, precios_d1['max'])
    
    # Día 2 (si aplica)
    if dias_holding >= 2:
        fecha_d2 = fecha_entrada + timedelta(days=1)
        # Saltar fin de semana
        while fecha_d2.weekday() >= 5:
            fecha_d2 += timedelta(days=1)
        
        fecha_d2_str = fecha_d2.strftime('%Y-%m-%d')
        precios_d2 = obtener_precios_opcion_dia(client, option_ticker, fecha_d2_str, multiplier)
        resultado['prima_max_d2'] = precios_d2['max']
        resultado['ganancia_d2'] = calcular_ganancia_opcion(prima_entrada, precios_d2['max'])
    
    return resultado