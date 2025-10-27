"""
Aplicación principal AG_PLATA - Estructura modular
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from polygon import RESTClient

# Importar módulos
from strategies.primera_vela_roja import PrimeraVelaRojaStrategy
from core.indicators import calcular_indicadores_completos
from core.filters import TICKER_CONFIGS, filtrar_resultados_validos

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')

def obtener_datos_ticker(client: RESTClient, ticker: str, fecha: datetime) -> pd.DataFrame:
    """Obtiene datos históricos de un ticker"""
    try:
        # Obtener últimos 30 días para calcular indicadores
        fecha_inicio = fecha - timedelta(days=30)
        
        aggs = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=fecha_inicio.strftime('%Y-%m-%d'),
            to=fecha.strftime('%Y-%m-%d'),
            limit=50
        )
        
        if not aggs:
            return pd.DataFrame()
        
        # Convertir a DataFrame
        data = []
        for agg in aggs:
            data.append({
                'timestamp': datetime.fromtimestamp(agg.timestamp/1000),
                'open': agg.open,
                'high': agg.high,
                'low': agg.low,
                'close': agg.close,
                'volume': agg.volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # Calcular indicadores
        df = calcular_indicadores_completos(df)
        
        return df
        
    except Exception as e:
        st.error(f"Error obteniendo datos de {ticker}: {e}")
        return pd.DataFrame()

def main():
    st.set_page_config(page_title="AG_PLATA - Modular", page_icon="🎯", layout="wide")
    
    st.title("🎯 AG_PLATA - Sistema Modular")
    st.info("Sistema con estructura modular para evitar conflictos entre módulos")
    
    # Cliente Polygon
    client = RESTClient(API_KEY)
    
    # Estrategia
    strategy = PrimeraVelaRojaStrategy(client)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Selección de fecha
        fecha_analisis = st.date_input(
            "Fecha de análisis",
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )
        fecha_analisis = datetime.combine(fecha_analisis, datetime.min.time())
        
        # Selección de tickers
        tickers_disponibles = list(TICKER_CONFIGS.keys())
        tickers_seleccionados = st.multiselect(
            "Seleccionar tickers",
            options=tickers_disponibles,
            default=['SPY', 'QQQ', 'AAPL']
        )
    
    # Botón de análisis
    if st.button("🔍 Analizar", type="primary"):
        resultados = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ticker in enumerate(tickers_seleccionados):
            status_text.text(f"Analizando {ticker}...")
            progress_bar.progress((i + 1) / len(tickers_seleccionados))
            
            # Obtener datos
            df = obtener_datos_ticker(client, ticker, fecha_analisis)
            
            if df.empty:
                continue
            
            # Evaluar estrategia
            signal = strategy.evaluar_entrada(df, ticker)
            
            if signal and signal.trade:
                # Calcular opciones
                option_result = strategy.calcular_opciones(signal)
                
                if option_result:
                    resultados.append({
                        'Ticker': ticker,
                        'Señal': '🔴 1VR',
                        'RSI': f"{signal.rsi:.1f}" if signal.rsi else "N/A",
                        'BB Pos': f"{signal.bb_position:.2f}" if signal.bb_position else "N/A",
                        'Strike': f"${option_result.strike}",
                        'Prima': f"${option_result.prima_entrada:.2f}",
                        'Ganancia D1': f"{option_result.ganancia_d1:.1f}%",
                        'Ganancia D2': f"{option_result.ganancia_d2:.1f}%",
                        'Éxito D1': '✅' if option_result.exito_d1 else '❌',
                        'Éxito D2': '✅' if option_result.exito_d2 else '❌'
                    })
        
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resultados
        if resultados:
            st.success(f"✅ Se encontraron {len(resultados)} señales")
            
            # Filtrar resultados válidos
            resultados_validos = filtrar_resultados_validos([
                {
                    'ticker': r['Ticker'],
                    'prima_entrada': float(r['Prima'].replace('$', '')),
                    'ganancia_d1': float(r['Ganancia D1'].replace('%', '')),
                    'ganancia_d2': float(r['Ganancia D2'].replace('%', ''))
                }
                for r in resultados
            ])
            
            if len(resultados_validos) < len(resultados):
                st.warning(f"⚠️ Se filtraron {len(resultados) - len(resultados_validos)} resultados con datos inválidos")
            
            # Crear DataFrame y mostrar
            df_resultados = pd.DataFrame(resultados)
            st.dataframe(df_resultados, use_container_width=True)
            
        else:
            st.info("No se encontraron señales para los tickers seleccionados")
    
    # Sección de información
    with st.expander("ℹ️ Información del Sistema"):
        st.markdown("""
        ### 🏗️ Estructura Modular
        
        El sistema está dividido en módulos independientes:
        
        - **`core/indicators.py`**: Cálculo de indicadores (RSI, BB)
        - **`core/filters.py`**: Validaciones y filtros
        - **`core/pnl.py`**: Cálculo de ganancias/pérdidas
        - **`strategies/primera_vela_roja.py`**: Estrategia específica
        
        ### ✅ Ventajas
        
        1. **Sin conflictos**: Cada módulo es independiente
        2. **Fácil mantenimiento**: Cambiar un módulo no afecta otros
        3. **Testeable**: Cada módulo se puede probar por separado
        4. **Escalable**: Fácil agregar nuevas estrategias
        
        ### 🔧 Problemas Resueltos
        
        - ✅ Detección correcta de 1VR para GLD y XOM
        - ✅ Validación de primas en rango correcto
        - ✅ Cálculo realista de ganancias (máx 400%)
        - ✅ Filtrado de datos inválidos
        """)

if __name__ == "__main__":
    main()