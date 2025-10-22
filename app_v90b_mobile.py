import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from polygon import RESTClient
from dotenv import load_dotenv
import os
import json

# Cargar variables de entorno
load_dotenv()

# AUTENTICACIÓN
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets.get("password", "Tomato4545@@"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔐 Password", type="password", on_change=password_entered, key="password")
        st.info("Introduce el password para acceder")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔐 Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrecto")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Configuración
st.set_page_config(
    page_title="AG1VRM",
    page_icon="📱",
    layout="centered"
)

st.title("📱 AG1VRM")
st.caption("Versión Móvil Simplificada")

# API
POLYGON_API_KEY = st.secrets.get("POLYGON_API_KEY", os.getenv("POLYGON_API_KEY"))
client = RESTClient(POLYGON_API_KEY)

# Zona horaria
ny_tz = pytz.timezone('America/New_York')

# Tickers
TICKERS = {
    'SPY': {'premium_min': 0.25, 'premium_max': 0.30, 'next_day_expiry': True},
    'QQQ': {'premium_min': 0.25, 'premium_max': 0.30, 'next_day_expiry': True},
    'AAPL': {'premium_min': 0.60, 'premium_max': 0.80, 'next_day_expiry': False},
    'GOOGL': {'premium_min': 0.60, 'premium_max': 0.80, 'next_day_expiry': False},
    'MSFT': {'premium_min': 0.60, 'premium_max': 0.80, 'next_day_expiry': False},
    'AMZN': {'premium_min': 0.60, 'premium_max': 0.80, 'next_day_expiry': False},
    'TSLA': {'premium_min': 2.50, 'premium_max': 3.00, 'next_day_expiry': False},
    'NVDA': {'premium_min': 0.60, 'premium_max': 0.80, 'next_day_expiry': False},
    'META': {'premium_min': 0.60, 'premium_max': 0.80, 'next_day_expiry': False},
    'AMD': {'premium_min': 0.60, 'premium_max': 0.80, 'next_day_expiry': False},
    'GLD': {'premium_min': 0.60, 'premium_max': 0.80, 'next_day_expiry': False},
    'SLV': {'premium_min': 0.60, 'premium_max': 0.80, 'next_day_expiry': False}
}

# Funciones auxiliares
def obtener_datos_stock(ticker, fecha_str):
    try:
        aggs = client.get_aggs(
            ticker=ticker,
            multiplier=30,
            timespan="minute",
            from_=fecha_str,
            to=fecha_str,
            limit=50000
        )
        
        if not aggs or len(aggs) == 0:
            return None
            
        df = pd.DataFrame([{
            'timestamp': a.timestamp,
            'open': a.open,
            'high': a.high,
            'low': a.low,
            'close': a.close,
            'volume': a.volume
        } for a in aggs])
        
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['datetime'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert(ny_tz)
        
        return df
    except Exception as e:
        return None

def calcular_rsi(precios, periodo=14):
    deltas = np.diff(precios)
    seed = deltas[:periodo+1]
    up = seed[seed >= 0].sum()/periodo
    down = -seed[seed < 0].sum()/periodo
    rs = up/down if down != 0 else 0
    rsi = np.zeros_like(precios)
    rsi[:periodo] = 100. - 100./(1. + rs)

    for i in range(periodo, len(precios)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up*(periodo-1) + upval)/periodo
        down = (down*(periodo-1) + downval)/periodo
        rs = up/down if down != 0 else 0
        rsi[i] = 100. - 100./(1. + rs)

    return rsi

def calcular_bollinger_bands(precios, periodo=20, num_std=2):
    sma = pd.Series(precios).rolling(window=periodo).mean().values
    std = pd.Series(precios).rolling(window=periodo).std().values
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return sma, upper_band, lower_band

def cargar_ganancia_historica(ticker, rsi_actual, bb_position):
    try:
        if os.path.exists('resultados_historicos.json'):
            with open('resultados_historicos.json', 'r') as f:
                historico = json.load(f)
            
            resultados_similares = []
            for resultado in historico.get(ticker, []):
                if (abs(resultado.get('rsi', 0) - rsi_actual) <= 5 and
                    abs(resultado.get('bb_position', 0) - bb_position) <= 0.1 and
                    resultado.get('probabilidad', 0) >= 60):
                    
                    ganancia_d1 = resultado.get('ganancia_d1', 0)
                    ganancia_d2 = resultado.get('ganancia_d2', 0)
                    resultados_similares.append(max(ganancia_d1, ganancia_d2))
            
            if resultados_similares:
                return round(np.median(resultados_similares), 1)
    except:
        pass
    
    return 0.0

def calcular_fecha_expiracion(fecha, next_day_expiry):
    if next_day_expiry:
        fecha_exp = fecha + timedelta(days=1)
        while fecha_exp.weekday() >= 5:
            fecha_exp += timedelta(days=1)
    else:
        dias_hasta_viernes = (4 - fecha.weekday()) % 7
        if dias_hasta_viernes == 0:
            dias_hasta_viernes = 7
        fecha_exp = fecha + timedelta(days=dias_hasta_viernes)
    return fecha_exp

def obtener_ganancia_opcion(ticker, strike, fecha_check, fecha_entrada, config):
    try:
        fecha_str = fecha_check.strftime('%Y-%m-%d')
        
        option_aggs = None
        for ajuste in [0, 0.01, -0.01, 0.02, -0.02, 0.03, -0.03]:
            strike_ajustado = round(strike * (1 + ajuste))
            strike_formateado = f"{int(strike_ajustado * 1000):08d}"
            fecha_expiracion = calcular_fecha_expiracion(fecha_entrada, config['next_day_expiry'])
            fecha_venc_str = fecha_expiracion.strftime('%y%m%d')
            option_ticker = f"O:{ticker}:{fecha_venc_str}P{strike_formateado}"
            
            try:
                option_aggs = client.get_aggs(
                    ticker=option_ticker,
                    multiplier=30,
                    timespan="minute",
                    from_=fecha_str,
                    to=fecha_str,
                    limit=50000
                )
                
                if option_aggs and len(option_aggs) > 0:
                    break
            except:
                continue
        
        if not option_aggs or len(option_aggs) == 0:
            return 0.0
        
        precios = [a.close for a in option_aggs]
        precio_inicial = precios[0]
        precio_maximo = max(precios)
        
        if config['premium_min'] <= precio_inicial <= config['premium_max']:
            ganancia_pct = ((precio_maximo - precio_inicial) / precio_inicial) * 100
            return round(ganancia_pct, 1)
        
        return 0.0
        
    except:
        return 0.0

def analizar_senal(ticker, fecha_analisis, usar_rsi, usar_bb, threshold):
    fecha_str = fecha_analisis.strftime('%Y-%m-%d')
    
    df = obtener_datos_stock(ticker, fecha_str)
    if df is None or len(df) == 0:
        return None
    
    target_time = fecha_analisis.replace(hour=10, minute=0, second=0, microsecond=0)
    target_time = ny_tz.localize(target_time)
    df_hasta_10am = df[df['datetime'] <= target_time].copy()
    
    if len(df_hasta_10am) < 20:
        return None
    
    precios = df_hasta_10am['close'].values
    rsi = calcular_rsi(precios)
    sma, upper_band, lower_band = calcular_bollinger_bands(precios)
    
    ultima_vela = df_hasta_10am.iloc[-1]
    rsi_actual = rsi[-1]
    bb_position = (ultima_vela['close'] - lower_band[-1]) / (upper_band[-1] - lower_band[-1]) if (upper_band[-1] - lower_band[-1]) != 0 else 0.5
    
    es_vela_roja = ultima_vela['close'] < ultima_vela['open']
    
    probabilidad = 0
    cumple_rsi = True
    cumple_bb = True
    
    if usar_rsi:
        cumple_rsi = rsi_actual < 40
        if cumple_rsi:
            probabilidad += 50
    
    if usar_bb:
        cumple_bb = bb_position < 0.2
        if cumple_bb:
            probabilidad += 50
    
    if not usar_rsi and not usar_bb:
        probabilidad = 50
    elif usar_rsi and not usar_bb:
        probabilidad = 100 if cumple_rsi else 0
    elif not usar_rsi and usar_bb:
        probabilidad = 100 if cumple_bb else 0
    
    ganancia_hist = cargar_ganancia_historica(ticker, rsi_actual, bb_position)
    
    config = TICKERS[ticker]
    precio_stock = ultima_vela['close']
    strike = round(precio_stock * 0.97)
    
    d1_pct = obtener_ganancia_opcion(ticker, strike, fecha_analisis, fecha_analisis, config)
    
    if config['next_day_expiry']:
        fecha_d2 = fecha_analisis + timedelta(days=1)
        while fecha_d2.weekday() >= 5:
            fecha_d2 += timedelta(days=1)
    else:
        dias_hasta_viernes = (4 - fecha_analisis.weekday()) % 7
        if dias_hasta_viernes == 0:
            dias_hasta_viernes = 7
        fecha_d2 = fecha_analisis + timedelta(days=dias_hasta_viernes)
    
    d2_pct = obtener_ganancia_opcion(ticker, strike, fecha_d2, fecha_analisis, config)
    
    # Calcular éxito D2
    exito_d2 = "✅" if d2_pct >= 100 else "❌"
    
    if probabilidad < threshold:
        senal = "🚫 NO"
    elif es_vela_roja:
        senal = "🎯 PUT"
    else:
        senal = "🟡 PUT"
    
    return {
        'Símbolo': ticker,
        'Hora': '10:00 AM ET',
        'Señal': senal,
        'G.Hist': ganancia_hist,
        'D1': d1_pct,
        'D2': d2_pct,
        'Éxito D2': exito_d2
    }

# INTERFAZ
st.markdown("### ⚙️ Configuración")

# Fecha
fecha_default = datetime.now(ny_tz).date() - timedelta(days=1)
while fecha_default.weekday() >= 5:
    fecha_default -= timedelta(days=1)

fecha_seleccionada = st.date_input(
    "📆 Fecha",
    value=fecha_default,
    max_value=datetime.now(ny_tz).date()
)

# Indicadores
col1, col2 = st.columns(2)
with col1:
    usar_rsi = st.checkbox("📊 RSI", value=True)
with col2:
    usar_bb = st.checkbox("📈 BB", value=True)

# Threshold
threshold = st.slider("🎯 Probabilidad mínima (%)", 0, 100, 60, 5)

# Ordenamiento
orden = st.selectbox(
    "🔢 Ordenar por:",
    ["Ganancia Histórica ↓", "Ticker (A-Z)"],
    index=0
)

# Botón
if st.button("🔄 Actualizar Datos", use_container_width=True):
    fecha_analisis = datetime.combine(fecha_seleccionada, datetime.min.time())
    fecha_analisis = ny_tz.localize(fecha_analisis)
    
    resultados = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(TICKERS.keys()):
        status_text.text(f"Analizando {ticker}...")
        progress_bar.progress((i + 1) / len(TICKERS))
        
        resultado = analizar_senal(ticker, fecha_analisis, usar_rsi, usar_bb, threshold)
        if resultado:
            resultados.append(resultado)
    
    progress_bar.empty()
    status_text.empty()
    
    if resultados:
        st.markdown("---")
        st.markdown("### 📊 Resultados")
        
        df = pd.DataFrame(resultados)
        
        # Ordenar según selección
        if "Ganancia Histórica" in orden:
            df = df.sort_values('G.Hist', ascending=False)
        else:
            df = df.sort_values('Símbolo')
        
        df = df.reset_index(drop=True)
        
        # Formatear para mostrar
        df['G.Hist'] = df['G.Hist'].apply(lambda x: f"{x:.1f}%")
        df['D1'] = df['D1'].apply(lambda x: f"{x:.1f}%")
        df['D2'] = df['D2'].apply(lambda x: f"{x:.1f}%")
        # La columna 'Éxito D2' ya tiene ✅ o ❌
        
        def colorear(row):
            if '🎯' in str(row['Señal']):
                return ['background-color: #d4edda'] * len(row)
            elif '🟡' in str(row['Señal']):
                return ['background-color: #fff3cd'] * len(row)
            return ['background-color: #f8d7da'] * len(row)
        
        def colorear_ghist(val):
            try:
                num = float(val.replace('%', ''))
                if num > 0:
                    return 'background-color: #fff3cd; font-weight: bold'
            except:
                pass
            return ''
        
        styled_df = df.style.apply(colorear, axis=1)\
                            .applymap(colorear_ghist, subset=['G.Hist'])\
                            .set_properties(**{
                                'text-align': 'center',
                                'font-size': '15px',
                                'padding': '8px'
                            })
        
        st.dataframe(styled_df, use_container_width=True, height=500)
        
        total = len([r for r in resultados if '🎯' in r['Señal']])
        st.success(f"✅ **{total} señales PUT detectadas**")
    else:
        st.warning("⚠️ No se encontraron datos para la fecha seleccionada")

st.markdown("---")
st.caption("AG1VRM © 2025 - Versión Móvil")
