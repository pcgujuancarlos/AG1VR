"""
Estrategia Primera Vela Roja - MÓDULO INDEPENDIENTE
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import pandas as pd
from polygon import RESTClient

from .base import BaseStrategy
from ..core.types import Signal, OptionResult
from ..core.indicators import detectar_primera_vela_roja, calcular_indicadores_completos
from ..core.filters import get_ticker_config, TICKER_CONFIGS
from ..core.pnl import (
    obtener_precios_opcion_dia, 
    buscar_prima_en_rango,
    calcular_pnl_completo
)

class PrimeraVelaRojaStrategy(BaseStrategy):
    """Estrategia basada en la primera vela roja después de sobrecompra"""
    
    def __init__(self, client: RESTClient):
        super().__init__("Primera Vela Roja")
        self.client = client
    
    def evaluar_entrada(self, df: pd.DataFrame, ticker: str) -> Optional[Signal]:
        """
        Evalúa si hay primera vela roja
        
        Args:
            df: DataFrame con datos OHLCV
            ticker: Símbolo del activo
            
        Returns:
            Signal si hay entrada, None en caso contrario
        """
        if df.empty or len(df) < 20:  # Necesitamos al menos 20 velas para indicadores
            return None
        
        # Calcular indicadores si no existen
        if 'rsi' not in df.columns:
            df = calcular_indicadores_completos(df)
        
        # Obtener configuración del ticker
        config = get_ticker_config(ticker)
        if not config:
            print(f"⚠️ {ticker} no tiene configuración")
            return None
        
        # Detectar primera vela roja
        if detectar_primera_vela_roja(df, config.umbral_rsi, config.umbral_bb):
            ultima_vela = df.iloc[-1]
            
            return Signal(
                ticker=ticker,
                fecha=ultima_vela.name,  # El index debe ser la fecha
                tipo='primera_vela_roja',
                precio_entrada=ultima_vela['close'],
                rsi=ultima_vela.get('rsi'),
                bb_position=ultima_vela.get('bb_position'),
                trade=True,
                mensaje=f"1VR detectada - RSI: {ultima_vela.get('rsi', 0):.1f}, BB: {ultima_vela.get('bb_position', 0):.2f}"
            )
        
        return None
    
    def calcular_opciones(
        self, 
        signal: Signal,
        buscar_mejor_ganancia: bool = True
    ) -> Optional[OptionResult]:
        """
        Calcula la opción óptima para una señal
        
        Args:
            signal: Señal de entrada
            buscar_mejor_ganancia: Si True, busca la opción con mayor % ganancia
            
        Returns:
            OptionResult con los detalles de la opción
        """
        ticker = signal.ticker
        fecha = signal.fecha
        precio_stock = signal.precio_entrada
        
        # Obtener configuración
        config = get_ticker_config(ticker)
        if not config:
            return None
        
        # Calcular fecha de vencimiento
        fecha_venc = self._calcular_fecha_vencimiento(fecha, config.tipo_vencimiento)
        
        # Generar contratos potenciales
        contratos = self._generar_contratos(ticker, fecha_venc, precio_stock)
        
        if buscar_mejor_ganancia:
            # Nueva estrategia: buscar mayor % ganancia
            return self._buscar_mejor_ganancia(contratos, fecha, config)
        else:
            # Estrategia anterior: buscar primera en rango
            return self._buscar_primera_en_rango(contratos, fecha, config)
    
    def _calcular_fecha_vencimiento(
        self, 
        fecha_señal: datetime, 
        tipo: str
    ) -> datetime:
        """Calcula la fecha de vencimiento según el tipo"""
        if tipo == 'siguiente_dia':
            fecha_venc = fecha_señal + timedelta(days=1)
            while fecha_venc.weekday() >= 5:  # Saltar fin de semana
                fecha_venc += timedelta(days=1)
        else:  # 'viernes'
            dias_hasta_viernes = (4 - fecha_señal.weekday()) % 7
            if dias_hasta_viernes == 0 and fecha_señal.hour >= 16:
                dias_hasta_viernes = 7  # Siguiente viernes si ya pasó el cierre
            fecha_venc = fecha_señal + timedelta(days=dias_hasta_viernes)
        
        return fecha_venc
    
    def _generar_contratos(
        self, 
        ticker: str, 
        fecha_venc: datetime, 
        precio_stock: float
    ) -> List[Dict]:
        """Genera lista de contratos PUT potenciales"""
        contratos = []
        
        # Rango de strikes: 15% ITM a 5% OTM
        strike_min = int(precio_stock * 0.85)
        strike_max = int(precio_stock * 1.05)
        
        # Step según ticker
        if ticker in ['SPY', 'QQQ']:
            step = 1
        elif ticker in ['TSLA']:
            step = 5
        else:
            step = 1 if precio_stock < 100 else 5
        
        fecha_venc_str = fecha_venc.strftime('%y%m%d')
        
        for strike in range(strike_min, strike_max + 1, step):
            option_ticker = f"O:{ticker}{fecha_venc_str}P{strike*1000:08d}"
            
            contratos.append({
                'ticker': option_ticker,
                'strike_price': strike,
                'expiration_date': fecha_venc,
                'distancia_pct': ((strike - precio_stock) / precio_stock) * 100
            })
        
        return contratos
    
    def _buscar_mejor_ganancia(
        self, 
        contratos: List[Dict], 
        fecha: datetime, 
        config
    ) -> Optional[OptionResult]:
        """Busca el contrato con mayor potencial de ganancia %"""
        fecha_str = fecha.strftime('%Y-%m-%d')
        multiplier = 1 if fecha.year < 2025 else 5
        candidatos = []
        
        # Analizar cada contrato
        for contrato in contratos[:50]:  # Límite para no demorar
            if contrato['distancia_pct'] < -15 or contrato['distancia_pct'] > 5:
                continue
            
            option_ticker = contrato['ticker']
            
            # Obtener precios del día
            precios_dia = obtener_precios_opcion_dia(
                self.client, 
                option_ticker, 
                fecha_str, 
                multiplier
            )
            
            # Buscar prima en rango
            prima_entrada = buscar_prima_en_rango(
                precios_dia, 
                config.prima_min, 
                config.prima_max
            )
            
            if prima_entrada and prima_entrada > 0:
                # Calcular ganancia potencial
                ganancia_pct = ((precios_dia['max'] - prima_entrada) / prima_entrada * 100)
                
                candidatos.append({
                    'contrato': contrato,
                    'prima_entrada': prima_entrada,
                    'prima_maxima': precios_dia['max'],
                    'ganancia_pct': ganancia_pct
                })
        
        if not candidatos:
            return None
        
        # Seleccionar el mejor
        mejor = max(candidatos, key=lambda x: x['ganancia_pct'])
        
        # Calcular P&L completo
        pnl = calcular_pnl_completo(
            self.client,
            mejor['contrato']['ticker'],
            fecha,
            mejor['prima_entrada']
        )
        
        return OptionResult(
            ticker=config.ticker,
            fecha=fecha,
            strike=mejor['contrato']['strike_price'],
            prima_entrada=mejor['prima_entrada'],
            prima_maxima_d1=pnl['prima_max_d1'],
            prima_maxima_d2=pnl['prima_max_d2'],
            ganancia_d1=pnl['ganancia_d1'],
            ganancia_d2=pnl['ganancia_d2'],
            exito_d1=pnl['ganancia_d1'] >= 100,
            exito_d2=pnl['ganancia_d2'] >= 100,
            mensaje=f"Strike ${mejor['contrato']['strike_price']} - Mejor ganancia: {pnl['ganancia_d1']:.1f}%"
        )
    
    def _buscar_primera_en_rango(
        self, 
        contratos: List[Dict], 
        fecha: datetime, 
        config
    ) -> Optional[OptionResult]:
        """Busca el primer contrato con prima en rango (método anterior)"""
        # Implementación similar pero más simple
        # Solo busca el primero que encuentre en rango
        pass