"""
Estrategia base - Template para todas las estrategias
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from ..core.types import Signal, OptionResult

class BaseStrategy(ABC):
    """Clase base para todas las estrategias de trading"""
    
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.señales_activas: List[Signal] = []
    
    @abstractmethod
    def evaluar_entrada(self, df: pd.DataFrame, ticker: str) -> Optional[Signal]:
        """
        Evalúa si hay condiciones de entrada
        
        Args:
            df: DataFrame con datos OHLCV e indicadores
            ticker: Símbolo del activo
            
        Returns:
            Signal si hay entrada, None en caso contrario
        """
        pass
    
    @abstractmethod
    def calcular_opciones(self, signal: Signal) -> Optional[OptionResult]:
        """
        Calcula la opción óptima para una señal
        
        Args:
            signal: Señal de entrada
            
        Returns:
            OptionResult con los detalles de la opción
        """
        pass
    
    def validar_señal(self, signal: Signal) -> bool:
        """
        Valida que una señal sea válida
        
        Args:
            signal: Señal a validar
            
        Returns:
            True si es válida, False en caso contrario
        """
        # Validaciones básicas
        if not signal.ticker:
            return False
        
        if signal.precio_entrada <= 0:
            return False
        
        return True
    
    def agregar_señal(self, signal: Signal) -> None:
        """Agrega una señal a la lista de activas"""
        if self.validar_señal(signal):
            self.señales_activas.append(signal)
    
    def limpiar_señales_antiguas(self, dias: int = 7) -> None:
        """Limpia señales más antiguas que N días"""
        fecha_limite = datetime.now() - timedelta(days=dias)
        self.señales_activas = [
            s for s in self.señales_activas 
            if s.fecha > fecha_limite
        ]