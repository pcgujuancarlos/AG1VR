import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys
import time
from dotenv import load_dotenv

# Importar funciones requeridas por Alberto
try:
    from funciones_alberto import (
        calc_bins, get_cohort, calc_mfe, 
        percentil_10, hist_90_display, normalizar_columnas
    )
except ImportError:
    print("⚠️ funciones_alberto.py no encontrado - usando funciones legacy")

# Cargar variables de entorno
load_dotenv()

# AUTENTICACIÓN CON PASSWORD
def check_password():
    def password_entered():
        try:
            password_correcto = st.secrets["password"]
        except:
            password_correcto = "Tomato4545@@"
        
        # Verificar que la clave existe antes de acceder
        if "password" in st.session_state and st.session_state["password"] == password_correcto:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Inicializar session state si es necesario
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state.get("password_correct", False):
        st.text_input("🔐 Password", type="password", on_change=password_entered, key="password")
        if st.session_state.get("password_correct", False):
            st.rerun()
        else:
            if "password" in st.session_state and st.session_state["password"]:
                st.error("😕 Password incorrecto")
            else:
                st.info("Introduce el password para acceder")
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
                # Limpiar datos corruptos
                resultados_limpios = []
                for r in self.resultados_historicos:
                    if isinstance(r, dict):
                        resultados_limpios.append(r)
                self.resultados_historicos = resultados_limpios
        except FileNotFoundError:
            self.resultados_historicos = []
        except json.JSONDecodeError as e:
            print(f"❌ Error cargando JSON: {e}")
            print("🔄 Iniciando con base de datos vacía")
            self.resultados_historicos = []
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            self.resultados_historicos = []
    
    def guardar_resultados_historicos(self):
        # Convertir valores para asegurar compatibilidad JSON
        resultados_limpios = []
        for r in self.resultados_historicos:
            resultado_limpio = {}
            for k, v in r.items():
                if isinstance(v, bool):
                    # Mantener booleanos como booleanos (JSON los soporta)
                    resultado_limpio[k] = v
                elif isinstance(v, (int, float)):
                    # Manejar NaN y infinitos
                    if pd.isna(v) or np.isinf(v):
                        resultado_limpio[k] = 0
                    else:
                        resultado_limpio[k] = v
                elif v is None:
                    resultado_limpio[k] = 0
                else:
                    resultado_limpio[k] = str(v)  # Convertir otros tipos a string
            resultados_limpios.append(resultado_limpio)
        
        try:
            with open(self.resultados_file, 'w') as f:
                json.dump(resultados_limpios, f, indent=2)
        except Exception as e:
            print(f"❌ Error guardando JSON: {e}")
            # Intentar guardar versión simplificada
            try:
                resultados_seguros = []
                for r in resultados_limpios:
                    resultado_seguro = {}
                    for k, v in r.items():
                        try:
                            json.dumps(v)  # Verificar que sea serializable
                            resultado_seguro[k] = v
                        except:
                            resultado_seguro[k] = str(v)
                    resultados_seguros.append(resultado_seguro)
                
                with open(self.resultados_file, 'w') as f:
                    json.dump(resultados_seguros, f, indent=2)
                print("✅ Guardado con conversión de seguridad")
            except Exception as e2:
                print(f"❌ Error crítico: {e2}")
    
    def agregar_resultado(self, fecha, ticker, rsi, bb_position, ganancia_d1, ganancia_d2, prima_entrada, prima_max_d1, prima_max_d2, strike):
        """Agrega un resultado histórico verificando que sea válido"""
        
        # VALIDACIONES CRÍTICAS
        # 1. Validar que la prima esté en el rango configurado
        if ticker in RANGOS_PRIMA:
            rango = RANGOS_PRIMA[ticker]
            if prima_entrada < rango['min'] * 0.8 or prima_entrada > rango['max'] * 1.5:
                print(f"⚠️ Prima fuera de rango para {ticker}: ${prima_entrada:.2f} (rango: ${rango['min']:.2f}-${rango['max']:.2f})")
                return  # NO guardar si está fuera de rango
        
        # 2. Validar ganancias realistas (máximo 400%)
        if ganancia_d1 > 400 or ganancia_d2 > 400:
            print(f"⚠️ Ganancia irreal detectada para {ticker}: D1={ganancia_d1}%, D2={ganancia_d2}%")
            return  # NO guardar ganancias irreales
        
        # 3. Validar que no sea duplicado
        for r in self.resultados_historicos[-10:]:  # Revisar últimos 10
            if (r.get('ticker') == str(ticker) and 
                r.get('fecha') == str(fecha) and
                abs(float(r.get('rsi', 0)) - float(rsi)) < 1):
                print(f"⚠️ Registro duplicado detectado: {ticker} {fecha}")
                return  # NO guardar duplicados
        
        # Convertir valores a tipos seguros para JSON
        resultado = {
            'fecha': str(fecha),
            'ticker': str(ticker),
            'rsi': float(rsi) if not pd.isna(rsi) else 0.0,
            'bb_position': float(bb_position) if not pd.isna(bb_position) else 0.0,
            'ganancia_d1': float(ganancia_d1) if not pd.isna(ganancia_d1) else 0.0,
            'ganancia_d2': float(ganancia_d2) if not pd.isna(ganancia_d2) else 0.0,
            'prima_entrada': float(prima_entrada) if not pd.isna(prima_entrada) else 0.0,
            'prima_max_d1': float(prima_max_d1) if not pd.isna(prima_max_d1) else 0.0,
            'prima_max_d2': float(prima_max_d2) if not pd.isna(prima_max_d2) else 0.0,
            'strike': float(strike) if not pd.isna(strike) else 0.0,
            'exitoso_d1': ganancia_d1 >= 100,
            'exitoso_d2': ganancia_d2 >= 100
        }
        self.resultados_historicos.append(resultado)
        self.guardar_resultados_historicos()
    
    def calcular_ganancia_historica(self, ticker, rsi, bb_position, fecha_excluir=None, usar_mediana=False):
        """Calcula ganancia histórica usando las especificaciones de Alberto"""
        
        try:
            # Convertir resultados históricos a DataFrame
            if not self.resultados_historicos:
                return None, 0, []
            
            df_hist = pd.DataFrame(self.resultados_historicos)
            
            # Preparar dataframe actual
            df_current = pd.DataFrame([{
                'ticker': ticker,
                'RSI': rsi,
                'BB Position': bb_position,
                'side': 'PUT'  # Asumimos PUT por defecto
            }])
            
            # Normalizar y calcular bins según Alberto
            df_current = calc_bins(df_current)
            df_hist = calc_bins(df_hist)
            
            # Obtener bins actuales
            current_rsi_bin = df_current['rsi_bin'].iloc[0]
            current_bb_bin = df_current['bb_bin'].iloc[0]
            
            # Filtrar por ticker
            df_hist_ticker = df_hist[df_hist['ticker'] == ticker].copy()
            
            # Excluir fecha si se especifica
            if fecha_excluir:
                df_hist_ticker = df_hist_ticker[df_hist_ticker['fecha'] != fecha_excluir]
            
            # Añadir side si no existe
            if 'side' not in df_hist_ticker.columns:
                df_hist_ticker['side'] = 'PUT'
            
            # Obtener cohorte con las nuevas reglas (n≥3, expansión ±1)
            cohort = get_cohort(
                df_hist_ticker,
                current_rsi_bin,
                current_bb_bin,
                'PUT',
                min_n=3
            )
            
            if cohort.empty:
                print(f"   ❌ No se encontraron días similares para {ticker}")
                return None, 0, []
            
            # Filtrar ganancias irreales
            cohort = cohort[
                (cohort['ganancia_d1'] > 0) & 
                (cohort['ganancia_d1'] <= 400) &
                (cohort['prima_entrada'] > 0.05)
            ]
            
            if cohort.empty:
                return None, 0, []
            
            # Calcular ganancia histórica
            dias_similares = cohort['ganancia_d1'].tolist()
            
            if usar_mediana:
                ganancia_hist = np.median(dias_similares)
            else:
                ganancia_hist = np.mean(dias_similares)
            
            # Convertir cohort a lista de diccionarios para compatibilidad
            dias_similares_detalle = cohort.to_dict('records')
            
            print(f"\n🔍 DÍAS SIMILARES PARA {ticker} (usando bins de Alberto):")
            print(f"   RSI bin: {current_rsi_bin} | BB bin: {current_bb_bin}")
            print(f"   Cohorte encontrada: {len(cohort)} días")
            print(f"   Ganancia histórica: {ganancia_hist:.0f}%")
            
            return ganancia_hist, len(dias_similares), dias_similares_detalle
            
        except Exception as e:
            print(f"❌ Error en calcular_ganancia_historica: {e}")
            # Fallback al método anterior si hay error
            return self._calcular_ganancia_historica_legacy(ticker, rsi, bb_position, fecha_excluir, usar_mediana)
    
    def _calcular_ganancia_historica_legacy(self, ticker, rsi, bb_position, fecha_excluir=None, usar_mediana=False):
        """Método legacy como fallback"""
        dias_similares = []
        dias_similares_detalle = []
        
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
                    prima = resultado.get('prima_entrada', 0)
                    
                    if ganancia > 0 and ganancia <= 400 and prima > 0.05:
                        dias_similares.append(ganancia)
                        dias_similares_detalle.append(resultado)
        
        if len(dias_similares) == 0:
            return None, 0, []
        
        if usar_mediana:
            ganancia_hist = np.median(dias_similares)
        else:
            ganancia_hist = np.mean(dias_similares)
        
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
            # ✅ CORRECCIÓN CRÍTICA: Si HOY es viernes (dias_hasta_viernes=0), 
            # buscar opciones que vencen HOY mismo (0DTE), NO el siguiente viernes
            # Esto es ESENCIAL para opciones de corto plazo que buscan 100%+ en 1 día
            # ANTES: if dias_hasta_viernes == 0: dias_hasta_viernes = 7  ❌
            # AHORA: Mantener dias_hasta_viernes = 0 para buscar opciones 0DTE ✅
        else:
            dias_hasta_viernes = 5 if dia_semana == 5 else 4
        fecha_venc = fecha_senal + timedelta(days=dias_hasta_viernes)
        print(f"   [VENC] {ticker} viernes: {fecha_senal} ({fecha_senal.strftime('%A')}) → {fecha_venc} ({fecha_venc.strftime('%A')}) [+{dias_hasta_viernes}d]")
        return fecha_venc

def buscar_contratos_disponibles(client, ticker, fecha_vencimiento, fecha_analisis=None):
    """Busca contratos PUT disponibles en Polygon con búsqueda agresiva"""
    try:
        import requests
        from datetime import datetime, timedelta
        
        # AJUSTE CLAVE: Para datos históricos de 2024, buscar contratos de 2024
        if fecha_analisis and fecha_analisis.year == 2024:
            print(f"📅 Ajustando búsqueda para datos históricos de {fecha_analisis.year}")
            # Para 2024, necesitamos contratos que vencían en 2024
            fecha_vencimiento = fecha_vencimiento.replace(year=2024)
            
            # Verificar que la fecha sea posterior a la fecha de análisis
            if fecha_vencimiento <= fecha_analisis:
                if ticker in ['SPY', 'QQQ']:
                    fecha_vencimiento = fecha_analisis + timedelta(days=1)
                    while fecha_vencimiento.weekday() >= 5:
                        fecha_vencimiento += timedelta(days=1)
                else:
                    dias_hasta_viernes = (4 - fecha_analisis.weekday()) % 7
                    if dias_hasta_viernes == 0:
                        dias_hasta_viernes = 7
                    fecha_vencimiento = fecha_analisis + timedelta(days=dias_hasta_viernes)
        
        fecha_venc_str = fecha_vencimiento.strftime('%Y-%m-%d')
        print(f"🎯 Buscando contratos PUT con vencimiento: {fecha_venc_str}")
        
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
        
        print(f"❌ NO SE ENCONTRARON CONTRATOS en la API para {ticker}")
        
        # FALLBACK: Para fechas históricas, generar contratos manualmente
        if fecha_analisis and fecha_analisis.year == 2024:
            print(f"\n🔧 Generando contratos manualmente para fecha histórica...")
            
            # Obtener precio del stock para ese día
            try:
                stock_aggs = client.get_aggs(
                    ticker=ticker,
                    multiplier=1,
                    timespan="day",
                    from_=fecha_analisis.strftime('%Y-%m-%d'),
                    to=fecha_analisis.strftime('%Y-%m-%d'),
                    limit=1
                )
                
                if stock_aggs:
                    precio_stock = stock_aggs[0].close
                    print(f"💵 Precio del stock el {fecha_analisis.strftime('%Y-%m-%d')}: ${precio_stock:.2f}")
                    
                    # Generar contratos manualmente
                    contratos_generados = []
                    fecha_str = fecha_vencimiento.strftime('%y%m%d')
                    
                    # Generar strikes desde 15% ITM hasta 5% OTM
                    strike_min = int(precio_stock * 0.85)
                    strike_max = int(precio_stock * 1.05)
                    step = 1 if ticker in ['SPY', 'QQQ'] else 5
                    
                    for strike in range(strike_min, strike_max + 1, step):
                        option_ticker = f"O:{ticker}{fecha_str}P{strike*1000:08d}"
                        
                        contrato = {
                            'ticker': option_ticker,
                            'underlying_ticker': ticker,
                            'contract_type': 'put',
                            'expiration_date': fecha_vencimiento.strftime('%Y-%m-%d'),
                            'strike_price': strike
                        }
                        
                        contratos_generados.append(contrato)
                    
                    print(f"✅ Generados {len(contratos_generados)} contratos manualmente")
                    print(f"📦 Rango de strikes: ${strike_min} - ${strike_max}")
                    return contratos_generados
                    
            except Exception as e:
                print(f"❌ Error generando contratos: {e}")
        
        return []
        
    except Exception as e:
        print(f"❌ ERROR buscando contratos: {str(e)}")
        return []

def calcular_ganancia_real_opcion(client, ticker, fecha, precio_stock):
    """
    NUEVA ESTRATEGIA V3: Buscar el strike que ofrece MAYOR GANANCIA PORCENTUAL
    dentro del rango de primas configurado
    """
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
                'mensaje': 'Sin rango definido'
            }
        
        rango = RANGOS_PRIMA[ticker]
        fecha_vencimiento = calcular_fecha_vencimiento(fecha, ticker)
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        # Calcular día siguiente
        fecha_dia_siguiente = fecha + timedelta(days=1)
        while fecha_dia_siguiente.weekday() >= 5:
            fecha_dia_siguiente += timedelta(days=1)
        fecha_dia_siguiente_str = fecha_dia_siguiente.strftime('%Y-%m-%d')
        
        print(f"\n=== NUEVA ESTRATEGIA: BUSCANDO MAYOR GANANCIA % ===")
        print(f"Ticker: {ticker}")
        print(f"Fecha: {fecha_str}")
        print(f"Precio stock: ${precio_stock:.2f}")
        print(f"Rango prima objetivo: ${rango['min']:.2f} - ${rango['max']:.2f}")
        
        # PASO 1: Determinar estrategia según el año
        if fecha.year >= 2025:
            # Para fechas futuras, intentar API primero
            print(f"📅 Fecha futura detectada ({fecha.year}) - intentando API primero")
            contratos = buscar_contratos_api_v2(client, ticker, fecha_vencimiento)
            
            # Si la API no devuelve contratos, generar manualmente
            if not contratos:
                print(f"⚠️ API no devolvió contratos - generando manualmente")
                contratos = generar_contratos_historicos_v2(ticker, fecha_vencimiento, precio_stock)
        else:
            # Para fechas pasadas, generar contratos manualmente
            print(f"📅 Fecha pasada detectada ({fecha.year}) - generando contratos")
            contratos = generar_contratos_historicos_v2(ticker, fecha_vencimiento, precio_stock)
        
        if not contratos:
            print(f"❌ No hay contratos PUT disponibles")
            return {
                'ganancia_pct': 0,
                'ganancia_dia_siguiente': 0,
                'exito': '❌',
                'exito_dia2': '❌',
                'strike': 0,
                'prima_entrada': 0,
                'prima_maxima': 0,
                'prima_maxima_dia2': 0,
                'mensaje': 'Sin contratos disponibles'
            }
        
        print(f"✅ Encontrados {len(contratos)} contratos PUT para analizar")
        
        # Agrupar por fecha de vencimiento
        from collections import defaultdict
        contratos_por_fecha = defaultdict(list)
        for contrato in contratos:
            exp_date = contrato.get('expiration_date', '')
            contratos_por_fecha[exp_date].append(contrato)
        
        # Seleccionar fecha más cercana
        fechas_disponibles = sorted(contratos_por_fecha.keys())
        fecha_elegida = None
        
        if fecha_vencimiento.strftime('%Y-%m-%d') in fechas_disponibles:
            fecha_elegida = fecha_vencimiento.strftime('%Y-%m-%d')
        elif fechas_disponibles:
            # Buscar la más cercana
            from datetime import datetime
            # Asegurar que fecha_objetivo sea date, no datetime
            if isinstance(fecha_vencimiento, datetime):
                fecha_objetivo = fecha_vencimiento.date()
            else:
                fecha_objetivo = fecha_vencimiento
            
            fecha_elegida = min(fechas_disponibles, 
                key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d').date() - fecha_objetivo).days))
        
        if not fecha_elegida:
            return {
                'ganancia_pct': 0,
                'ganancia_dia_siguiente': 0,
                'exito': '❌',
                'exito_dia2': '❌',
                'strike': 0,
                'prima_entrada': 0,
                'prima_maxima': 0,
                'prima_maxima_dia2': 0,
                'mensaje': 'Sin fechas disponibles'
            }
        
        contratos = contratos_por_fecha[fecha_elegida]
        print(f"📅 Usando contratos del {fecha_elegida} ({len(contratos)} strikes)")
        
        print(f"\n📊 Analizando {len(contratos)} contratos...")
        
        # ANALIZAR TODOS LOS CONTRATOS Y CALCULAR GANANCIAS
        candidatos = []
        contratos_analizados = 0
        
        for contrato in contratos:
            option_ticker = contrato['ticker']
            strike = contrato['strike_price']
            
            # Filtrar strikes razonables
            distancia_pct = ((strike - precio_stock) / precio_stock) * 100
            if distancia_pct < -15 or distancia_pct > 5:
                continue
                
            contratos_analizados += 1
            if contratos_analizados > 50:  # Límite para no demorar mucho
                break
            
            try:
                # Obtener datos del día
                multiplier = 1 if fecha.year < 2025 else 5
                
                option_aggs = client.get_aggs(
                    ticker=option_ticker,
                    multiplier=multiplier,
                    timespan="minute",
                    from_=fecha_str,
                    to=fecha_str,
                    limit=500
                )
                
                if option_aggs and len(option_aggs) > 0:
                    # Analizar todos los precios del día
                    todos_precios = []
                    for agg in option_aggs:
                        todos_precios.extend([agg.open, agg.high, agg.low, agg.close])
                    
                    min_precio = min(todos_precios)
                    max_precio = max(todos_precios)
                    
                    # Buscar primas en el rango objetivo
                    primas_en_rango = [p for p in todos_precios if rango['min'] <= p <= rango['max']]
                    
                    if primas_en_rango:
                        # Para cada prima en rango, calcular ganancia potencial
                        for prima_entrada in primas_en_rango[:3]:  # Máximo 3 por strike
                            # Validar prima mínima
                            if prima_entrada < 0.05:
                                continue
                                
                            # Calcular ganancia máxima posible
                            ganancia_maxima_pct = ((max_precio - prima_entrada) / prima_entrada * 100)
                            
                            # Filtrar ganancias irreales
                            if ganancia_maxima_pct > 500:  # Más de 500% es muy sospechoso
                                continue
                            
                            candidatos.append({
                                'contrato': contrato,
                                'prima_entrada': prima_entrada,
                                'prima_maxima': max_precio,
                                'ganancia_pct': ganancia_maxima_pct,
                                'min_precio_dia': min_precio,
                                'distancia_otm': distancia_pct
                            })
                            
                            if len(candidatos) % 5 == 0:
                                print(f"   Analizados {len(candidatos)} candidatos...")
                    
                    # También considerar el más cercano si no hay en rango exacto
                    elif len(candidatos) < 5:  # Solo si tenemos pocos candidatos
                        # Buscar el precio más cercano al rango
                        rango_medio = (rango['min'] + rango['max']) / 2
                        precio_mas_cercano = min(todos_precios, key=lambda x: abs(x - rango_medio))
                        
                        # Solo considerar si está razonablemente cerca
                        if abs(precio_mas_cercano - rango_medio) <= rango_medio * 0.5:
                            ganancia_pct = ((max_precio - precio_mas_cercano) / precio_mas_cercano * 100)
                            
                            candidatos.append({
                                'contrato': contrato,
                                'prima_entrada': precio_mas_cercano,
                                'prima_maxima': max_precio,
                                'ganancia_pct': ganancia_pct,
                                'min_precio_dia': min_precio,
                                'distancia_otm': distancia_pct,
                                'fuera_de_rango': True
                            })
                            
            except Exception as e:
                continue
        
        if not candidatos:
            print("❌ No se encontraron candidatos viables")
            return {
                'ganancia_pct': 0,
                'ganancia_dia_siguiente': 0,
                'exito': '❌',
                'exito_dia2': '❌',
                'strike': 0,
                'prima_entrada': 0,
                'prima_maxima': 0,
                'prima_maxima_dia2': 0,
                'mensaje': 'Sin primas en rango'
            }
        
        # SELECCIONAR EL MEJOR: Mayor ganancia % con prima en rango preferentemente
        print(f"\n🎯 Encontrados {len(candidatos)} candidatos")
        
        # Separar en rango vs fuera de rango
        en_rango = [c for c in candidatos if not c.get('fuera_de_rango', False)]
        fuera_rango = [c for c in candidatos if c.get('fuera_de_rango', False)]
        
        # Preferir los que están en rango
        if en_rango:
            # Ordenar por mayor ganancia %
            en_rango.sort(key=lambda x: x['ganancia_pct'], reverse=True)
            mejor = en_rango[0]
            print(f"\n✅ MEJOR OPCIÓN (en rango):")
        else:
            # Si no hay en rango, usar el más cercano con mejor ganancia
            fuera_rango.sort(key=lambda x: x['ganancia_pct'], reverse=True)
            mejor = fuera_rango[0]
            print(f"\n⚠️ MEJOR OPCIÓN (fuera de rango):")
        
        print(f"   Strike: ${mejor['contrato']['strike_price']}")
        print(f"   Prima entrada: ${mejor['prima_entrada']:.2f}")
        print(f"   Prima máxima: ${mejor['prima_maxima']:.2f}")
        print(f"   GANANCIA POTENCIAL: {mejor['ganancia_pct']:.1f}%")
        
        # Mostrar top 3 alternativas
        print(f"\n📋 Otras opciones consideradas:")
        todos_ordenados = sorted(candidatos, key=lambda x: x['ganancia_pct'], reverse=True)
        for i, alt in enumerate(todos_ordenados[1:4]):
            print(f"   {i+2}. Strike ${alt['contrato']['strike_price']}: "
                  f"Prima ${alt['prima_entrada']:.2f} → {alt['ganancia_pct']:.1f}%")
        
        # Obtener datos completos para el mejor
        mejor_contrato = mejor['contrato']
        option_ticker = mejor_contrato['ticker']
        prima_entrada = mejor['prima_entrada']
        strike_real = mejor_contrato['strike_price']
        
        print(f"\n📈 CALCULANDO GANANCIAS para {option_ticker}")
        print(f"   Strike seleccionado: ${strike_real:.2f}")
        print(f"   Prima de entrada: ${prima_entrada:.2f}")
        
        # Obtener prima máxima del día 1
        try:
            # Usar 1 minuto para mejor precisión en datos históricos
            multiplier = 1 if fecha.year < 2025 else 5
            
            option_aggs_dia1 = client.get_aggs(
                ticker=option_ticker,
                multiplier=multiplier,
                timespan="minute",
                from_=fecha_str,
                to=fecha_str,
                limit=50000
            )
            
            if option_aggs_dia1:
                prima_maxima_dia1 = max([agg.high for agg in option_aggs_dia1])
            else:
                prima_maxima_dia1 = prima_entrada
        except:
            prima_maxima_dia1 = prima_entrada
        
        # Calcular ganancia día 1 con validaciones estrictas
        if prima_entrada > 0.05 and prima_entrada < 50:  # Prima mínima $0.05
            # Verificar que la prima máxima sea realista
            if prima_maxima_dia1 / prima_entrada > 5:  # Más de 5x es sospechoso
                print(f"⚠️ Prima máxima sospechosa: ${prima_entrada:.2f} → ${prima_maxima_dia1:.2f}")
                prima_maxima_dia1 = prima_entrada * 3  # Limitar a 3x
            
            ganancia_dia1 = ((prima_maxima_dia1 - prima_entrada) / prima_entrada * 100)
            # Validar que sea realista
            if ganancia_dia1 > 200:  # Reducir límite a 200%
                print(f"⚠️ Ganancia D1 irreal: {ganancia_dia1:.1f}% - limitando a 200%")
                ganancia_dia1 = 200
        else:
            print(f"⚠️ Prima entrada inválida: ${prima_entrada:.2f}")
            ganancia_dia1 = 0
        
        # Día 2
        prima_maxima_dia2 = 0
        ganancia_dia2 = 0
        
        try:
            option_aggs_dia2 = client.get_aggs(
                ticker=option_ticker,
                multiplier=multiplier,
                timespan="minute",
                from_=fecha_dia_siguiente_str,
                to=fecha_dia_siguiente_str,
                limit=50000
            )
            
            if option_aggs_dia2:
                prima_maxima_dia2 = max([agg.high for agg in option_aggs_dia2])
                if prima_entrada > 0.05 and prima_entrada < 50:
                    # Verificar que la prima máxima sea realista
                    if prima_maxima_dia2 / prima_entrada > 5:  # Más de 5x es sospechoso
                        print(f"⚠️ Prima máxima D2 sospechosa: ${prima_entrada:.2f} → ${prima_maxima_dia2:.2f}")
                        prima_maxima_dia2 = prima_entrada * 3  # Limitar a 3x
                    
                    ganancia_dia2 = ((prima_maxima_dia2 - prima_entrada) / prima_entrada * 100)
                    if ganancia_dia2 > 200:  # Reducir límite a 200%
                        print(f"⚠️ Ganancia D2 irreal: {ganancia_dia2:.1f}% - limitando a 200%")
                        ganancia_dia2 = 200
                else:
                    ganancia_dia2 = 0
        except:
            pass
        
        print(f"\n📊 RESULTADOS FINALES:")
        print(f"   Prima entrada: ${prima_entrada:.2f}")
        print(f"   Prima máxima D1: ${prima_maxima_dia1:.2f}")
        print(f"   Ganancia D1: {ganancia_dia1:.1f}%")
        print(f"   Prima máxima D2: ${prima_maxima_dia2:.2f}")
        print(f"   Ganancia D2: {ganancia_dia2:.1f}%")
        
        return {
            'ganancia_pct': round(ganancia_dia1, 1),
            'ganancia_dia_siguiente': round(ganancia_dia2, 1),
            'exito': '✅' if ganancia_dia1 >= 100 else '❌',
            'exito_dia2': '✅' if ganancia_dia2 >= 100 else '❌',
            'strike': strike_real,
            'prima_entrada': round(prima_entrada, 2) if prima_entrada else 0,
            'prima_maxima': round(prima_maxima_dia1, 2),
            'prima_maxima_dia2': round(prima_maxima_dia2, 2),
            'mensaje': f'Strike ${strike_real:.2f} - Mejor ganancia: {ganancia_dia1:.1f}%'
        }
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
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

def buscar_contratos_api_v2(client, ticker, fecha_vencimiento):
    """Busca contratos usando la API (para fechas futuras)"""
    import requests
    from datetime import timedelta
    
    url = "https://api.polygon.io/v3/reference/options/contracts"
    
    # Buscar con rango flexible
    params = {
        'underlying_ticker': ticker,
        'contract_type': 'put',
        'expiration_date.gte': (fecha_vencimiento - timedelta(days=7)).strftime('%Y-%m-%d'),
        'expiration_date.lte': (fecha_vencimiento + timedelta(days=7)).strftime('%Y-%m-%d'),
        'limit': 250,
        'apiKey': API_KEY,
        'order': 'asc',
        'sort': 'strike_price'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            contratos = data.get('results', [])
            if contratos:
                print(f"✅ {len(contratos)} contratos encontrados en API")
                return contratos
    except Exception as e:
        print(f"❌ Error API: {e}")
    
    return []


def generar_contratos_historicos_v2(ticker, fecha_vencimiento, precio_stock):
    """Genera contratos manualmente para fechas históricas"""
    contratos = []
    fecha_str = fecha_vencimiento.strftime('%y%m%d')
    
    # Generar strikes desde 15% ITM hasta 5% OTM
    strike_min = int(precio_stock * 0.85)
    strike_max = int(precio_stock * 1.05)
    
    # Step según ticker
    if ticker in ['SPY', 'QQQ']:
        step = 1
    elif ticker in ['TSLA']:
        step = 5
    else:
        step = 1 if precio_stock < 100 else 5
    
    for strike in range(strike_min, strike_max + 1, step):
        option_ticker = f"O:{ticker}{fecha_str}P{strike*1000:08d}"
        
        contrato = {
            'ticker': option_ticker,
            'underlying_ticker': ticker,
            'contract_type': 'put',
            'expiration_date': fecha_vencimiento.strftime('%Y-%m-%d'),
            'strike_price': strike
        }
        
        contratos.append(contrato)
    
    print(f"✅ {len(contratos)} contratos generados (strikes ${strike_min}-${strike_max})")
    return contratos


def calcular_ganancia_real_opcion_OLD(client, ticker, fecha, precio_stock):
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
        
        print("\n🔍 Buscando contratos disponibles...")
        contratos = buscar_contratos_disponibles(client, ticker, fecha_vencimiento, fecha_analisis=fecha)
        
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
        
        # Mostrar algunos contratos para debugging
        if len(contratos) > 0:
            print(f"📋 Primeros 3 contratos disponibles:")
            for i, c in enumerate(contratos[:3]):
                print(f"   {c['ticker']} - Strike: ${c.get('strike_price')} - Exp: {c.get('expiration_date')}")
        
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
            # ✅ CORRECCIÓN: Usar agregados de 30 MINUTOS (compatible con plan Starter)
            option_aggs_dia1 = client.get_aggs(
                ticker=option_ticker,
                multiplier=30,  # ✅ 30 minutos
                timespan="minute",
                from_=fecha_str,
                to=fecha_str,
                limit=50000
            )
            
            print(f"📊 Día 1: {len(option_aggs_dia1) if option_aggs_dia1 else 0} registros de 30min")
            
            if not option_aggs_dia1 or len(option_aggs_dia1) == 0:
                print(f"❌ NO SE ENCONTRARON DATOS para {option_ticker}")
                print("🔄 Usando estimación basada en volatilidad del subyacente...")
                
                # NUEVA ESTRATEGIA: Estimar primas usando volatilidad del subyacente
                # Compatible con plan Starter que no tiene datos históricos de opciones
                
                # 1. Obtener volatilidad histórica del subyacente
                fecha_30_dias_atras = fecha - timedelta(days=30)
                volatilidad_anual = 0.25  # Por defecto
                
                try:
                    stock_aggs = client.get_aggs(
                        ticker=ticker,
                        multiplier=1,
                        timespan="day", 
                        from_=fecha_30_dias_atras.strftime('%Y-%m-%d'),
                        to=fecha_str,
                        limit=50
                    )
                    
                    if stock_aggs and len(stock_aggs) > 10:
                        precios_cierre = [agg.close for agg in stock_aggs]
                        rendimientos = []
                        for i in range(1, len(precios_cierre)):
                            rendimiento = np.log(precios_cierre[i] / precios_cierre[i-1])
                            rendimientos.append(rendimiento)
                        
                        volatilidad_diaria = np.std(rendimientos)
                        volatilidad_anual = volatilidad_diaria * np.sqrt(252)
                        print(f"📊 Volatilidad anual calculada: {volatilidad_anual:.2%}")
                    else:
                        # Volatilidades por defecto según ticker
                        volatilidades_default = {
                            'SPY': 0.15, 'QQQ': 0.20, 'AAPL': 0.25, 'AMD': 0.40,
                            'AMZN': 0.25, 'META': 0.30, 'MSFT': 0.22, 'NVDA': 0.45,
                            'TSLA': 0.50, 'GLD': 0.12, 'GOOGL': 0.25, 'NFLX': 0.35,
                            'MRNA': 0.60, 'BAC': 0.25, 'SLV': 0.30, 'USO': 0.40,
                            'TNA': 0.45, 'XOM': 0.28, 'CVX': 0.28, 'PLTR': 0.55,
                            'BABA': 0.35, 'CMG': 0.25, 'SMCI': 0.60, 'AVGO': 0.30,
                            'CORZ': 0.70, 'BBAI': 0.65, 'SOUN': 0.60, 'LAC': 0.55,
                            'RKLB': 0.50, 'POWI': 0.35, 'CRWD': 0.40, 'IREN': 0.65,
                            'TIGO': 0.45, 'RR': 0.50
                        }
                        volatilidad_anual = volatilidades_default.get(ticker, 0.30)
                        print(f"⚠️ Usando volatilidad por defecto: {volatilidad_anual:.2%}")
                except:
                    pass
                
                # 2. Calcular tiempo hasta vencimiento
                dias_hasta_vencimiento = (fecha_vencimiento - fecha).days
                tiempo_hasta_vencimiento = dias_hasta_vencimiento / 365.0
                
                # 3. Estimar prima usando modelo simplificado
                moneyness = precio_stock / strike_real
                
                if moneyness > 1:  # OTM
                    otm_factor = 1 - moneyness
                    prima_base = precio_stock * volatilidad_anual * np.sqrt(tiempo_hasta_vencimiento) * 0.4
                    prima_estimada = prima_base * np.exp(otm_factor * 3)
                    
                    if dias_hasta_vencimiento <= 2:
                        prima_minima = precio_stock * 0.001 * (1 + volatilidad_anual)
                        prima_estimada = max(prima_estimada, prima_minima)
                else:
                    prima_estimada = max(strike_real - precio_stock, 0) + precio_stock * volatilidad_anual * np.sqrt(tiempo_hasta_vencimiento) * 0.4
                
                # 4. Ajustar prima al rango esperado
                prima_entrada = min(max(prima_estimada, rango['min']), rango['max'])
                
                # 5. Estimar variación intradiaria
                factor_variacion = 1 + (volatilidad_anual * 0.5)
                prima_maxima_dia1 = prima_estimada * factor_variacion
                
                # 6. Estimar prima día 2 con decaimiento theta
                theta_decay = 1 / dias_hasta_vencimiento if dias_hasta_vencimiento > 0 else 0.5
                prima_maxima_dia2 = prima_maxima_dia1 * (1 - theta_decay * 0.3)
                
                # 7. Calcular ganancias estimadas
                ganancia_dia1 = ((prima_maxima_dia1 - prima_entrada) / prima_entrada * 100) if prima_entrada > 0 else 0
                ganancia_dia2 = ((prima_maxima_dia2 - prima_entrada) / prima_entrada * 100) if prima_entrada > 0 else 0
                
                exito_dia1 = '✅' if ganancia_dia1 >= 100 else '❌'
                exito_dia2 = '✅' if ganancia_dia2 >= 100 else '❌'
                
                print(f"\n📊 ESTIMACIÓN (sin datos históricos):")
                print(f"  Prima entrada estimada: ${prima_entrada:.2f}")
                print(f"  Prima máxima D1 estimada: ${prima_maxima_dia1:.2f}")
                print(f"  Prima máxima D2 estimada: ${prima_maxima_dia2:.2f}")
                print(f"  Ganancia D1 estimada: {ganancia_dia1:.1f}% {exito_dia1}")
                print(f"  Ganancia D2 estimada: {ganancia_dia2:.1f}% {exito_dia2}")
                
                return {
                    'ganancia_pct': round(ganancia_dia1, 1),
                    'ganancia_dia_siguiente': round(ganancia_dia2, 1),
                    'exito': exito_dia1,
                    'exito_dia2': exito_dia2,
                    'strike': strike_real,
                    'prima_entrada': round(prima_entrada, 2),
                    'prima_maxima': round(prima_maxima_dia1, 2),
                    'prima_maxima_dia2': round(prima_maxima_dia2, 2),
                    'mensaje': f'ESTIMADO - D1: ${prima_entrada}→${prima_maxima_dia1:.2f}'
                }
            
            precios_dia1 = []
            for agg in option_aggs_dia1:
                precios_dia1.append({
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close
                })
            
            # ✅ CORREGIDO: Buscar prima EN TODOS LOS PRECIOS del día (open, high, low, close)
            prima_entrada = None
            prima_maxima_dia1 = max([p['high'] for p in precios_dia1])
            
            print(f"Rango objetivo: ${rango['min']:.2f} - ${rango['max']:.2f}")
            print(f"Prima apertura (primera vela): ${precios_dia1[0]['open']:.2f}")
            
            # 1. Buscar la PRIMERA prima que esté dentro del rango en CUALQUIER momento del día
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
                
                print(f"📊 Total de precios recolectados: {len(todos_los_precios)}")
                print(f"📊 Rango de precios: ${min(todos_los_precios):.2f} - ${max(todos_los_precios):.2f}")
                
                rango_medio = (rango['min'] + rango['max']) / 2
                
                # Encontrar la prima más cercana al centro del rango
                prima_mas_cercana = min(todos_los_precios, key=lambda x: abs(x - rango_medio))
                
                print(f"🎯 Rango objetivo: ${rango['min']:.2f} - ${rango['max']:.2f}")
                print(f"🎯 Centro del rango: ${rango_medio:.2f}")
                print(f"🎯 Prima más cercana encontrada: ${prima_mas_cercana:.2f}")
                print(f"🎯 Diferencia al centro: ${abs(prima_mas_cercana - rango_medio):.2f}")
                
                # MEJORADO: Lógica más inteligente para aceptar primas
                # 1. Si está dentro del 50% extra del rango, aceptar
                margen_extra = (rango['max'] - rango['min']) * 0.5
                limite_superior = rango['max'] + margen_extra
                limite_inferior = max(0.01, rango['min'] - margen_extra)  # Nunca menos de $0.01
                
                print(f"🎯 Límites flexibles: ${limite_inferior:.2f} - ${limite_superior:.2f}")
                
                # 2. Filtrar solo primas dentro de límites razonables
                primas_aceptables = [p for p in todos_los_precios if limite_inferior <= p <= limite_superior]
                
                if primas_aceptables:
                    # Encontrar la más cercana al rango objetivo
                    prima_entrada = min(primas_aceptables, key=lambda x: 
                        0 if rango['min'] <= x <= rango['max'] else  # Prioridad 0 si está en rango
                        min(abs(x - rango['min']), abs(x - rango['max']))  # Distancia al rango si está fuera
                    )
                    print(f"✅ Prima seleccionada: ${prima_entrada:.2f} (de {len(primas_aceptables)} opciones aceptables)")
                else:
                    # Si no hay primas en límites razonables, tomar la más cercana pero avisar
                    prima_entrada = prima_mas_cercana
                    print(f"⚠️ AVISO: Usando prima fuera de límites: ${prima_entrada:.2f}")
                    print(f"⚠️ Rango esperado: ${rango['min']:.2f}-${rango['max']:.2f}")
                    
                    # Si la prima está MUY lejos (más de 5x el rango máximo), rechazar
                    if prima_entrada > rango['max'] * 5:
                        print(f"❌ Prima demasiado cara: ${prima_entrada:.2f} > ${rango['max'] * 5:.2f} (5x máximo)")
                        return {
                            'ganancia_pct': 0,
                            'ganancia_dia_siguiente': 0,
                            'exito': '❌',
                            'exito_dia2': '❌',
                            'strike': strike_real,
                            'prima_entrada': 0,
                            'prima_maxima': 0,
                            'prima_maxima_dia2': 0,
                            'mensaje': f'Prima muy cara: ${prima_entrada:.2f} (máx: ${rango["max"]:.2f})'
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
                # ✅ Usando agregados de 30 MINUTOS (igual que día 1)
                option_aggs_dia2 = client.get_aggs(
                    ticker=option_ticker,
                    multiplier=30,  # ✅ 30 minutos
                    timespan="minute",
                    from_=fecha_dia_siguiente_str,
                    to=fecha_dia_siguiente_str,
                    limit=5000  # Suficiente para todo el día
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
    """Carga histórico de 4 meses para todos los tickers"""
    # NUEVO: Confirmación para borrar datos existentes
    st.warning("⚠️ **Importante**: Se recomienda borrar los datos existentes antes de cargar nuevos para evitar duplicados")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🗑️ Borrar y cargar limpio", type="primary", key="borrar_antes_cargar"):
            try:
                archivos_borrados = []
                if os.path.exists("historial_operaciones.json"):
                    os.remove("historial_operaciones.json")
                    archivos_borrados.append("historial_operaciones.json")
                if os.path.exists("resultados_historicos.json"):
                    os.remove("resultados_historicos.json")
                    archivos_borrados.append("resultados_historicos.json")
                
                if archivos_borrados:
                    st.success(f"✅ Archivos borrados: {', '.join(archivos_borrados)}")
                    st.info("🔄 Recargando aplicación...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info("No había archivos para borrar")
            except Exception as e:
                st.error(f"Error al borrar archivos: {e}")
                return
    
    with col2:
        if st.button("💾 Mantener datos existentes", key="mantener_datos"):
            st.info("📁 Los nuevos datos se agregarán a los existentes")
    
    with col3:
        st.caption("Selecciona una opción antes de continuar")
    
    # Solo continuar si se seleccionó alguna opción
    if not (st.session_state.get('borrar_antes_cargar') or st.session_state.get('mantener_datos')):
        st.stop()
    
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
            
            # Calcular RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Calcular Bollinger Bands
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
                
                # VERIFICAR VELA ROJA
                vela_roja = actual['close'] < anterior['close']
                
                if not vela_roja:
                    continue
                
                senales_ticker += 1
                
                rsi_actual = actual['RSI'] if not pd.isna(actual['RSI']) else 50
                bb_position_actual = actual['BB_Position'] if not pd.isna(actual['BB_Position']) else 0.5
                
                fecha_dia = actual.name.to_pydatetime()
                fecha_str = fecha_dia.strftime('%Y-%m-%d')
                
                # VERIFICAR SI YA EXISTE - NO DUPLICAR
                ya_existe = any(
                    r['fecha'] == fecha_str and r['ticker'] == ticker 
                    for r in analisis.resultados_historicos
                )
                
                if ya_existe:
                    continue
                
                ganancia_real = calcular_ganancia_real_opcion(
                    client,
                    ticker,
                    fecha_dia,
                    actual['open']
                )
                
                if ganancia_real['ganancia_pct'] > 0:
                    analisis.agregar_resultado(
                        fecha=fecha_str,
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
            
            total_senales_detectadas += senales_ticker
            st.write(f"✅ {ticker}: {senales_ticker} señales | {guardados_ticker} guardadas")
            
        except Exception as e:
            st.write(f"❌ {ticker}: Error - {str(e)}")
    
    progress_bar.empty()
    status_text.empty()
    
    st.success(f"""
    ✅ Carga histórica completada!
    
    📊 Estadísticas:
    - Días analizados: {total_dias_analizados}
    - Señales detectadas: {total_senales_detectadas}
    - Resultados guardados: {total_guardados}
    - Total en base de datos: {len(analisis.resultados_historicos)}
    """)
    st.balloons()
    
    time.sleep(3)
    st.rerun()

def main():
    st.title("🎯 AG1VR - DETECCIÓN EN TIEMPO REAL")
    
    try:
        client = RESTClient(API_KEY)
        st.success("✅ Conectado a Polygon.io")
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return
    
    # USAR TODOS LOS 33 TICKERS DEFINIDOS EN RANGOS_PRIMA
    tickers = list(RANGOS_PRIMA.keys())
    st.info(f"📊 Analizando {len(tickers)} tickers: {', '.join(tickers[:10])}...")
    
    analisis = AnalisisHistorico()
    
    # Verificar si hay suficientes datos históricos
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
        
        # BOTÓN PARA DESCARGAR BASE DE DATOS
        st.divider()
        st.subheader("💾 Gestión de Datos")
        
        if num_registros > 0:
            # Preparar JSON para descarga
            json_data = json.dumps(analisis.resultados_historicos, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="📥 Descargar Base de Datos",
                data=json_data,
                file_name=f"resultados_historicos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                help="Descarga todos los resultados guardados en formato JSON"
            )
        
        # BOTÓN PARA BORRAR BASE DE DATOS
        st.caption("⚠️ Usa esto solo si hay datos corruptos")
        if st.button("🗑️ Borrar Base de Datos", type="secondary", use_container_width=True, help="Elimina todos los datos y empieza limpio"):
            if st.session_state.get('confirmar_borrar', False):
                try:
                    if os.path.exists("historial_operaciones.json"):
                        os.remove("historial_operaciones.json")
                    if os.path.exists("resultados_historicos.json"):
                        os.remove("resultados_historicos.json")
                    st.success("✅ Base de datos borrada completamente")
                    st.info("🔄 Recargando página...")
                    time.sleep(2)
                    st.session_state.confirmar_borrar = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.session_state.confirmar_borrar = True
                st.warning("⚠️ Click de nuevo para CONFIRMAR el borrado")
                st.rerun()
    
    fecha_desde = (fecha_seleccionada - timedelta(days=30)).strftime('%Y-%m-%d')
    fecha_hasta = fecha_seleccionada.strftime('%Y-%m-%d')
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
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
                # Primero obtener datos diarios para RSI/BB
                aggs_daily = client.get_aggs(
                    ticker=ticker,
                    multiplier=1,
                    timespan="day",
                    from_=fecha_desde,
                    to=fecha_hasta,
                    limit=30
                )
                
                if not aggs_daily:
                    continue
                
                data = []
                for agg in aggs_daily:
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
                
                # Calcular RSI
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
                
                # Calcular Bollinger Bands
                df['SMA_20'] = df['close'].rolling(20).mean()
                df['STD_20'] = df['close'].rolling(20).std()
                df['BB_Upper'] = df['SMA_20'] + (df['STD_20'] * 2)
                df['BB_Lower'] = df['SMA_20'] - (df['STD_20'] * 2)
                df['BB_Position'] = (df['close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
                
                if len(df) < 2:
                    continue
                    
                ultimo = df.iloc[-1]
                anterior = df.iloc[-2]
                
                # VERIFICAR PRIMERA VELA ROJA (30 minutos de 9:30-10:00 AM)
                fecha_analisis_str = fecha_seleccionada.strftime('%Y-%m-%d')
                
                # Obtener velas de 30 minutos del día
                aggs_30min = client.get_aggs(
                    ticker=ticker,
                    multiplier=30,
                    timespan="minute",
                    from_=fecha_analisis_str,
                    to=fecha_analisis_str,
                    limit=20  # Traer varias para encontrar la primera
                )
                
                if aggs_30min:
                    # Encontrar la primera vela (la más temprana)
                    primera_vela = min(aggs_30min, key=lambda x: x.timestamp)
                    es_primera_vela_roja = primera_vela.close < primera_vela.open
                    
                    if not es_primera_vela_roja:
                        continue  # La primera vela NO es roja
                    
                    # Es vela roja!
                    hora_senal = "9:30-10:00 AM ET"
                else:
                    # Sin datos de 30 min, NO dar señal
                    continue
                
                rsi_actual = ultimo['RSI'] if not pd.isna(ultimo['RSI']) else 50
                bb_position_actual = ultimo['BB_Position'] if not pd.isna(ultimo['BB_Position']) else 0.5
                
                # Calcular probabilidad (ajustada según feedback de Alberto)
                # GLD Oct 23: RSI 62.6, BB 0.84 -> SÍ debe ser 1VR
                # USO Oct 24: RSI 41.6, BB 0.40 -> NO debe ser 1VR
                prob_base = 50  # Bajamos la base
                
                if rsi_actual > 70:
                    prob_ajustada = prob_base + 30
                elif rsi_actual > 60:
                    prob_ajustada = prob_base + 20  # GLD con RSI 62 debe dar señal
                elif rsi_actual > 50:
                    prob_ajustada = prob_base + 10
                else:
                    prob_ajustada = prob_base - 20  # USO con RSI 41 NO debe dar señal
                
                if bb_position_actual > 0.8:
                    prob_ajustada += 20  # GLD con BB 0.84 debe sumar más
                elif bb_position_actual > 0.6:
                    prob_ajustada += 10
                else:
                    prob_ajustada -= 10  # USO con BB 0.40 debe restar más
                
                probabilidad_final = max(0, min(100, prob_ajustada))
                
                if probabilidad_final >= threshold:
                    señal = "🎯 PUT"
                    trade = "SI"
                elif probabilidad_final >= 65:  # Subir de 60 a 65 para ser más estricto
                    señal = "🟡 PUT"
                    trade = "SI"
                else:
                    señal = "🚫 NO"
                    trade = "NO"
                
                # Calcular ganancia histórica con detalles
                ganancia_hist, num_dias_similares, dias_similares_detalle = analisis.calcular_ganancia_historica(
                    ticker, 
                    rsi_actual, 
                    bb_position_actual,
                    fecha_excluir=fecha_seleccionada.strftime('%Y-%m-%d'),
                    usar_mediana=False
                )
                
                # Calcular ganancia real
                ganancia_real = calcular_ganancia_real_opcion(
                    client,
                    ticker,
                    datetime.combine(fecha_seleccionada, datetime.min.time()),
                    ultimo['open']
                )
                
                # VERIFICAR DUPLICADOS - No guardar si ya existe este día
                fecha_str = fecha_seleccionada.strftime('%Y-%m-%d')
                ya_existe = any(
                    r['fecha'] == fecha_str and r['ticker'] == ticker 
                    for r in analisis.resultados_historicos
                )
                
                if not ya_existe and ganancia_real['ganancia_pct'] > 0:
                    analisis.agregar_resultado(
                        fecha=fecha_str,
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
                
                # SOLO agregar a resultados si tiene señal positiva (trade = SI)
                if trade == "SI":
                    if ganancia_hist is not None:
                        ganancia_hist_str = f"{int(ganancia_hist)}% ({num_dias_similares})"
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
                    'Éxito D2': ganancia_real['exito_dia2'],
                    '_dias_similares_detalle': dias_similares_detalle  # Para el modal
                })
                
            except Exception as e:
                st.write(f"❌ {ticker}: Error - {str(e)}")
        
        progress_bar.empty()
        status_text.empty()
        
        if resultados:
            st.subheader("📊 Resultados de Análisis")
            
            df_resultados = pd.DataFrame(resultados)
            
            # ORDENAR POR GANANCIA HISTÓRICA (mayor a menor) ANTES de formatear
            def extraer_ganancia_hist(ganancia_hist_str):
                if ganancia_hist_str == "Sin datos":
                    return -1  # Poner al final
                try:
                    return float(ganancia_hist_str.split('%')[0])
                except:
                    return -1
            
            df_resultados['_ganancia_sort'] = df_resultados['Ganancia Hist'].apply(extraer_ganancia_hist)
            df_resultados = df_resultados.sort_values('_ganancia_sort', ascending=False)
            
            # Guardar días similares detalle antes de eliminar columna
            dias_similares_map = dict(zip(df_resultados['Activo'], df_resultados['_dias_similares_detalle']))
            
            df_resultados = df_resultados.drop(['_ganancia_sort', '_dias_similares_detalle'], axis=1)
            
            # Renombrar columnas
            df_resultados = df_resultados.rename(columns={
                'Activo': 'Ticker',
                'Hora': 'Hora',
                'Señal': 'Señal',
                'Probabilidad': 'Prob (%)',
                'RSI': 'RSI',
                'BB': 'BB Pos',
                'Trade': 'Trade',
                'Strike': 'Strike PUT',
                'Prima Entrada': 'Prima Inicial',
                'Prima Máx D1': 'Prima Máx D1',
                'Prima Máx D2': 'Prima Máx D2',
                'Ganancia Hist': 'Ganancia Hist (n)',
                'Ganancia Día 1': 'Ganancia D1 (%)',
                'Ganancia Día 2': 'Ganancia D2 (%)',
                'Éxito D1': 'Éxito D1',
                'Éxito D2': 'Éxito D2',
                'Detalle': 'Ver Detalle'
            })
            
            # FORMATEAR SIN DECIMALES - SOLO ENTEROS
            df_resultados['Ganancia D1 (%)'] = df_resultados['Ganancia D1 (%)'].apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "0%")
            df_resultados['Ganancia D2 (%)'] = df_resultados['Ganancia D2 (%)'].apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "0%")
            df_resultados['Prob (%)'] = df_resultados['Prob (%)'].apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "0%")
            df_resultados['RSI'] = df_resultados['RSI'].apply(lambda x: f"{int(x)}" if pd.notnull(x) else "0")
            df_resultados['BB Pos'] = df_resultados['BB Pos'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "0.00")
            
            # Colorear columna Ganancia Hist
            def highlight_ganancia_hist(row):
                return ['background-color: #fffacd' if col == 'Ganancia Hist (n)' else '' for col in row.index]
            
            # Agregar nota sobre cómo ver detalles
            st.info("💡 **Tip**: Usa los expandibles debajo de cada ticker para ver el detalle de días históricos")
            
            # Mostrar tabla principal
            st.dataframe(
                df_resultados.style.apply(highlight_ganancia_hist, axis=1),
                use_container_width=True, 
                hide_index=True
            )
            
            # Crear expandibles para cada ticker con ganancia histórica
            st.markdown("---")
            st.subheader("📊 Detalle de Días Históricos por Ticker")
            
            # Filtrar solo tickers con datos históricos
            tickers_con_datos_hist = []
            for idx, row in df_resultados.iterrows():
                if "Sin datos" not in row['Ganancia Hist (n)']:
                    tickers_con_datos_hist.append(row['Ticker'])
            
            if tickers_con_datos_hist:
                # Crear columnas para organizar expandibles
                cols_per_row = 3
                for i in range(0, len(tickers_con_datos_hist), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, ticker in enumerate(tickers_con_datos_hist[i:i+cols_per_row]):
                        if j < len(cols):
                            with cols[j]:
                                # Obtener datos del ticker
                                row_data = df_resultados[df_resultados['Ticker'] == ticker].iloc[0]
                                ganancia_hist = row_data['Ganancia Hist (n)']
                                
                                # Crear expandible con información condensada
                                with st.expander(f"📁 {ticker} - {ganancia_hist}"):
                                    dias_detalle = dias_similares_map.get(ticker, [])
                                    if dias_detalle:
                                        st.success(f"✅ {len(dias_detalle)} días similares")
                                        
                                        # Mostrar estadísticas rápidas
                                        ganancias_d1 = [d['ganancia_d1'] for d in dias_detalle]
                                        promedio = np.mean(ganancias_d1)
                                        mediana = np.median(ganancias_d1)
                                        
                                        col_stat1, col_stat2 = st.columns(2)
                                        with col_stat1:
                                            st.metric("Promedio", f"{promedio:.0f}%")
                                        with col_stat2:
                                            st.metric("Mediana", f"{mediana:.0f}%")
                                        
                                        # Tabla compacta de días
                                        st.markdown("**Detalle por día:**")
                                        for d in dias_detalle[:5]:  # Mostrar solo primeros 5
                                            st.text(f"📅 {d['fecha']}: D1={d['ganancia_d1']:.0f}% | RSI={d['rsi']:.0f}")
                                        
                                        if len(dias_detalle) > 5:
                                            st.text(f"... y {len(dias_detalle)-5} días más")
                                    else:
                                        st.warning("Sin datos históricos")
            else:
                st.info("📊 No hay tickers con datos históricos para mostrar")
            
            # ==========================================
            # NUEVO: MODAL MEJORADO PARA DÍAS SIMILARES
            # ==========================================
            
            st.markdown("---")
            st.subheader("🔍 Ver Días Similares - Click en un ticker")
            
            # Info adicional
            st.markdown("📖 **Opciones adicionales**: También puedes usar los botones de abajo para ver detalles más completos")
            
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