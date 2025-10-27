"""
Filtros y validaciones - MÓDULO INDEPENDIENTE
"""
from typing import Dict, Optional
from .types import TickerConfig

# Configuración de rangos de prima por ticker
TICKER_CONFIGS = {
    'SPY': TickerConfig('SPY', 0.25, 0.30, 'siguiente_dia'),
    'QQQ': TickerConfig('QQQ', 0.25, 0.30, 'siguiente_dia'),
    'AAPL': TickerConfig('AAPL', 0.60, 0.80, 'viernes'),
    'AMD': TickerConfig('AMD', 0.60, 0.80, 'viernes'),
    'AMZN': TickerConfig('AMZN', 0.60, 0.80, 'viernes'),
    'META': TickerConfig('META', 0.60, 0.80, 'viernes'),
    'MSFT': TickerConfig('MSFT', 0.60, 0.80, 'viernes'),
    'GOOGL': TickerConfig('GOOGL', 0.60, 0.80, 'viernes'),
    'NVDA': TickerConfig('NVDA', 0.60, 0.80, 'viernes'),
    'TSLA': TickerConfig('TSLA', 2.50, 3.00, 'viernes'),
    'NFLX': TickerConfig('NFLX', 1.50, 2.50, 'viernes'),
    'MRNA': TickerConfig('MRNA', 2.00, 2.00, 'viernes'),
    'BAC': TickerConfig('BAC', 0.10, 0.20, 'viernes'),
    'SLV': TickerConfig('SLV', 0.10, 0.20, 'viernes'),
    'USO': TickerConfig('USO', 0.10, 0.20, 'viernes'),
    'GLD': TickerConfig('GLD', 0.60, 0.80, 'viernes'),
    'TNA': TickerConfig('TNA', 0.60, 0.80, 'viernes'),
    'XOM': TickerConfig('XOM', 0.60, 0.80, 'viernes'),
    'CVX': TickerConfig('CVX', 0.60, 0.80, 'viernes'),
    'PLTR': TickerConfig('PLTR', 0.60, 0.80, 'viernes'),
    'BABA': TickerConfig('BABA', 0.60, 0.80, 'viernes'),
    'CMG': TickerConfig('CMG', 0.60, 0.80, 'viernes'),
    'SMCI': TickerConfig('SMCI', 0.60, 0.80, 'viernes'),
    'AVGO': TickerConfig('AVGO', 0.60, 0.80, 'viernes'),
    'CORZ': TickerConfig('CORZ', 0.10, 0.20, 'viernes'),
    'BBAI': TickerConfig('BBAI', 0.10, 0.20, 'viernes'),
    'SOUN': TickerConfig('SOUN', 0.10, 0.20, 'viernes'),
    'LAC': TickerConfig('LAC', 0.10, 0.20, 'viernes'),
    'RKLB': TickerConfig('RKLB', 0.10, 0.20, 'viernes'),
    'POWI': TickerConfig('POWI', 0.60, 0.80, 'viernes'),
    'CRWD': TickerConfig('CRWD', 0.60, 0.80, 'viernes'),
    'IREN': TickerConfig('IREN', 0.10, 0.20, 'viernes'),
    'TIGO': TickerConfig('TIGO', 0.10, 0.20, 'viernes'),
    'RR': TickerConfig('RR', 0.10, 0.20, 'viernes')
}

def validar_prima_en_rango(
    ticker: str, 
    prima: float,
    tolerancia: float = 0.2
) -> bool:
    """
    Valida si una prima está dentro del rango configurado
    
    Args:
        ticker: Símbolo del activo
        prima: Prima a validar
        tolerancia: Tolerancia adicional (20% por defecto)
    
    Returns:
        True si está en rango, False en caso contrario
    """
    if ticker not in TICKER_CONFIGS:
        print(f"⚠️ Ticker {ticker} no configurado")
        return True  # Si no está configurado, aceptar
    
    config = TICKER_CONFIGS[ticker]
    min_permitido = config.prima_min * (1 - tolerancia)
    max_permitido = config.prima_max * (1 + tolerancia)
    
    return min_permitido <= prima <= max_permitido

def validar_ganancia_realista(
    ganancia_pct: float,
    max_permitido: float = 400.0
) -> bool:
    """
    Valida si una ganancia es realista
    
    Args:
        ganancia_pct: Porcentaje de ganancia
        max_permitido: Máximo permitido (default 400%)
    
    Returns:
        True si es realista, False si es sospechosa
    """
    return 0 <= ganancia_pct <= max_permitido

def filtrar_resultados_validos(resultados: list) -> list:
    """
    Filtra una lista de resultados para excluir datos inválidos
    
    Args:
        resultados: Lista de diccionarios con resultados
    
    Returns:
        Lista filtrada con solo resultados válidos
    """
    validos = []
    
    for r in resultados:
        ticker = r.get('ticker', '')
        prima = r.get('prima_entrada', 0)
        ganancia_d1 = r.get('ganancia_d1', 0)
        ganancia_d2 = r.get('ganancia_d2', 0)
        
        # Validar prima
        if not validar_prima_en_rango(ticker, prima):
            print(f"❌ Filtrado: {ticker} prima ${prima:.2f} fuera de rango")
            continue
        
        # Validar ganancias
        if not validar_ganancia_realista(ganancia_d1):
            print(f"❌ Filtrado: {ticker} ganancia D1 {ganancia_d1}% irreal")
            continue
            
        if not validar_ganancia_realista(ganancia_d2):
            print(f"❌ Filtrado: {ticker} ganancia D2 {ganancia_d2}% irreal")
            continue
        
        # Si pasa todas las validaciones
        validos.append(r)
    
    return validos

def get_ticker_config(ticker: str) -> Optional[TickerConfig]:
    """Obtiene la configuración de un ticker"""
    return TICKER_CONFIGS.get(ticker)