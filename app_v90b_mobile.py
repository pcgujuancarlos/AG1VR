import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# AUTENTICACIÓN CON PASSWORD
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

# Rangos de primas para opciones PUT (por ticker) - IGUAL QUE DESKTOP
RANGOS_PRIMA = {
    'SPY': {'min': 0.25, 'max': 0.30, 'vencimiento': 'siguiente_dia'},
    'QQQ': {'min': 0.25, 'max': 0.30, 'vencimiento': 'siguiente_dia'},
    'AAPL': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'AMD': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'AMZN': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'META': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'MSFT': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'GOOGL': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'NVDA': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'TSLA': {'min': 2.50, 'max': 3.00, 'vencimiento': 'viernes'},
    'NFLX': {'min': 1.50, 'max': 2.50, 'vencimiento': 'viernes'},
    'MRNA': {'min': 2.00, 'max': 2.00, 'vencimiento': 'viernes'},
    'BAC': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'SLV': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'USO': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'GLD': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'TNA': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'XOM': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'CVX': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'PLTR': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'BABA': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'CMG': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'SMCI': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'AVGO': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'CORZ': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'BBAI': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'SOUN': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'LAC': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'RKLB': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'POWI': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'CRWD': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'IREN': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'TIGO': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'},
    'RR': {'min': 0.10, 'max': 0.20, 'vencimiento': 'viernes'}
}

st.set_page_config(page_title="AG1VRM", page_icon="📱", layout="centered")

st.title("📱 AG1VRM")
st.caption("Versión Móvil Simplificada")

try:
    from polygon import RESTClient
except ImportError:
    st.warning("📦 Instalando polygon-api-client...")
    os.system(f"{sys.executable} -m pip install polygon-api-client -q")
    from polygon import RESTClient

API_KEY = os.getenv('POLYGON_API_KEY') or st.secrets.get("POLYGON_API_KEY")

# CLASE DE ANÁLISIS HISTÓRICO - IGUAL QUE DESKTOP
class AnalisisHistorico:
    def __init__(self):
        self.historial_file = "historial_operaciones.json"
        self.resultados_file = "resultados_historicos.json"
        self.cargar_historial()
        self.cargar_resultados_historicos()
    
    def cargar_historial(self):
        try:
            with open(self.historial_file, 'r') as f:
                self.historial = json.load(f)
        except FileNotFoundError:
            self.historial = {}
    
    def guardar_historial(self):
        with open(self.historial_file, 'w') as f:
            json.dump(self.historial, f, indent=2)
    
    def cargar_resultados_historicos(self):
        try:
            with open(self.resultados_file, 'r') as f:
                self.resultados_historicos = json.load(f)
        except FileNotFoundError:
            self.resultados_historicos = []
    
    def guardar_resultados_historicos(self):
        with open(self.resultados_file, 'w') as f:
            json.dump(self.resultados_historicos, f, indent=2)
    
    def agregar_resultado(self, fecha, ticker, rsi, bb_position, ganancia_d1, ganancia_d2, prima_entrada, prima_max_d1, prima_max_d2, strike):
        resultado = {
            'fecha': fecha,
            'ticker': ticker,
            'rsi': rsi,
            'bb_position': bb_position,
            'ganancia_d1': ganancia_d1,
            'ganancia_d2': ganancia_d2,
            'prima_entrada': prima_entrada,
            'prima_max_d1': prima_max_d1,
            'prima_max_d2': prima_max_d2,
            'strike': strike,
            'exitoso_d1': ganancia_d1 >= 100,
            'exitoso_d2': ganancia_d2 >= 100
        }
        self.resultados_historicos.append(resultado)
        self.guardar_resultados_historicos()
    
    def calcular_ganancia_historica(self, ticker, rsi, bb_position, fecha_excluir=None, usar_mediana=True):
        dias_similares = []
        
        rsi_rango = 10
        bb_rango = 0.20
        
        for resultado in self.resultados_historicos:
            if fecha_excluir and resultado.get('fecha') == fecha_excluir:
                continue
                
            if resultado['ticker'] == ticker:
                rsi_hist = resultado['rsi']
                bb_hist = resultado['bb_position']
                
                rsi_similar = abs(rsi_hist - rsi) <= rsi_rango
                bb_similar = abs(bb_hist - bb_position) <= bb_rango
                
                if rsi_similar and bb_similar:
                    ganancia = resultado['ganancia_d1']
                    if ganancia > 0:
                        dias_similares.append(ganancia)
        
        if len(dias_similares) == 0:
            return None, 0
        
        if usar_mediana:
            ganancia_hist = np.median(dias_similares)
        else:
            ganancia_hist = np.mean(dias_similares)
        
        return ganancia_hist, len(dias_similares)

# FUNCIÓN PARA CALCULAR GANANCIA REAL - IGUAL QUE DESKTOP
def calcular_ganancia_real_opcion(client, ticker, fecha, precio_stock):
    try:
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        rangos = RANGOS_PRIMA.get(ticker, {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'})
        
        if rangos['vencimiento'] == 'siguiente_dia':
            fecha_vencimiento = fecha + timedelta(days=1)
            while fecha_vencimiento.weekday() >= 5:
                fecha_vencimiento += timedelta(days=1)
        else:
            dias_hasta_viernes = (4 - fecha.weekday()) % 7
            if dias_hasta_viernes == 0:
                dias_hasta_viernes = 7
            fecha_vencimiento = fecha + timedelta(days=dias_hasta_viernes)
        
        strike = round(precio_stock * 0.97)
        strike_formateado = f"{int(strike * 1000):08d}"
        
        fecha_venc_str = fecha_vencimiento.strftime('%y%m%d')
        option_ticker = f"O:{ticker}:{fecha_venc_str}P{strike_formateado}"
        
        try:
            option_aggs = client.get_aggs(
                ticker=option_ticker,
                multiplier=1,
                timespan="minute",
                from_=fecha_str,
                to=fecha_str,
                limit=50000
            )
            
            if not option_aggs or len(option_aggs) == 0:
                raise Exception("No data")
        except:
            for ajuste in [0.01, -0.01, 0.02, -0.02, 0.03, -0.03]:
                strike_ajustado = round(strike * (1 + ajuste))
                strike_formateado = f"{int(strike_ajustado * 1000):08d}"
                option_ticker = f"O:{ticker}:{fecha_venc_str}P{strike_formateado}"
                
                try:
                    option_aggs = client.get_aggs(
                        ticker=option_ticker,
                        multiplier=1,
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
            return {
                'ganancia_pct': 0,
                'exito': '❌',
                'prima_entrada': 0,
                'prima_maxima': 0,
                'strike': strike,
                'ganancia_dia_siguiente': 0,
                'exito_dia2': '⚪',
                'prima_maxima_dia2': 0
            }
        
        precios_opcion = [a.close for a in option_aggs]
        prima_entrada = precios_opcion[0]
        prima_maxima = max(precios_opcion)
        
        if not (rangos['min'] <= prima_entrada <= rangos['max']):
            ganancia_pct = 0
            exito = '❌'
        else:
            if prima_maxima > prima_entrada:
                ganancia_pct = ((prima_maxima - prima_entrada) / prima_entrada) * 100
            else:
                ganancia_pct = 0
            
            exito = '✅' if ganancia_pct >= 100 else '❌'
        
        fecha_dia_siguiente = fecha + timedelta(days=1)
        while fecha_dia_siguiente.weekday() >= 5:
            fecha_dia_siguiente += timedelta(days=1)
        
        fecha_dia_sig_str = fecha_dia_siguiente.strftime('%Y-%m-%d')
        
        try:
            option_aggs_dia2 = client.get_aggs(
                ticker=option_ticker,
                multiplier=1,
                timespan="minute",
                from_=fecha_dia_sig_str,
                to=fecha_dia_sig_str,
                limit=50000
            )
            
            if option_aggs_dia2 and len(option_aggs_dia2) > 0:
                precios_dia2 = [a.close for a in option_aggs_dia2]
                prima_maxima_dia2 = max(precios_dia2)
                
                if prima_maxima_dia2 > prima_entrada:
                    ganancia_dia2_pct = ((prima_maxima_dia2 - prima_entrada) / prima_entrada) * 100
                else:
                    ganancia_dia2_pct = 0
                
                exito_dia2 = '✅' if ganancia_dia2_pct >= 100 else '❌'
            else:
                ganancia_dia2_pct = 0
                exito_dia2 = '⚪'
                prima_maxima_dia2 = 0
        except:
            ganancia_dia2_pct = 0
            exito_dia2 = '⚪'
            prima_maxima_dia2 = 0
        
        return {
            'ganancia_pct': round(ganancia_pct, 1),
            'exito': exito,
            'prima_entrada': prima_entrada,
            'prima_maxima': prima_maxima,
            'strike': strike,
            'ganancia_dia_siguiente': round(ganancia_dia2_pct, 1),
            'exito_dia2': exito_dia2,
            'prima_maxima_dia2': prima_maxima_dia2
        }
        
    except Exception as e:
        return {
            'ganancia_pct': 0,
            'exito': '❌',
            'prima_entrada': 0,
            'prima_maxima': 0,
            'strike': 0,
            'ganancia_dia_siguiente': 0,
            'exito_dia2': '⚪',
            'prima_maxima_dia2': 0
        }

# INTERFAZ MÓVIL SIMPLIFICADA
st.markdown("### ⚙️ Configuración")

# Selector de fecha
fecha_default = datetime.now()
if fecha_default.weekday() >= 5:
    dias_atras = fecha_default.weekday() - 4
    fecha_default = fecha_default - timedelta(days=dias_atras)
else:
    fecha_default = fecha_default - timedelta(days=1)

fecha_seleccionada = st.date_input(
    "📆 Fecha",
    value=fecha_default,
    max_value=datetime.now().date()
)

# Indicadores
col1, col2 = st.columns(2)
with col1:
    usar_rsi = st.checkbox("📊 RSI", value=True)
with col2:
    usar_bb = st.checkbox("📈 BB", value=True)

# Threshold
threshold = st.slider("🎯 Probabilidad mínima (%)", 0, 100, 70, 5)

# Ordenamiento
orden = st.selectbox(
    "🔢 Ordenar por:",
    ["Ganancia Histórica ↓", "Ticker (A-Z)"],
    index=0
)

# Botón de actualización
if st.button("🔄 Actualizar Datos", use_container_width=True):
    client = RESTClient(API_KEY)
    analisis = AnalisisHistorico()
    
    tickers = list(RANGOS_PRIMA.keys())
    resultados = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, ticker in enumerate(tickers):
        status_text.text(f"Analizando {ticker}...")
        progress_bar.progress((idx + 1) / len(tickers))
        
        try:
            fecha_str = fecha_seleccionada.strftime('%Y-%m-%d')
            
            aggs = client.get_aggs(
                ticker=ticker,
                multiplier=30,
                timespan="minute",
                from_=fecha_str,
                to=fecha_str,
                limit=50000
            )
            
            if not aggs or len(aggs) == 0:
                continue
            
            df = pd.DataFrame([{
                'timestamp': a.timestamp,
                'open': a.open,
                'high': a.high,
                'low': a.low,
                'close': a.close,
                'volume': a.volume
            } for a in aggs])
            
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df['datetime'] = df['datetime'].dt.tz_convert('America/New_York')
            
            df_10am = df[df['datetime'].dt.hour <= 10].copy()
            
            if len(df_10am) < 20:
                continue
            
            delta = df_10am['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            df_10am['RSI'] = 100 - (100 / (1 + rs))
            
            df_10am['SMA_20'] = df_10am['close'].rolling(20).mean()
            df_10am['STD_20'] = df_10am['close'].rolling(20).std()
            df_10am['BB_Upper'] = df_10am['SMA_20'] + (df_10am['STD_20'] * 2)
            df_10am['BB_Lower'] = df_10am['SMA_20'] - (df_10am['STD_20'] * 2)
            df_10am['BB_Position'] = (df_10am['close'] - df_10am['BB_Lower']) / (df_10am['BB_Upper'] - df_10am['BB_Lower'])
            
            if len(df_10am) < 2:
                continue
            
            ultimo = df_10am.iloc[-1]
            anterior = df_10am.iloc[-2]
            vela_roja = ultimo['close'] < anterior['close']
            
            if not vela_roja:
                continue
            
            rsi_actual = ultimo['RSI'] if not pd.isna(ultimo['RSI']) else 50
            bb_position_actual = ultimo['BB_Position'] if not pd.isna(ultimo['BB_Position']) else 0.5
            
            prob_base = 65
            
            if rsi_actual > 70:
                prob_ajustada = prob_base + 20
            elif rsi_actual > 60:
                prob_ajustada = prob_base + 10
            elif rsi_actual > 50:
                prob_ajustada = prob_base
            else:
                prob_ajustada = prob_base - 15
            
            if bb_position_actual > 0.8:
                prob_ajustada += 15
            elif bb_position_actual > 0.6:
                prob_ajustada += 8
            else:
                prob_ajustada -= 5
            
            probabilidad_final = max(0, min(100, prob_ajustada))
            
            if probabilidad_final >= threshold:
                señal = "🎯 PUT"
            elif probabilidad_final >= 60:
                señal = "🟡 PUT"
            else:
                señal = "🚫 NO"
            
            ganancia_hist, num_dias_similares = analisis.calcular_ganancia_historica(
                ticker, 
                rsi_actual, 
                bb_position_actual,
                fecha_excluir=fecha_seleccionada.strftime('%Y-%m-%d'),
                usar_mediana=True
            )
            
            ganancia_real = calcular_ganancia_real_opcion(
                client,
                ticker,
                fecha_seleccionada,
                ultimo['open']
            )
            
            analisis.agregar_resultado(
                fecha=fecha_seleccionada.strftime('%Y-%m-%d'),
                ticker=ticker,
                rsi=rsi_actual,
                bb_position=bb_position_actual,
                ganancia_d1=ganancia_real['ganancia_pct'],
                ganancia_d2=ganancia_real['ganancia_dia_siguiente'],
                prima_entrada=ganancia_real['prima_entrada'],
                prima_max_d1=ganancia_real['prima_maxima'],
                prima_max_d2=ganancia_real['prima_maxima_dia2'],
                strike=ganancia_real['strike']
            )
            
            # TABLA MÓVIL SIMPLIFICADA - SOLO ESTAS COLUMNAS
            if ganancia_hist is not None:
                ganancia_hist_display = f"{ganancia_hist:.1f}%"
            else:
                ganancia_hist_display = "Sin datos"
            
            resultados.append({
                'Símbolo': ticker,
                'Hora': '10:00 AM ET',
                'Señal': señal,
                'G.Hist': ganancia_hist_display,
                'D1': f"{ganancia_real['ganancia_pct']:.1f}%",
                'D2': f"{ganancia_real['ganancia_dia_siguiente']:.1f}%",
                'Éxito D2': ganancia_real['exito_dia2']
            })
            
        except Exception as e:
            continue
    
    progress_bar.empty()
    status_text.empty()
    
    if resultados:
        st.markdown("---")
        st.markdown("### 📊 Resultados")
        
        df = pd.DataFrame(resultados)
        
        # Ordenar
        if "Ganancia Histórica" in orden:
            df['G.Hist_sort'] = df['G.Hist'].replace('Sin datos', '0.0%').str.replace('%', '').astype(float)
            df = df.sort_values('G.Hist_sort', ascending=False).drop('G.Hist_sort', axis=1)
        else:
            df = df.sort_values('Símbolo')
        
        df = df.reset_index(drop=True)
        
        # Colorear filas
        def colorear(row):
            if '🎯' in str(row['Señal']):
                return ['background-color: #d4edda'] * len(row)
            elif '🟡' in str(row['Señal']):
                return ['background-color: #fff3cd'] * len(row)
            return ['background-color: #f8d7da'] * len(row)
        
        def colorear_ghist(val):
            if val != 'Sin datos':
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
                                'font-size': '14px',
                                'padding': '6px'
                            })
        
        st.dataframe(styled_df, use_container_width=True, height=500)
        
        total = len([r for r in resultados if '🎯' in r['Señal']])
        st.success(f"✅ **{total} señales PUT detectadas**")
        
        st.caption(f"📊 Total registros históricos: {len(analisis.resultados_historicos)}")
    else:
        st.warning("⚠️ No se encontraron datos para la fecha seleccionada")

st.markdown("---")
st.caption("AG1VRM © 2025 - Versión Móvil")