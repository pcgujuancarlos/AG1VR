"""
Cálculo de indicadores técnicos - AISLADO para evitar conflictos
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional

def calcular_rsi(precios: pd.Series, periodo: int = 14) -> pd.Series:
    """
    Calcula el RSI (Relative Strength Index)
    
    Args:
        precios: Serie de precios de cierre
        periodo: Período para el cálculo (default 14)
    
    Returns:
        Serie con valores RSI
    """
    if len(precios) < periodo + 1:
        return pd.Series(index=precios.index, dtype=float)
    
    # Calcular cambios
    delta = precios.diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    
    # Evitar división por cero
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calcular_bollinger_bands(
    precios: pd.Series, 
    periodo: int = 20, 
    num_std: float = 2
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Calcula las Bandas de Bollinger
    
    Args:
        precios: Serie de precios
        periodo: Período para la media móvil
        num_std: Número de desviaciones estándar
    
    Returns:
        Tupla (media, banda_superior, banda_inferior, posicion_bb)
    """
    if len(precios) < periodo:
        empty = pd.Series(index=precios.index, dtype=float)
        return empty, empty, empty, empty
    
    # Media móvil
    media = precios.rolling(window=periodo).mean()
    
    # Desviación estándar
    std = precios.rolling(window=periodo).std()
    
    # Bandas
    banda_superior = media + (num_std * std)
    banda_inferior = media - (num_std * std)
    
    # Posición BB (0 = banda inferior, 1 = banda superior)
    posicion_bb = (precios - banda_inferior) / (banda_superior - banda_inferior)
    
    return media, banda_superior, banda_inferior, posicion_bb

def detectar_primera_vela_roja(
    df: pd.DataFrame,
    umbral_rsi: float = 70.0,
    umbral_bb: float = 0.8
) -> bool:
    """
    Detecta si hay primera vela roja según las condiciones
    
    Args:
        df: DataFrame con datos OHLCV y indicadores
        umbral_rsi: Umbral mínimo de RSI
        umbral_bb: Umbral mínimo de posición BB
    
    Returns:
        True si hay primera vela roja, False en caso contrario
    """
    if df.empty or len(df) < 2:
        return False
    
    # Verificar última vela
    ultima_vela = df.iloc[-1]
    penultima_vela = df.iloc[-2]
    
    # Condiciones para primera vela roja:
    # 1. La vela actual es roja (close < open)
    # 2. La vela anterior era verde (close > open) 
    # 3. RSI > umbral
    # 4. BB Position > umbral
    
    es_roja = ultima_vela['close'] < ultima_vela['open']
    anterior_verde = penultima_vela['close'] > penultima_vela['open']
    
    rsi_alto = ultima_vela.get('rsi', 0) > umbral_rsi
    bb_alto = ultima_vela.get('bb_position', 0) > umbral_bb
    
    return es_roja and anterior_verde and rsi_alto and bb_alto

def calcular_indicadores_completos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula todos los indicadores necesarios
    
    Args:
        df: DataFrame con datos OHLCV
    
    Returns:
        DataFrame con indicadores añadidos
    """
    df = df.copy()
    
    # RSI
    df['rsi'] = calcular_rsi(df['close'])
    
    # Bollinger Bands
    _, _, _, df['bb_position'] = calcular_bollinger_bands(df['close'])
    
    return df