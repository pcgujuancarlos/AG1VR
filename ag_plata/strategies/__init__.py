"""
Trading strategies for AG_PLATA system
"""
from .base import BaseStrategy
from .primera_vela_roja import PrimeraVelaRojaStrategy

__all__ = ['BaseStrategy', 'PrimeraVelaRojaStrategy']