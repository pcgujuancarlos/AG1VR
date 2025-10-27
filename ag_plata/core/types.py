"""
Tipos de datos y estructuras base para el sistema AG_PLATA
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List

@dataclass
class PriceData:
    """Datos de precio para una vela"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class Signal:
    """Señal de trading"""
    ticker: str
    fecha: datetime
    tipo: str  # 'primera_vela_roja', etc.
    precio_entrada: float
    rsi: Optional[float] = None
    bb_position: Optional[float] = None
    trade: bool = False
    mensaje: str = ""

@dataclass
class OptionContract:
    """Contrato de opción"""
    ticker: str
    underlying_ticker: str
    strike_price: float
    expiration_date: datetime
    contract_type: str  # 'PUT' o 'CALL'
    
@dataclass
class OptionResult:
    """Resultado del análisis de opciones"""
    ticker: str
    fecha: datetime
    strike: float
    prima_entrada: float
    prima_maxima_d1: float
    prima_maxima_d2: float
    ganancia_d1: float
    ganancia_d2: float
    exito_d1: bool
    exito_d2: bool
    mensaje: str = ""

@dataclass
class TickerConfig:
    """Configuración por ticker"""
    ticker: str
    prima_min: float
    prima_max: float
    tipo_vencimiento: str  # 'siguiente_dia' o 'viernes'
    umbral_rsi: float = 70.0
    umbral_bb: float = 0.8