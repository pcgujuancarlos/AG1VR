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
        try:
            password_correcto = st.secrets["password"]
        except:
            password_correcto = "Tomato4545@@"
        
        if st.session_state["password"] == password_correcto:
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

st.set_page_config(page_title="AG1VR", page_icon="🎯", layout="wide")

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
        """Agrega un resultado histórico verificando que sea una vela roja válida"""
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
    
    def calcular_ganancia_historica(self, ticker, rsi, bb_position, fecha_excluir=None, usar_mediana=False):
        """Calcula ganancia histórica promedio de días similares"""
        dias_similares = []
        dias_similares_detalle = []  # Para mostrar en modal
        
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
                        dias_similares_detalle.append(resultado)
                        print(f"   ✅ {resultado['fecha']}: RSI={rsi_hist:.1f}, BB={bb_hist:.2f} → D1={ganancia:.1f}%")
        
        if len(dias_similares) == 0:
            print(f"   ❌ No se encontraron días similares")
            return None, 0, []
        
        if usar_mediana:
            ganancia_hist = np.median(dias_similares)
        else:
            ganancia_hist = np.mean(dias_similares)
        
        print(f"   📊 Ganancias encontradas: {dias_similares}")
        print(f"   📈 {'Mediana' if usar_mediana else 'Promedio'}: {ganancia_hist:.0f}%")
        print(f"   📌 Total días similares: {len(dias_similares)}")
        
        return ganancia_hist, len(dias_similares), dias_similares_detalle
    
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
    """Calcula la fecha de vencimiento correcta para el ticker"""
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
    """Busca contratos PUT disponibles en Polygon con búsqueda agresiva"""
    try:
        fecha_venc_str = fecha_vencimiento.strftime('%Y-%m-%d')
        import requests
        url = f"https://api.polygon.io/v3/reference/options/contracts"
        
        # INTENTO 1: Buscar en la fecha exacta
        params = {
            'underlying_ticker': ticker,
            'contract_type': 'put',
            'expiration_date': fecha_venc_str,
            'limit': 1000,
            'apiKey': API_KEY
        }
        
        response = requests.get(url, params=params)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ERROR HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return []
        
        if response.status_code == 200:
            data = response.json()
            print(f"📦 Response keys: {data.keys() if data else 'empty'}")
            
            if 'status' in data:
                print(f"📌 Status: {data['status']}")
            
            if 'message' in data:
                print(f"📌 Message: {data['message']}")
            
            if 'results' in data and len(data['results']) > 0:
                print(f"✅ Encontrados {len(data['results'])} contratos para {fecha_venc_str}")
                return data['results']
            else:
                print(f"⚠️  Response tiene 'results' pero vacío o no existe")
                print(f"⚠️  Contenido completo: {data}")
        
        print(f"⚠️  No hay contratos para {fecha_venc_str}")
        
        # INTENTO 2: Buscar en rango ±7 días (más agresivo)
        fecha_desde = (fecha_vencimiento - timedelta(days=7)).strftime('%Y-%m-%d')
        fecha_hasta = (fecha_vencimiento + timedelta(days=7)).strftime('%Y-%m-%d')
        
        print(f"🔄 Buscando en rango: {fecha_desde} a {fecha_hasta}")
        
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
                print(f"✅ Encontrados {len(data['results'])} contratos en rango ±7 días")
                return data['results']
        
        # INTENTO 3: Buscar en rango ±30 días (muy agresivo - último recurso)
        fecha_desde = (fecha_vencimiento - timedelta(days=30)).strftime('%Y-%m-%d')
        fecha_hasta = (fecha_vencimiento + timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"🔄 Último intento - buscando en rango: {fecha_desde} a {fecha_hasta}")
        
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
                print(f"⚠️  Encontrados {len(data['results'])} contratos en rango ±30 días (lejos del objetivo)")
                return data['results']
        
        print(f"❌ NO SE ENCONTRARON CONTRATOS para {ticker} en ningún rango")
        return []
        
    except Exception as e:
        print(f"❌ ERROR buscando contratos: {str(e)}")
        return []

def calcular_ganancia_real_opcion(client, ticker, fecha, precio_stock):
    """Calcula la ganancia real de la opción PUT para Día 1 y Día 2"""
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
        
        # CORRECTO: Calcular día siguiente saltando fines de semana
        fecha_dia_siguiente = fecha + timedelta(days=1)
        while fecha_dia_siguiente.weekday() >= 5:  # 5 = sábado, 6 = domingo
            fecha_dia_siguiente += timedelta(days=1)
        fecha_dia_siguiente_str = fecha_dia_siguiente.strftime('%Y-%m-%d')
        
        print(f"\n=== BUSCANDO OPCIÓN PARA {ticker} ===")
        print(f"Fecha análisis: {fecha_str}")
        print(f"Fecha día siguiente (hábil): {fecha_dia_siguiente_str}")
        print(f"Precio stock: ${precio_stock:.2f}")
        print(f"Strike objetivo (3% OTM): ${strike_objetivo:.2f}")
        
        contratos = buscar_contratos_disponibles(client, ticker, fecha_vencimiento)
        
        if not contratos:
            print(f"❌ No hay contratos disponibles")
            return {
                'ganancia_pct': 0,
                'ganancia_dia_siguiente': 0,
                'exito': '❌',
                'exito_dia2': '❌',
                'strike': strike_objetivo,
                'prima_entrada': 0,
                'prima_maxima': 0,
                'prima_maxima_dia2': 0,
                'mensaje': 'Sin contratos'
            }
        
        strikes_disponibles = sorted([c['strike_price'] for c in contratos])
        print(f"Strikes disponibles: {strikes_disponibles[:10]}...")
        
        mejor_contrato = None
        diferencia_minima = float('inf')
        
        for contrato in contratos:
            strike = contrato['strike_price']
            diferencia = abs(strike - strike_objetivo)
            
            if diferencia < diferencia_minima:
                diferencia_minima = diferencia
                mejor_contrato = contrato
                
                if diferencia < strike_objetivo * 0.05:
                    break
        
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
            
            # ✅ CORRECCIÓN CRÍTICA: Buscar prima EN TODOS LOS PRECIOS DEL DÍA
            prima_entrada = None
            prima_maxima_dia1 = max([p['high'] for p in precios_dia1])
            
            print(f"Rango objetivo: ${rango['min']:.2f} - ${rango['max']:.2f}")
            print(f"Prima apertura (primera vela): ${precios_dia1[0]['open']:.2f}")
            
            # 1. Buscar la PRIMERA prima que esté dentro del rango en CUALQUIER momento
            print("🔍 Buscando prima dentro del rango en TODOS los precios...")
            
            prima_encontrada = False
            for i, p in enumerate(precios_dia1):
                # Revisar TODOS los precios de la vela (open, high, low, close)
                precios_vela = [p['open'], p['high'], p['low'], p['close']]
                
                for precio in precios_vela:
                    if rango['min'] <= precio <= rango['max']:
                        prima_entrada = precio
                        prima_encontrada = True
                        print(f"✅ Prima EN RANGO encontrada en vela {i}: ${prima_entrada:.2f}")
                        break
                
                if prima_encontrada:
                    break
            
            # 2. Si NO encontró prima en rango, buscar la MÁS CERCANA
            if not prima_encontrada:
                print("⚠️  No hay primas en rango exacto - buscando la más cercana...")
                
                # Recolectar TODOS los precios del día (open, high, low, close de todas las velas)
                todos_los_precios = []
                for p in precios_dia1:
                    todos_los_precios.extend([p['open'], p['high'], p['low'], p['close']])
                
                rango_medio = (rango['min'] + rango['max']) / 2
                
                # Encontrar la prima más cercana al centro del rango
                prima_mas_cercana = min(todos_los_precios, key=lambda x: abs(x - rango_medio))
                
                # CRÍTICO: Solo aceptar si está dentro del 150% del ancho del rango
                diferencia_permitida = (rango['max'] - rango['min']) * 1.5
                
                if abs(prima_mas_cercana - rango_medio) <= diferencia_permitida:
                    prima_entrada = prima_mas_cercana
                    print(f"✅ Prima MÁS CERCANA aceptada: ${prima_entrada:.2f} (diferencia: ${abs(prima_entrada - rango_medio):.2f})")
                else:
                    print(f"❌ Prima más cercana (${prima_mas_cercana:.2f}) está DEMASIADO LEJOS del rango - rechazada")
                    return {
                        'ganancia_pct': 0,
                        'ganancia_dia_siguiente': 0,
                        'exito': '❌',
                        'exito_dia2': '❌',
                        'strike': strike_real,
                        'prima_entrada': 0,
                        'prima_maxima': 0,
                        'prima_maxima_dia2': 0,
                        'mensaje': f'Prima fuera de rango: ${prima_mas_cercana:.2f} (esperado: ${rango["min"]:.2f}-${rango["max"]:.2f})'
                    }
            
            if prima_entrada is None or prima_entrada == 0:
                print("❌ No se pudo determinar prima de entrada válida")
                return {
                    'ganancia_pct': 0,
                    'ganancia_dia_siguiente': 0,
                    'exito': '❌',
                    'exito_dia2': '❌',
                    'strike': strike_real,
                    'prima_entrada': 0,
                    'prima_maxima': 0,
                    'prima_maxima_dia2': 0,
                    'mensaje': 'No se encontró prima válida'
                }
            
            print(f"\n📊 CÁLCULO DÍA 1:")
            print(f"  Prima entrada: ${prima_entrada:.2f}")
            print(f"  Prima máxima día 1: ${prima_maxima_dia1:.2f}")
            
            if prima_entrada > 0:
                ganancia_dia1 = ((prima_maxima_dia1 - prima_entrada) / prima_entrada) * 100
            else:
                ganancia_dia1 = 0
            
            exito_dia1 = '✅' if ganancia_dia1 >= 100 else '❌'
            
            print(f"  Ganancia día 1: {ganancia_dia1:.1f}% {exito_dia1}")
            
            # CÁLCULO DÍA 2
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
                'mensaje': f'Error: {str(e)}'
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

def obtener_datos_historicos(ticker, fecha, client):
    """Obtiene datos históricos de una fecha específica"""
    try:
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        aggs = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=fecha_str,
            to=fecha_str
        )
        
        if aggs and len(aggs) > 0:
            return aggs[0]
        return None
    except Exception as e:
        print(f"Error obteniendo datos de {ticker}: {str(e)}")
        return None

def calcular_rsi(precios, periodo=14):
    """Calcula RSI"""
    if len(precios) < periodo + 1:
        return None
    
    deltas = np.diff(precios)
    ganancias = np.where(deltas > 0, deltas, 0)
    perdidas = np.where(deltas < 0, -deltas, 0)
    
    ganancia_promedio = np.mean(ganancias[-periodo:])
    perdida_promedio = np.mean(perdidas[-periodo:])
    
    if perdida_promedio == 0:
        return 100
    
    rs = ganancia_promedio / perdida_promedio
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calcular_bollinger_bands(precios, periodo=20, desviaciones=2):
    """Calcula Bollinger Bands"""
    if len(precios) < periodo:
        return None, None, None
    
    sma = np.mean(precios[-periodo:])
    std = np.std(precios[-periodo:])
    
    banda_superior = sma + (desviaciones * std)
    banda_inferior = sma - (desviaciones * std)
    
    return banda_superior, sma, banda_inferior

def es_vela_roja(data):
    """Verifica si es una vela roja (cierre < apertura)"""
    return data.close < data.open

def analizar_ticker(ticker, fecha, client):
    """Analiza un ticker específico en una fecha"""
    try:
        fecha_str = fecha.strftime('%Y-%m-%d')
        fecha_inicio = (fecha - timedelta(days=50)).strftime('%Y-%m-%d')
        
        # Obtener datos históricos (últimos 50 días)
        aggs = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=fecha_inicio,
            to=fecha_str,
            limit=50
        )
        
        if not aggs or len(aggs) < 20:
            return None
        
        # Obtener precios de cierre
        precios = [agg.close for agg in aggs]
        data_dia = aggs[-1]
        
        # Verificar que sea vela roja
        if not es_vela_roja(data_dia):
            return None
        
        # Calcular RSI
        rsi = calcular_rsi(precios)
        if rsi is None or rsi < 30:
            return None
        
        # Calcular Bollinger Bands
        bb_sup, bb_med, bb_inf = calcular_bollinger_bands(precios)
        if bb_sup is None:
            return None
        
        precio_actual = data_dia.close
        bb_position = (precio_actual - bb_inf) / (bb_sup - bb_inf) if (bb_sup - bb_inf) > 0 else 0
        
        # Filtro: BB position > 0.7
        if bb_position < 0.7:
            return None
        
        return {
            'ticker': ticker,
            'rsi': rsi,
            'bb_position': bb_position,
            'precio': precio_actual,
            'fecha': fecha_str
        }
        
    except Exception as e:
        print(f"Error analizando {ticker}: {str(e)}")
        return None

def main():
    st.title("🎯 AG1VR - Sistema de Trading con Opciones PUT")
    
    if not API_KEY:
        st.error("⚠️ No se encontró POLYGON_API_KEY. Verifica tu archivo .env")
        st.stop()
    
    try:
        client = RESTClient(API_KEY)
    except Exception as e:
        st.error(f"❌ Error conectando con Polygon: {str(e)}")
        st.stop()
    
    # Crear objeto de análisis histórico
    analisis = AnalisisHistorico()
    
    # Lista de tickers a analizar
    tickers = [
        'SPY', 'QQQ', 'AAPL', 'AMD', 'AMZN', 'META', 'MSFT', 'GOOGL', 'NVDA',
        'TSLA', 'NFLX', 'MRNA', 'BAC', 'SLV', 'USO', 'GLD', 'TNA', 'XOM',
        'CVX', 'PLTR', 'BABA', 'CMG', 'SMCI', 'AVGO', 'CORZ', 'BBAI', 'SOUN',
        'LAC', 'RKLB', 'POWI', 'CRWD', 'IREN', 'TIGO', 'RR'
    ]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📅 Seleccionar Fecha de Análisis")
        
        # Fecha por defecto: viernes 17 de octubre de 2025
        fecha_default = datetime(2025, 10, 17)
        
        fecha_seleccionada = st.date_input(
            "Fecha de análisis:",
            value=fecha_default,
            min_value=datetime(2020, 1, 1),
            max_value=datetime.now()
        )
        
        fecha_analisis = datetime.combine(fecha_seleccionada, datetime.min.time())
        
        if st.button("🔍 Analizar Fecha", type="primary"):
            st.info(f"📊 Analizando {len(tickers)} tickers para {fecha_analisis.strftime('%Y-%m-%d')}...")
            
            progress_bar = st.progress(0)
            resultados = []
            dias_similares_map = {}  # Para guardar días similares de cada ticker
            
            for idx, ticker in enumerate(tickers):
                progress_bar.progress((idx + 1) / len(tickers))
                
                senal = analizar_ticker(ticker, fecha_analisis, client)
                
                if senal:
                    st.write(f"✅ {ticker}: RSI={senal['rsi']:.1f}, BB={senal['bb_position']:.2f}")
                    
                    # Calcular ganancia real de la opción
                    ganancia_opcion = calcular_ganancia_real_opcion(
                        client, 
                        ticker, 
                        fecha_analisis, 
                        senal['precio']
                    )
                    
                    # Calcular probabilidad histórica (excluir fecha actual)
                    prob_hist, dias_hist, dias_similares_detalle = analisis.calcular_ganancia_historica(
                        ticker,
                        senal['rsi'],
                        senal['bb_position'],
                        fecha_excluir=fecha_analisis.strftime('%Y-%m-%d'),
                        usar_mediana=False
                    )
                    
                    # Guardar días similares para el modal
                    dias_similares_map[ticker] = dias_similares_detalle
                    
                    # Guardar resultado histórico
                    analisis.agregar_resultado(
                        fecha=fecha_analisis.strftime('%Y-%m-%d'),
                        ticker=ticker,
                        rsi=senal['rsi'],
                        bb_position=senal['bb_position'],
                        ganancia_d1=ganancia_opcion['ganancia_pct'],
                        ganancia_d2=ganancia_opcion['ganancia_dia_siguiente'],
                        prima_entrada=ganancia_opcion['prima_entrada'],
                        prima_max_d1=ganancia_opcion['prima_maxima'],
                        prima_max_d2=ganancia_opcion['prima_maxima_dia2'],
                        strike=ganancia_opcion['strike']
                    )
                    
                    resultado = {
                        'Activo': ticker,
                        'RSI': int(senal['rsi']),
                        'BB Pos': round(senal['bb_position'], 2),
                        'Precio': f"${senal['precio']:.2f}",
                        'Strike': f"${ganancia_opcion['strike']:.0f}",
                        'Prima': f"${ganancia_opcion['prima_entrada']:.2f}",
                        'Ganancia D1': f"{int(ganancia_opcion['ganancia_pct'])}%",
                        'Ganancia D2': f"{int(ganancia_opcion['ganancia_dia_siguiente'])}%" if ganancia_opcion['exito_dia2'] != '⚪' else 'N/A',
                        'Ganancia Hist': f"{int(prob_hist)}% ({dias_hist}d)" if prob_hist else "Sin datos",
                        'Éxito D1': ganancia_opcion['exito'],
                        'Éxito D2': ganancia_opcion['exito_dia2'],
                        'Trade': 'SI' if ganancia_opcion['ganancia_pct'] >= 100 else 'NO',
                        'Probabilidad': prob_hist if prob_hist else 0,
                        'Dias Similares': dias_hist
                    }
                    
                    resultados.append(resultado)
            
            progress_bar.empty()
            
            # Mostrar resultados
            if resultados:
                st.success(f"✅ Análisis completado - {len(resultados)} señales detectadas")
                
                # Ordenar por probabilidad histórica descendente
                resultados_ordenados = sorted(resultados, key=lambda x: x['Probabilidad'], reverse=True)
                
                # Crear DataFrame
                df_resultados = pd.DataFrame(resultados_ordenados)
                
                # Función para colorear filas según ganancia histórica
                def highlight_ganancia_hist(row):
                    if 'Sin datos' in str(row['Ganancia Hist']):
                        return ['background-color: #f0f0f0'] * len(row)
                    else:
                        try:
                            ganancia = int(row['Ganancia Hist'].split('%')[0])
                            if ganancia >= 100:
                                return ['background-color: #90EE90'] * len(row)  # Verde claro
                            else:
                                return ['background-color: #FFB6C1'] * len(row)  # Rosa claro
                        except:
                            return [''] * len(row)
                
                st.dataframe(
                    df_resultados.style.apply(highlight_ganancia_hist, axis=1),
                    use_container_width=True, 
                    hide_index=True
                )
                
                # ==========================================
                # NUEVO: MODAL MEJORADO PARA DÍAS SIMILARES
                # ==========================================
                
                st.markdown("---")
                st.subheader("🔍 Ver Días Similares - Click en un ticker")
                
                # Crear botones en columnas (5 por fila)
                tickers_resultados = [r['Activo'] for r in resultados]
                
                # Organizar en filas de 5 botones
                for i in range(0, len(tickers_resultados), 5):
                    cols = st.columns(5)
                    for j, ticker in enumerate(tickers_resultados[i:i+5]):
                        with cols[j]:
                            # Obtener ganancia histórica para colorear botón
                            resultado_ticker = next(r for r in resultados if r['Activo'] == ticker)
                            ganancia_hist_str = resultado_ticker['Ganancia Hist']
                            
                            # Color según si tiene datos o no
                            if "Sin datos" in ganancia_hist_str:
                                button_type = "secondary"
                                emoji = "⚪"
                            else:
                                button_type = "primary"
                                emoji = "📊"
                            
                            if st.button(f"{emoji} {ticker}", key=f"modal_{ticker}", type=button_type, use_container_width=True):
                                # Guardar en session_state para mostrar modal
                                st.session_state.modal_ticker = ticker
                                st.session_state.modal_open = True
                
                # Mostrar modal si está activo
                if st.session_state.get('modal_open', False):
                    ticker_modal = st.session_state.get('modal_ticker')
                    
                    if ticker_modal:
                        # Encontrar el resultado del ticker
                        resultado_ticker = next((r for r in resultados if r['Activo'] == ticker_modal), None)
                        
                        if resultado_ticker:
                            # Crear contenedor con fondo destacado
                            with st.container():
                                st.markdown("""
                                <style>
                                .modal-container {
                                    background-color: #f0f2f6;
                                    padding: 20px;
                                    border-radius: 10px;
                                    border: 2px solid #4CAF50;
                                    margin: 10px 0;
                                }
                                </style>
                                """, unsafe_allow_html=True)
                                
                                # Header con botón cerrar
                                col_title, col_close = st.columns([6, 1])
                                with col_title:
                                    st.markdown(f"### 📊 Días Similares: **{ticker_modal}**")
                                with col_close:
                                    if st.button("❌ Cerrar", key="close_modal", type="secondary"):
                                        st.session_state.modal_open = False
                                        st.rerun()
                                
                                st.markdown("---")
                                
                                # Obtener días similares del mapa
                                dias_similares_detalle = dias_similares_map.get(ticker_modal, [])
                                
                                if dias_similares_detalle:
                                    st.success(f"✅ Se encontraron **{len(dias_similares_detalle)} días similares**")
                                    
                                    # Crear tabla de días similares
                                    dias_similares_data = []
                                    for hist_result in dias_similares_detalle:
                                        dias_similares_data.append({
                                            'Fecha': hist_result['fecha'],
                                            'RSI': f"{int(hist_result['rsi'])}",
                                            'BB Pos': f"{hist_result['bb_position']:.2f}",
                                            'Ganancia D1': f"{int(hist_result['ganancia_d1'])}%",
                                            'Ganancia D2': f"{int(hist_result['ganancia_d2'])}%",
                                            'Strike': f"${hist_result['strike']:.0f}",
                                            'Prima Entrada': f"${hist_result['prima_entrada']:.2f}"
                                        })
                                    
                                    df_similares = pd.DataFrame(dias_similares_data)
                                    df_similares = df_similares.sort_values('Ganancia D1', ascending=False)
                                    
                                    st.dataframe(
                                        df_similares,
                                        use_container_width=True,
                                        hide_index=True,
                                        height=400
                                    )
                                    
                                    # Estadísticas
                                    ganancias_d1 = [int(d['Ganancia D1'].replace('%', '')) for d in dias_similares_data]
                                    promedio = sum(ganancias_d1) / len(ganancias_d1)
                                    mediana = sorted(ganancias_d1)[len(ganancias_d1)//2]
                                    
                                    st.info("ℹ️ El sistema usa **PROMEDIO** (no mediana) para Ganancia Histórica")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("✅ Promedio D1", f"{int(promedio)}%")
                                    with col2:
                                        st.metric("Mediana D1", f"{int(mediana)}%")
                                    with col3:
                                        exitos = len([g for g in ganancias_d1 if g >= 100])
                                        tasa = (exitos / len(ganancias_d1)) * 100
                                        st.metric("Tasa Éxito", f"{int(tasa)}%")
                                else:
                                    st.warning(f"⚠️ No se encontraron días similares para {ticker_modal}")
                                    st.info("💡 Esto puede ocurrir porque no hay suficientes datos históricos con condiciones similares (RSI y BB Position)")
                
                st.markdown("---")
                
                # Estadísticas generales
                col_stat1, col_stat2, col_stat3, col_stat4, col_stat5 = st.columns(5)
                with col_stat1:
                    st.metric("Señales Detectadas", len(resultados))
                with col_stat2:
                    trades_si = len([r for r in resultados if r['Trade'] == 'SI'])
                    st.metric("Señales de TRADE", trades_si)
                with col_stat3:
                    exitos_d1 = len([r for r in resultados if r['Éxito D1'] == '✅'])
                    tasa_exito_d1 = (exitos_d1 / len(resultados) * 100) if len(resultados) > 0 else 0
                    st.metric("Éxito Día 1", f"{int(tasa_exito_d1)}%")
                with col_stat4:
                    exitos_d2 = len([r for r in resultados if r['Éxito D2'] == '✅'])
                    con_datos_d2 = len([r for r in resultados if r['Éxito D2'] != '⚪'])
                    if con_datos_d2 > 0:
                        tasa_exito_d2 = (exitos_d2 / con_datos_d2 * 100)
                    else:
                        tasa_exito_d2 = 0
                    st.metric("Éxito Día 2", f"{int(tasa_exito_d2)}%")
                with col_stat5:
                    prob_promedio = sum([r['Probabilidad'] for r in resultados]) / len(resultados)
                    st.metric("Prob. Promedio", f"{prob_promedio:.1f}%")
            else:
                st.info("ℹ️ No se detectaron señales para la fecha seleccionada")
    
    with col2:
        st.subheader("💾 Registrar Trade Manual")
        
        with st.form("registro_trade"):
            ticker_reg = st.selectbox("Activo", tickers)
            rsi_reg = st.number_input("RSI", min_value=0.0, max_value=100.0, value=70.0)
            bb_reg = st.number_input("BB Position", min_value=0.0, max_value=1.0, value=0.8)
            resultado_reg = st.number_input("Resultado (%)", value=0.0)
            
            if st.form_submit_button("💾 Guardar Resultado"):
                analisis.agregar_operacion(ticker_reg, rsi_reg, bb_reg, resultado_reg, datetime.now().isoformat())
                st.success("✅ Resultado guardado")

if __name__ == "__main__":
    main()