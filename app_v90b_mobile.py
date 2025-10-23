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

# Rangos de primas para opciones PUT (por ticker)
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

try:
    from polygon import RESTClient
except ImportError:
    st.warning("📦 Instalando polygon-api-client...")
    os.system(f"{sys.executable} -m pip install polygon-api-client -q")
    from polygon import RESTClient

API_KEY = os.getenv('POLYGON_API_KEY') or st.secrets.get("POLYGON_API_KEY")

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
        
        # AMPLIAR RANGOS para encontrar más días similares
        rsi_rango = 10
        bb_rango = 0.20
        
        print(f"\n🔍 BUSCANDO DÍAS SIMILARES PARA {ticker}")
        print(f"   RSI objetivo: {rsi:.1f} (rango: {rsi-rsi_rango:.1f} - {rsi+rsi_rango:.1f})")
        print(f"   BB objetivo: {bb_position:.2f} (rango: {bb_position-bb_rango:.2f} - {bb_position+bb_rango:.2f})")
        print(f"   Fecha a excluir: {fecha_excluir}")
        print(f"   Total registros históricos: {len(self.resultados_historicos)}")
        
        for resultado in self.resultados_historicos:
            if fecha_excluir and resultado.get('fecha') == fecha_excluir:
                print(f"   ⏭️  Saltando fecha actual: {resultado.get('fecha')}")
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
                        print(f"   ✅ {resultado['fecha']}: RSI={rsi_hist:.1f}, BB={bb_hist:.2f} → D1={ganancia:.1f}%")
        
        if len(dias_similares) == 0:
            print(f"   ❌ No se encontraron días similares")
            return None, 0
        
        if usar_mediana:
            ganancia_hist = np.median(dias_similares)
        else:
            ganancia_hist = np.mean(dias_similares)
        
        print(f"   📊 Ganancias encontradas: {dias_similares}")
        print(f"   📈 {'Mediana' if usar_mediana else 'Promedio'}: {ganancia_hist:.1f}%")
        print(f"   📌 Total días similares: {len(dias_similares)}")
        
        return ganancia_hist, len(dias_similares)
    
    def agregar_operacion(self, ticker, rsi, bb_position, resultado, timestamp):
        if ticker not in self.historial:
            self.historial[ticker] = []
        
        self.historial[ticker].append({
            'timestamp': timestamp,
            'rsi': rsi,
            'bb_position': bb_position,
            'resultado': resultado,
            'exitosa': resultado > 0
        })
        self.guardar_historial()

def calcular_fecha_vencimiento(fecha_senal, ticker):
    rango = RANGOS_PRIMA.get(ticker, {})
    tipo_vencimiento = rango.get('vencimiento', 'viernes')
    
    if tipo_vencimiento == 'siguiente_dia':
        fecha_venc = fecha_senal + timedelta(days=1)
        while fecha_venc.weekday() >= 5:
            fecha_venc += timedelta(days=1)
        print(f"   [VENC] {ticker} siguiente_dia: {fecha_senal} → {fecha_venc} ({fecha_venc.strftime('%A')})")
        return fecha_venc
    else:
        dia_semana = fecha_senal.weekday()
        if dia_semana <= 4:
            dias_hasta_viernes = 4 - dia_semana
            if dias_hasta_viernes == 0:
                dias_hasta_viernes = 7
        else:
            dias_hasta_viernes = 5 if dia_semana == 5 else 4
        fecha_venc = fecha_senal + timedelta(days=dias_hasta_viernes)
        print(f"   [VENC] {ticker} viernes: {fecha_senal} ({fecha_senal.strftime('%A')}) → {fecha_venc} ({fecha_venc.strftime('%A')}) [+{dias_hasta_viernes}d]")
        return fecha_venc

def buscar_contratos_disponibles(client, ticker, fecha_vencimiento):
    try:
        fecha_venc_str = fecha_vencimiento.strftime('%Y-%m-%d')
        import requests
        url = f"https://api.polygon.io/v3/reference/options/contracts"
        
        params = {
            'underlying_ticker': ticker,
            'contract_type': 'put',
            'expiration_date': fecha_venc_str,
            'limit': 1000,
            'apiKey': API_KEY
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                print(f"✅ Encontrados {len(data['results'])} contratos para {fecha_venc_str}")
                return data['results']
        
        print(f"⚠️  No hay contratos para {fecha_venc_str}, buscando en rango cercano (±30 días)...")
        
        fecha_desde = (fecha_vencimiento - timedelta(days=30)).strftime('%Y-%m-%d')
        fecha_hasta = (fecha_vencimiento + timedelta(days=30)).strftime('%Y-%m-%d')
        
        params = {
            'underlying_ticker': ticker,
            'contract_type': 'put',
            'expiration_date.gte': fecha_desde,
            'expiration_date.lte': fecha_hasta,
            'limit': 1000,
            'apiKey': API_KEY
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                print(f"✅ Encontrados {len(data['results'])} contratos en rango cercano")
                return data['results']
        
        return []
        
    except Exception as e:
        print(f"Error buscando contratos: {str(e)}")
        return []

def calcular_ganancia_real_opcion(client, ticker, fecha, precio_stock):
    try:
        if ticker not in RANGOS_PRIMA:
            return {
                'ganancia_pct': 0,
                'ganancia_dia_siguiente': 0,
                'exito': '❌',
                'exito_dia2': '❌',
                'strike': 0,
                'prima_entrada': 0,
                'prima_maxima': 0,
                'prima_maxima_dia2': 0,
                'mensaje': 'Sin rango'
            }
        
        rango = RANGOS_PRIMA[ticker]
        fecha_vencimiento = calcular_fecha_vencimiento(fecha, ticker)
        strike_objetivo = round(precio_stock * 0.97, 2)
        
        fecha_str = fecha.strftime('%Y-%m-%d')
        fecha_dia_siguiente = fecha + timedelta(days=1)
        fecha_dia_siguiente_str = fecha_dia_siguiente.strftime('%Y-%m-%d')
        
        print(f"\n=== BUSCANDO OPCIÓN PARA {ticker} ===")
        print(f"Fecha análisis: {fecha_str}")
        print(f"Precio stock: ${precio_stock:.2f}")
        print(f"Strike objetivo (3% OTM): ${strike_objetivo:.2f}")
        
        print("\n🔍 Buscando contratos disponibles...")
        contratos = buscar_contratos_disponibles(client, ticker, fecha_vencimiento)
        
        if not contratos or len(contratos) == 0:
            print(f"❌ No hay contratos PUT disponibles para {ticker}")
            return {
                'ganancia_pct': 0,
                'ganancia_dia_siguiente': 0,
                'exito': '❌',
                'exito_dia2': '❌',
                'strike': strike_objetivo,
                'prima_entrada': 0,
                'prima_maxima': 0,
                'prima_maxima_dia2': 0,
                'mensaje': 'Sin opciones disponibles'
            }
        
        print(f"✅ Encontrados {len(contratos)} contratos PUT")
        
        from collections import defaultdict
        contratos_por_fecha = defaultdict(list)
        for contrato in contratos:
            exp_date = contrato.get('expiration_date', '')
            contratos_por_fecha[exp_date].append(contrato)
        
        fechas_disponibles = sorted(contratos_por_fecha.keys())
        fecha_elegida = None
        
        if len(fechas_disponibles) > 1:
            if isinstance(fecha_vencimiento, datetime):
                fecha_venc_date = fecha_vencimiento.date()
            else:
                fecha_venc_date = fecha_vencimiento
            
            fecha_elegida = min(
                fechas_disponibles, 
                key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d').date() - fecha_venc_date).days)
            )
            contratos = contratos_por_fecha[fecha_elegida]
        else:
            fecha_elegida = fechas_disponibles[0]
            contratos = contratos_por_fecha[fecha_elegida]
        
        mejor_contrato = None
        menor_diferencia = float('inf')
        
        for contrato in contratos:
            strike_contrato = contrato.get('strike_price', 0)
            diferencia = abs(strike_contrato - strike_objetivo)
            
            if diferencia < menor_diferencia:
                menor_diferencia = diferencia
                mejor_contrato = contrato
        
        if not mejor_contrato:
            print("❌ No se encontró strike cercano")
            return {
                'ganancia_pct': 0,
                'ganancia_dia_siguiente': 0,
                'exito': '❌',
                'exito_dia2': '❌',
                'strike': strike_objetivo,
                'prima_entrada': 0,
                'prima_maxima': 0,
                'prima_maxima_dia2': 0,
                'mensaje': 'Strike no disponible'
            }
        
        option_ticker = mejor_contrato['ticker']
        strike_real = mejor_contrato['strike_price']
        
        print(f"📌 Contrato seleccionado: {option_ticker}")
        print(f"📌 Strike real: ${strike_real}")
        
        try:
            option_aggs_dia1 = client.get_aggs(
                ticker=option_ticker,
                multiplier=1,
                timespan="minute",
                from_=fecha_str,
                to=fecha_str,
                limit=50000
            )
            
            print(f"📊 Día 1: {len(option_aggs_dia1) if option_aggs_dia1 else 0} registros")
            
            if not option_aggs_dia1 or len(option_aggs_dia1) == 0:
                print(f"❌ NO SE ENCONTRARON DATOS para {option_ticker}")
                return {
                    'ganancia_pct': 0,
                    'ganancia_dia_siguiente': 0,
                    'exito': '❌',
                    'exito_dia2': '❌',
                    'strike': strike_real,
                    'prima_entrada': 0,
                    'prima_maxima': 0,
                    'prima_maxima_dia2': 0,
                    'mensaje': 'Sin datos opción'
                }
            
            precios_dia1 = []
            for agg in option_aggs_dia1:
                precios_dia1.append({
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close
                })
            
            prima_entrada = precios_dia1[0]['open']
            prima_maxima_dia1 = max([p['high'] for p in precios_dia1])
            
            print(f"Prima apertura: ${prima_entrada:.2f}")
            print(f"Rango objetivo: ${rango['min']:.2f} - ${rango['max']:.2f}")
            
            if prima_entrada < rango['min'] or prima_entrada > rango['max']:
                print("Prima fuera de rango - buscando momento correcto...")
                for p in precios_dia1:
                    if rango['min'] <= p['open'] <= rango['max']:
                        prima_entrada = p['open']
                        print(f"✅ Prima en rango encontrada: ${prima_entrada:.2f}")
                        break
            
            print(f"\n📊 CÁLCULO DÍA 1:")
            print(f"  Prima entrada: ${prima_entrada:.2f}")
            print(f"  Prima máxima día 1: ${prima_maxima_dia1:.2f}")
            
            if prima_entrada > 0:
                ganancia_dia1 = ((prima_maxima_dia1 - prima_entrada) / prima_entrada) * 100
            else:
                ganancia_dia1 = 0
            
            exito_dia1 = '✅' if ganancia_dia1 >= 100 else '❌'
            
            print(f"  Ganancia día 1: {ganancia_dia1:.1f}% {exito_dia1}")
            
            print(f"\n📊 CÁLCULO DÍA 2:")
            print(f"🔄 Buscando datos del día siguiente: {fecha_dia_siguiente_str}...")
            
            option_aggs_dia2 = None
            try:
                option_aggs_dia2 = client.get_aggs(
                    ticker=option_ticker,
                    multiplier=1,
                    timespan="minute",
                    from_=fecha_dia_siguiente_str,
                    to=fecha_dia_siguiente_str,
                    limit=50000
                )
            except:
                pass
            
            if option_aggs_dia2 and len(option_aggs_dia2) > 0:
                print(f"  ✅ {len(option_aggs_dia2)} registros encontrados día 2")
                
                precios_dia2 = []
                for agg in option_aggs_dia2:
                    precios_dia2.append({
                        'open': agg.open,
                        'high': agg.high,
                        'low': agg.low,
                        'close': agg.close
                    })
                
                prima_maxima_dia2 = max([p['high'] for p in precios_dia2])
                
                print(f"  Prima entrada (MISMA): ${prima_entrada:.2f}")
                print(f"  Prima máxima día 2: ${prima_maxima_dia2:.2f}")
                
                if prima_entrada > 0:
                    ganancia_dia2 = ((prima_maxima_dia2 - prima_entrada) / prima_entrada) * 100
                else:
                    ganancia_dia2 = 0
                
                exito_dia2 = '✅' if ganancia_dia2 >= 100 else '❌'
                
                print(f"  Ganancia día 2: {ganancia_dia2:.1f}% {exito_dia2}")
            else:
                print("  ❌ No hay datos del día siguiente")
                prima_maxima_dia2 = 0
                ganancia_dia2 = 0
                exito_dia2 = '⚪'
            
            print("=" * 50)
            
            return {
                'ganancia_pct': round(ganancia_dia1, 1),
                'ganancia_dia_siguiente': round(ganancia_dia2, 1),
                'exito': exito_dia1,
                'exito_dia2': exito_dia2,
                'strike': strike_real,
                'prima_entrada': round(prima_entrada, 2),
                'prima_maxima': round(prima_maxima_dia1, 2),
                'prima_maxima_dia2': round(prima_maxima_dia2, 2),
                'mensaje': f'D1: ${prima_entrada}→${prima_maxima_dia1} | D2: ${prima_maxima_dia2}'
            }
            
        except Exception as e:
            print(f"❌ ERROR API: {str(e)}")
            return {
                'ganancia_pct': 0,
                'ganancia_dia_siguiente': 0,
                'exito': '❌',
                'exito_dia2': '❌',
                'strike': strike_real,
                'prima_entrada': 0,
                'prima_maxima': 0,
                'prima_maxima_dia2': 0,
                'mensaje': f'API error: {str(e)[:30]}'
            }
        
    except Exception as e:
        print(f"❌ ERROR GENERAL: {str(e)}")
        return {
            'ganancia_pct': 0,
            'ganancia_dia_siguiente': 0,
            'exito': '❌',
            'exito_dia2': '❌',
            'strike': 0,
            'prima_entrada': 0,
            'prima_maxima': 0,
            'prima_maxima_dia2': 0,
            'mensaje': f'Error: {str(e)}'
        }

def cargar_historico_4_meses(client, analisis, tickers):
    st.info("🔄 Cargando histórico de 4 meses... Esto puede tardar varios minutos.")
    
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=120)
    
    fecha_desde = fecha_inicio.strftime('%Y-%m-%d')
    fecha_hasta = fecha_fin.strftime('%Y-%m-%d')
    
    st.write(f"📅 Buscando datos desde {fecha_desde} hasta {fecha_hasta}")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_dias_analizados = 0
    total_senales_detectadas = 0
    total_guardados = 0
    
    for idx, ticker in enumerate(tickers):
        progress = (idx + 1) / len(tickers)
        progress_bar.progress(progress)
        status_text.text(f"Procesando histórico de {ticker}... ({idx + 1}/{len(tickers)})")
        
        try:
            aggs = client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=fecha_desde,
                to=fecha_hasta,
                limit=5000
            )
            
            if not aggs or len(aggs) < 20:
                st.write(f"⚠️ {ticker}: Datos insuficientes ({len(aggs) if aggs else 0} días)")
                continue
            
            st.write(f"📊 {ticker}: {len(aggs)} días descargados")
            
            data = []
            for agg in aggs:
                data.append({
                    'timestamp': pd.to_datetime(agg.timestamp, unit='ms'),
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            df = df.sort_index()
            
            total_dias_analizados += len(df)
            
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            df['SMA_20'] = df['close'].rolling(20).mean()
            df['STD_20'] = df['close'].rolling(20).std()
            df['BB_Upper'] = df['SMA_20'] + (df['STD_20'] * 2)
            df['BB_Lower'] = df['SMA_20'] - (df['STD_20'] * 2)
            df['BB_Position'] = (df['close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
            
            senales_ticker = 0
            guardados_ticker = 0
            
            for i in range(1, len(df)):
                actual = df.iloc[i]
                anterior = df.iloc[i-1]
                
                vela_roja = actual['close'] < anterior['close']
                
                if not vela_roja:
                    continue
                
                if pd.isna(actual['RSI']) or pd.isna(actual['BB_Position']):
                    continue
                
                rsi_actual = actual['RSI']
                bb_position_actual = actual['BB_Position']
                
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
                
                if probabilidad_final < 60:
                    continue
                
                senales_ticker += 1
                total_senales_detectadas += 1
                
                fecha_senal = actual.name.date()
                
                ya_existe = any(
                    r['fecha'] == str(fecha_senal) and r['ticker'] == ticker 
                    for r in analisis.resultados_historicos
                )
                
                if ya_existe:
                    continue
                
                ganancia_real = calcular_ganancia_real_opcion(
                    client,
                    ticker,
                    fecha_senal,
                    actual['open']
                )
                
                analisis.agregar_resultado(
                    fecha=str(fecha_senal),
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
                guardados_ticker += 1
                total_guardados += 1
            
            st.write(f"✅ {ticker}: {senales_ticker} señales detectadas → {guardados_ticker} guardadas")
        
        except Exception as e:
            st.warning(f"⚠️ Error en {ticker}: {str(e)}")
            continue
    
    progress_bar.empty()
    status_text.empty()
    
    st.success(f"""
    ✅ Proceso completado:
    - 📅 Días analizados: {total_dias_analizados}
    - 🎯 Señales detectadas: {total_senales_detectadas}
    - 💾 Resultados guardados: {total_guardados}
    """)
    st.balloons()
    
    time.sleep(3)
    st.rerun()

def main():
    st.title("📱 AG1VRM - VERSIÓN MÓVIL")
    
    try:
        client = RESTClient(API_KEY)
        st.success("✅ Conectado a Polygon.io")
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return
    
    tickers = ['SPY', 'QQQ', 'GOOGL', 'AMD', 'GLD', 'BBAI', 'NFLX', 'AMZN', 'CORZ', 'XOM', 'BAC']
    analisis = AnalisisHistorico()
    
    if len(analisis.resultados_historicos) < 200:
        st.warning(f"⚠️ Solo hay {len(analisis.resultados_historicos)} registros históricos. Se recomienda tener al menos 200.")
        
        with st.expander("🔄 ¿Cargar datos históricos ahora?", expanded=True):
            st.info("Se cargarán ~4 meses de datos. Esto tarda 10-15 minutos pero solo se hace una vez.")
            if st.button("✅ SÍ, cargar ahora", type="primary"):
                cargar_historico_4_meses(client, analisis, tickers)
                return
    
    with st.sidebar:
        st.header("⚙️ Configuración")
        usar_rsi = st.checkbox("Usar RSI", value=True)
        usar_bb = st.checkbox("Usar Bollinger Bands", value=True)
        threshold = st.slider("Threshold mínimo (%)", 50, 90, 70)
        
        if st.button("🔄 Actualizar Datos"):
            st.rerun()
        
        st.subheader("📅 Fecha de Backtesting")
        fecha_seleccionada = st.date_input(
            "Selecciona fecha",
            value=datetime(2025, 10, 17).date(),
            max_value=datetime.now().date()
        )
        st.info(f"Analizando: {fecha_seleccionada.strftime('%A, %d %B %Y')}")
        
        st.divider()
        st.subheader("📊 Base de Datos Histórica")
        
        num_registros = len(analisis.resultados_historicos)
        if num_registros > 0:
            st.success(f"✅ {num_registros} resultados guardados")
            
            fechas = [r['fecha'] for r in analisis.resultados_historicos]
            if fechas:
                fecha_min = min(fechas)
                fecha_max = max(fechas)
                st.caption(f"Rango: {fecha_min} a {fecha_max}")
        else:
            st.warning("⚠️ Sin datos históricos")
        
        if st.button("🔄 Cargar Histórico (4 meses)", help="Analiza los últimos 4 meses y guarda todos los D1"):
            cargar_historico_4_meses(client, analisis, tickers)
    
    fecha_desde = (fecha_seleccionada - timedelta(days=30)).strftime('%Y-%m-%d')
    fecha_hasta = fecha_seleccionada.strftime('%Y-%m-%d')
    
    # VERSIÓN MÓVIL - SIN COLUMNAS, TODO EN ANCHO COMPLETO
    st.subheader("📊 Señales en Tiempo Real")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    resultados = []
    total_tickers = len(tickers)
    for idx, ticker in enumerate(tickers):
        progress = (idx + 1) / total_tickers
        progress_bar.progress(progress)
        status_text.text(f"Analizando {ticker}... ({idx + 1}/{total_tickers})")
        
        try:
            aggs = client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=fecha_desde,
                to=fecha_hasta,
                limit=30
            )
            
            if not aggs:
                continue
            
            data = []
            for agg in aggs:
                data.append({
                    'timestamp': pd.to_datetime(agg.timestamp, unit='ms'),
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            df = df.sort_index()
            
            if len(df) < 10:
                continue
            
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            df['SMA_20'] = df['close'].rolling(20).mean()
            df['STD_20'] = df['close'].rolling(20).std()
            df['BB_Upper'] = df['SMA_20'] + (df['STD_20'] * 2)
            df['BB_Lower'] = df['SMA_20'] - (df['STD_20'] * 2)
            df['BB_Position'] = (df['close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
            
            if len(df) < 2:
                continue
                
            ultimo = df.iloc[-1]
            anterior = df.iloc[-2]
            vela_roja = ultimo['close'] < anterior['close']
            
            if not vela_roja:
                continue
            
            hora_senal = "10:00 AM ET"
            
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
                trade = "SI"
            elif probabilidad_final >= 60:
                señal = "🟡 PUT"
                trade = "SI"
            else:
                señal = "🚫 NO"
                trade = "NO"
            
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
            
            if ganancia_hist is not None:
                ganancia_hist_str = f"{ganancia_hist:.1f}% ({num_dias_similares})"
            else:
                ganancia_hist_str = "Sin datos"
            
            resultados.append({
                'Activo': ticker,
                'Hora': hora_senal,
                'Señal': señal,
                'Probabilidad': probabilidad_final,
                'RSI': rsi_actual,
                'BB': bb_position_actual,
                'Trade': trade,
                'Strike': f"${ganancia_real.get('strike', 0):.0f}",
                'Prima Entrada': f"${ganancia_real.get('prima_entrada', 0):.2f}",
                'Prima Máx D1': f"${ganancia_real.get('prima_maxima', 0):.2f}",
                'Prima Máx D2': f"${ganancia_real.get('prima_maxima_dia2', 0):.2f}",
                'Ganancia Hist': ganancia_hist_str,
                'Ganancia Día 1': ganancia_real['ganancia_pct'],
                'Ganancia Día 2': ganancia_real['ganancia_dia_siguiente'],
                'Éxito D1': ganancia_real['exito'],
                'Éxito D2': ganancia_real['exito_dia2']
            })
            
        except Exception as e:
            st.write(f"❌ {ticker}: Error - {str(e)}")
    
    progress_bar.empty()
    status_text.empty()
    
    if resultados:
        st.subheader("📊 Resultados de Análisis")
        
        df_resultados = pd.DataFrame(resultados)
        
        # VERSIÓN MÓVIL - TABLA SIMPLIFICADA (solo 7 columnas)
        df_mobile = df_resultados[['Activo', 'Hora', 'Señal', 'Ganancia Hist', 'Ganancia Día 1', 'Ganancia Día 2', 'Éxito D2']].copy()
        df_mobile = df_mobile.rename(columns={
            'Activo': 'Símbolo',
            'Hora': 'Hora',
            'Señal': 'Señal',
            'Ganancia Hist': 'G.Hist',
            'Ganancia Día 1': 'D1 (%)',
            'Ganancia Día 2': 'D2 (%)',
            'Éxito D2': 'Éxito D2'
        })
        
        def colorear(row):
            if '🎯' in str(row['Señal']):
                return ['background-color: #d4edda'] * len(row)
            elif '🟡' in str(row['Señal']):
                return ['background-color: #fff3cd'] * len(row)
            return ['background-color: #f8d7da'] * len(row)
        
        def colorear_ghist(val):
            if 'Sin datos' not in str(val):
                return 'background-color: #fffacd; font-weight: bold'
            return ''
        
        st.dataframe(
            df_mobile.style.apply(colorear, axis=1).applymap(colorear_ghist, subset=['G.Hist']),
            use_container_width=True, 
            hide_index=True,
            height=500
        )
        
        col_stat1, col_stat2, col_stat3, col_stat4, col_stat5 = st.columns(5)
        with col_stat1:
            st.metric("Señales Detectadas", len(resultados))
        with col_stat2:
            trades_si = len([r for r in resultados if r['Trade'] == 'SI'])
            st.metric("Señales de TRADE", trades_si)
        with col_stat3:
            exitos_d1 = len([r for r in resultados if r['Éxito D1'] == '✅'])
            tasa_exito_d1 = (exitos_d1 / len(resultados) * 100) if len(resultados) > 0 else 0
            st.metric("Éxito Día 1", f"{tasa_exito_d1:.0f}%")
        with col_stat4:
            exitos_d2 = len([r for r in resultados if r['Éxito D2'] == '✅'])
            con_datos_d2 = len([r for r in resultados if r['Éxito D2'] != '⚪'])
            if con_datos_d2 > 0:
                tasa_exito_d2 = (exitos_d2 / con_datos_d2 * 100)
            else:
                tasa_exito_d2 = 0
            st.metric("Éxito Día 2", f"{tasa_exito_d2:.0f}%")
        with col_stat5:
            prob_promedio = sum([r['Probabilidad'] for r in resultados]) / len(resultados)
            st.metric("Prob. Promedio", f"{prob_promedio:.1f}%")
    else:
        st.info("ℹ️ No se detectaron señales para la fecha seleccionada")

if __name__ == "__main__":
    main()