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
    'NVDA': {'min': 0.80, 'max': 1.00, 'vencimiento': 'viernes'},
    'TESLA': {'min': 0.80, 'max': 1.00, 'vencimiento': 'viernes'},
    'GLD': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'GOOGL': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'GOOG': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'BRK.B': {'min': 0.50, 'max': 0.70, 'vencimiento': 'viernes'},
    'JPM': {'min': 0.50, 'max': 0.70, 'vencimiento': 'viernes'},
    'V': {'min': 0.50, 'max': 0.70, 'vencimiento': 'viernes'},
    'MA': {'min': 0.50, 'max': 0.70, 'vencimiento': 'viernes'},
    'UNH': {'min': 0.50, 'max': 0.70, 'vencimiento': 'viernes'},
    'HD': {'min': 0.50, 'max': 0.70, 'vencimiento': 'viernes'},
    'DIS': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'ADBE': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'CRM': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'NFLX': {'min': 0.70, 'max': 0.90, 'vencimiento': 'viernes'},
    'PFE': {'min': 0.40, 'max': 0.60, 'vencimiento': 'viernes'},
    'KO': {'min': 0.30, 'max': 0.50, 'vencimiento': 'viernes'},
    'PEP': {'min': 0.30, 'max': 0.50, 'vencimiento': 'viernes'},
    'WMT': {'min': 0.40, 'max': 0.60, 'vencimiento': 'viernes'},
    'BAC': {'min': 0.40, 'max': 0.60, 'vencimiento': 'viernes'},
    'XOM': {'min': 0.50, 'max': 0.70, 'vencimiento': 'viernes'},
    'CVX': {'min': 0.50, 'max': 0.70, 'vencimiento': 'viernes'},
    'ABBV': {'min': 0.40, 'max': 0.60, 'vencimiento': 'viernes'},
    'COST': {'min': 0.50, 'max': 0.70, 'vencimiento': 'viernes'},
    'AVGO': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'},
    'INTC': {'min': 0.60, 'max': 0.80, 'vencimiento': 'viernes'}
}

# Configuración
API_KEY = os.getenv('POLYGON_API_KEY')

if not API_KEY:
    st.error("🔴 No se encontró POLYGON_API_KEY en las variables de entorno.")
    st.stop()

print(f"✅ API Key cargada (primeros 8 caracteres): {API_KEY[:8]}...")

# Polygon REST Client
try:
    from polygon import RESTClient
    client = RESTClient(api_key=API_KEY)
except Exception as e:
    st.error(f"Error al conectar con Polygon: {str(e)}")
    st.info("💡 Ejecuta: pip install polygon-api-client")
    st.stop()

# Función para calcular fecha de vencimiento
def calcular_fecha_vencimiento(fecha_actual, ticker):
    """Calcula la fecha de vencimiento según el ticker"""
    if ticker in ['SPY', 'QQQ']:
        # Siguiente día hábil
        fecha_venc = fecha_actual + timedelta(days=1)
        while fecha_venc.weekday() >= 5:  # 5 = sábado, 6 = domingo
            fecha_venc += timedelta(days=1)
        return fecha_venc
    else:
        # Próximo viernes
        dias_hasta_viernes = (4 - fecha_actual.weekday()) % 7
        if dias_hasta_viernes == 0:  # Si hoy es viernes
            dias_hasta_viernes = 7  # Próximo viernes
        fecha_venc = fecha_actual + timedelta(days=dias_hasta_viernes)
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
            
            contratos = data.get('results', [])
            
            if contratos:
                print(f"✅ {len(contratos)} contratos encontrados")
                return contratos
            else:
                print("⚠️ No hay contratos en esa fecha exacta, buscando fechas cercanas...")
                
                # INTENTO 2: Búsqueda más amplia (sin fecha específica)
                fecha_actual = fecha_vencimiento
                contratos_totales = []
                
                for i in range(7):  # Buscar en los próximos 7 días
                    fecha_busqueda = fecha_actual + timedelta(days=i)
                    fecha_busqueda_str = fecha_busqueda.strftime('%Y-%m-%d')
                    
                    params_amplio = {
                        'underlying_ticker': ticker,
                        'contract_type': 'put',
                        'expiration_date': fecha_busqueda_str,
                        'limit': 1000,
                        'apiKey': API_KEY
                    }
                    
                    response_amplio = requests.get(url, params=params_amplio)
                    
                    if response_amplio.status_code == 200:
                        data_amplio = response_amplio.json()
                        contratos_dia = data_amplio.get('results', [])
                        if contratos_dia:
                            print(f"  ✅ {fecha_busqueda_str}: {len(contratos_dia)} contratos")
                            contratos_totales.extend(contratos_dia)
                    
                    time.sleep(0.1)  # Rate limiting
                
                if contratos_totales:
                    print(f"✅ Total: {len(contratos_totales)} contratos encontrados")
                    return contratos_totales
                else:
                    print("❌ No se encontraron contratos en ninguna fecha cercana")
                    return []
        
        return []
            
    except Exception as e:
        print(f"❌ Error buscando contratos: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def calcular_ganancia_real_opcion_v2(client, ticker, fecha, precio_stock):
    """
    NUEVA VERSIÓN: Calcula ganancia usando una aproximación basada en Greeks y volatilidad
    cuando no hay datos históricos de agregados disponibles (plan Starter)
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
                'mensaje': 'Sin rango'
            }
        
        rango = RANGOS_PRIMA[ticker]
        fecha_vencimiento = calcular_fecha_vencimiento(fecha, ticker)
        strike_objetivo = round(precio_stock * 0.97, 2)
        
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        # Calcular día siguiente saltando fines de semana
        fecha_dia_siguiente = fecha + timedelta(days=1)
        while fecha_dia_siguiente.weekday() >= 5:
            fecha_dia_siguiente += timedelta(days=1)
        fecha_dia_siguiente_str = fecha_dia_siguiente.strftime('%Y-%m-%d')
        
        print(f"\n=== BUSCANDO OPCIÓN PARA {ticker} ===")
        print(f"Fecha análisis: {fecha_str}")
        print(f"Fecha día siguiente (hábil): {fecha_dia_siguiente_str}")
        print(f"Precio stock: ${precio_stock:.2f}")
        print(f"Strike objetivo (3% OTM): ${strike_objetivo:.2f}")
        
        # Buscar contratos disponibles
        contratos = buscar_contratos_disponibles(client, ticker, fecha_vencimiento)
        
        if not contratos or len(contratos) == 0:
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
        
        # Agrupar por fecha de vencimiento
        contratos_por_fecha = {}
        for contrato in contratos:
            fecha_exp = contrato.get('expiration_date', '')
            if fecha_exp not in contratos_por_fecha:
                contratos_por_fecha[fecha_exp] = []
            contratos_por_fecha[fecha_exp].append(contrato)
        
        # Seleccionar contratos más cercanos
        fechas_disponibles = sorted(contratos_por_fecha.keys())
        if fecha_vencimiento.strftime('%Y-%m-%d') in fechas_disponibles:
            fecha_elegida = fecha_vencimiento.strftime('%Y-%m-%d')
            contratos = contratos_por_fecha[fecha_elegida]
        else:
            fecha_elegida = fechas_disponibles[0]
            contratos = contratos_por_fecha[fecha_elegida]
        
        # Buscar el strike más cercano
        mejor_contrato = None
        menor_diferencia = float('inf')
        
        for contrato in contratos:
            strike_contrato = contrato.get('strike_price', 0)
            diferencia = abs(strike_contrato - strike_objetivo)
            
            if diferencia < menor_diferencia:
                menor_diferencia = diferencia
                mejor_contrato = contrato
        
        if not mejor_contrato:
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
        
        # NUEVA ESTRATEGIA: Usar aproximación basada en la volatilidad del subyacente
        # y la distancia al strike para estimar las primas
        
        # 1. Obtener volatilidad del subyacente (últimos 30 días)
        fecha_30_dias_atras = fecha - timedelta(days=30)
        
        try:
            # Obtener datos históricos del subyacente
            stock_aggs = client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=fecha_30_dias_atras.strftime('%Y-%m-%d'),
                to=fecha_str,
                limit=50
            )
            
            if stock_aggs and len(stock_aggs) > 10:
                # Calcular volatilidad histórica
                precios_cierre = [agg.close for agg in stock_aggs]
                rendimientos = []
                for i in range(1, len(precios_cierre)):
                    rendimiento = np.log(precios_cierre[i] / precios_cierre[i-1])
                    rendimientos.append(rendimiento)
                
                volatilidad_diaria = np.std(rendimientos)
                volatilidad_anual = volatilidad_diaria * np.sqrt(252)  # 252 días de trading
                
                print(f"📊 Volatilidad anual calculada: {volatilidad_anual:.2%}")
            else:
                # Volatilidad por defecto según el ticker
                volatilidades_default = {
                    'SPY': 0.15,
                    'QQQ': 0.20,
                    'AAPL': 0.25,
                    'AMD': 0.40,
                    'AMZN': 0.25,
                    'META': 0.30,
                    'MSFT': 0.22,
                    'NVDA': 0.45,
                    'TESLA': 0.50,
                    'GLD': 0.12,
                    'GOOGL': 0.25,
                    'GOOG': 0.25,
                    'BRK.B': 0.18,
                    'JPM': 0.22,
                    'V': 0.20,
                    'MA': 0.22,
                    'UNH': 0.20,
                    'HD': 0.22,
                    'DIS': 0.28,
                    'ADBE': 0.30,
                    'CRM': 0.32,
                    'NFLX': 0.35,
                    'PFE': 0.25,
                    'KO': 0.16,
                    'PEP': 0.16,
                    'WMT': 0.20,
                    'BAC': 0.25,
                    'XOM': 0.28,
                    'CVX': 0.28,
                    'ABBV': 0.22,
                    'COST': 0.20,
                    'AVGO': 0.30,
                    'INTC': 0.35
                }
                volatilidad_anual = volatilidades_default.get(ticker, 0.25)
                print(f"⚠️ Usando volatilidad por defecto: {volatilidad_anual:.2%}")
        except:
            volatilidad_anual = 0.25  # Por defecto
            
        # 2. Estimar prima usando aproximación Black-Scholes simplificada
        # Para opciones PUT OTM de corto plazo
        
        dias_hasta_vencimiento = (fecha_vencimiento - fecha).days
        tiempo_hasta_vencimiento = dias_hasta_vencimiento / 365.0
        
        # Distancia al strike (moneyness)
        moneyness = precio_stock / strike_real
        
        # Prima aproximada (simplificación para PUT OTM)
        if moneyness > 1:  # OTM
            # Factor de decaimiento por estar OTM
            otm_factor = 1 - moneyness
            
            # Prima base usando volatilidad y tiempo
            prima_base = precio_stock * volatilidad_anual * np.sqrt(tiempo_hasta_vencimiento) * 0.4
            
            # Ajustar por qué tan OTM está
            prima_estimada = prima_base * np.exp(otm_factor * 3)
            
            # Para opciones muy cortas (1-2 días), usar un mínimo
            if dias_hasta_vencimiento <= 2:
                prima_minima = precio_stock * 0.001 * (1 + volatilidad_anual)
                prima_estimada = max(prima_estimada, prima_minima)
        else:
            # ITM o ATM - usar aproximación diferente
            prima_estimada = max(strike_real - precio_stock, 0) + precio_stock * volatilidad_anual * np.sqrt(tiempo_hasta_vencimiento) * 0.4
        
        print(f"💰 Prima estimada: ${prima_estimada:.2f}")
        
        # 3. Simular variación de la prima durante el día
        # Las opciones típicamente tienen mayor prima al inicio del día y decaen
        
        # Prima de entrada (asumimos entrada con prima en el rango)
        prima_entrada = min(max(prima_estimada, rango['min']), rango['max'])
        
        # Prima máxima del día (típicamente 10-30% más alta que la estimada)
        factor_variacion = 1 + (volatilidad_anual * 0.5)  # Mayor volatilidad = mayor variación
        prima_maxima = prima_estimada * factor_variacion
        
        # Prima máxima día 2 (con decaimiento theta)
        theta_decay = 1 / dias_hasta_vencimiento if dias_hasta_vencimiento > 0 else 0.5
        prima_maxima_dia2 = prima_maxima * (1 - theta_decay * 0.3)  # 30% del theta
        
        # 4. Calcular ganancias
        ganancia_pct = ((prima_maxima - prima_entrada) / prima_entrada * 100) if prima_entrada > 0 else 0
        ganancia_dia_siguiente = ((prima_maxima_dia2 - prima_entrada) / prima_entrada * 100) if prima_entrada > 0 else 0
        
        # Determinar éxito
        exito = '✅' if ganancia_pct >= 20 else '❌'
        exito_dia2 = '✅' if ganancia_dia_siguiente >= 20 else '❌'
        
        print(f"\n📊 RESULTADOS ESTIMADOS:")
        print(f"  Prima entrada: ${prima_entrada:.2f}")
        print(f"  Prima máxima día 1: ${prima_maxima:.2f}")
        print(f"  Prima máxima día 2: ${prima_maxima_dia2:.2f}")
        print(f"  Ganancia día 1: {ganancia_pct:.1f}%")
        print(f"  Ganancia día 2: {ganancia_dia_siguiente:.1f}%")
        
        return {
            'ganancia_pct': round(ganancia_pct, 1),
            'ganancia_dia_siguiente': round(ganancia_dia_siguiente, 1),
            'exito': exito,
            'exito_dia2': exito_dia2,
            'strike': strike_real,
            'prima_entrada': round(prima_entrada, 2),
            'prima_maxima': round(prima_maxima, 2),
            'prima_maxima_dia2': round(prima_maxima_dia2, 2),
            'mensaje': 'Estimado (sin datos históricos)'
        }
        
    except Exception as e:
        print(f"❌ Error en cálculo: {str(e)}")
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

# Usar la nueva función en lugar de la anterior
calcular_ganancia_real_opcion = calcular_ganancia_real_opcion_v2

# ===== CONFIGURACIÓN DE PÁGINA =====
st.set_page_config(
    page_title="AG SPY System V90b - Mobile",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===== CSS OPTIMIZADO PARA MÓVIL =====
st.markdown("""
<style>
    /* Diseño móvil */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
        padding: 0.5rem;
        max-width: 100vw;
    }
    
    /* Métricas compactas para móvil */
    [data-testid="metric-container"] {
        background-color: #1e1e1e;
        border: 1px solid #333;
        padding: 0.4rem;
        border-radius: 6px;
        margin: 0.2rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    [data-testid="metric-container"] > div {
        padding: 0 !important;
    }
    
    [data-testid="metric-container"] label {
        font-size: 0.75rem !important;
        color: #999;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 1.2rem !important;
        font-weight: bold;
    }
    
    [data-testid="metric-container"] [data-testid="metric-delta"] {
        font-size: 0.7rem !important;
    }
    
    /* Tabs optimizados para móvil */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.3rem;
        padding: 0.3rem;
        background-color: #1e1e1e;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.4rem 0.8rem;
        font-size: 0.8rem;
        background-color: #2a2a2a;
        color: #ccc;
        border: 1px solid #444;
        border-radius: 6px;
        white-space: nowrap;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
        border-color: #4CAF50 !important;
        font-weight: bold;
    }
    
    /* Tablas móviles */
    .dataframe {
        font-size: 0.7rem !important;
        width: 100% !important;
    }
    
    .dataframe th {
        background-color: #2a2a2a !important;
        color: #e0e0e0 !important;
        padding: 0.3rem !important;
        font-size: 0.7rem !important;
        text-align: left !important;
        position: sticky;
        top: 0;
        z-index: 10;
        border: 1px solid #444 !important;
    }
    
    .dataframe td {
        padding: 0.3rem !important;
        background-color: #1e1e1e !important;
        color: #ccc !important;
        border: 1px solid #333 !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100px;
    }
    
    .dataframe tbody tr:hover {
        background-color: #2a2a2a !important;
    }
    
    /* Botones móviles */
    .stButton > button {
        width: 100%;
        padding: 0.5rem;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: bold;
        margin: 0.3rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .stButton > button:hover {
        background-color: #45a049;
        transform: translateY(-1px);
    }
    
    /* Inputs móviles */
    .stSelectbox, .stDateInput, .stNumberInput {
        margin: 0.3rem 0;
    }
    
    .stSelectbox > div > div, 
    .stDateInput > div > div,
    .stNumberInput > div > div {
        background-color: #2a2a2a !important;
        border: 1px solid #444 !important;
        color: #e0e0e0 !important;
        padding: 0.4rem !important;
        font-size: 0.85rem !important;
    }
    
    /* Headers móviles */
    h1, h2, h3 {
        color: #4CAF50 !important;
        margin: 0.5rem 0 !important;
    }
    
    h1 { font-size: 1.3rem !important; }
    h2 { font-size: 1.1rem !important; }
    h3 { font-size: 0.95rem !important; }
    
    /* Alertas móviles */
    .stAlert {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 6px;
        font-size: 0.8rem;
    }
    
    /* Expanders móviles */
    .streamlit-expanderHeader {
        background-color: #2a2a2a !important;
        border: 1px solid #444 !important;
        border-radius: 6px !important;
        padding: 0.5rem !important;
        font-size: 0.85rem !important;
    }
    
    /* Sidebar para móvil (si se usa) */
    section[data-testid="stSidebar"] {
        width: 80% !important;
        background-color: #1a1a1a;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #4CAF50 !important;
    }
    
    /* Responsive para pantallas pequeñas */
    @media (max-width: 480px) {
        .stApp { padding: 0.3rem; }
        [data-testid="metric-container"] { padding: 0.3rem; }
        .dataframe { font-size: 0.65rem !important; }
        .dataframe td { max-width: 80px; }
    }
</style>
""", unsafe_allow_html=True)

# ===== FUNCIONES PRINCIPALES =====
def analizar_ticker_historico(ticker):
    """Análisis histórico de un ticker con 20 días previos a cada señal alcista"""
    
    hoy = datetime.now().date()
    fecha_inicio = hoy - timedelta(days=365)  # 1 año de historia
    fecha_desde = fecha_inicio.strftime('%Y-%m-%d')
    fecha_hasta = hoy.strftime('%Y-%m-%d')
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text(f"📥 Descargando datos de {ticker}...")
        progress_bar.progress(10)
        
        # Obtener datos históricos
        aggs = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=fecha_desde,
            to=fecha_hasta,
            limit=5000
        )
        
        if not aggs or len(aggs) < 20:
            st.error(f"❌ Datos insuficientes para {ticker}")
            return pd.DataFrame()
        
        progress_bar.progress(30)
        status_text.text(f"🔍 Analizando {len(aggs)} días de datos...")
        
        # Convertir a DataFrame
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
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df = df.sort_index()
        
        # Calcular indicadores técnicos
        progress_bar.progress(40)
        status_text.text("📊 Calculando indicadores técnicos...")
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Medias móviles
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA50'] = df['close'].rolling(window=50).mean()
        
        # Bandas de Bollinger
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        
        # ADX
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = np.abs(df['high'] - df['close'].shift())
        df['low_close'] = np.abs(df['low'] - df['close'].shift())
        df['TR'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14).mean()
        
        df['+DM'] = np.where((df['high'] - df['high'].shift()) > (df['low'].shift() - df['low']), 
                             np.maximum(df['high'] - df['high'].shift(), 0), 0)
        df['-DM'] = np.where((df['low'].shift() - df['low']) > (df['high'] - df['high'].shift()), 
                             np.maximum(df['low'].shift() - df['low'], 0), 0)
        
        df['+DI'] = 100 * (df['+DM'].rolling(window=14).mean() / df['ATR'])
        df['-DI'] = 100 * (df['-DM'].rolling(window=14).mean() / df['ATR'])
        df['DX'] = 100 * np.abs((df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI']))
        df['ADX'] = df['DX'].rolling(window=14).mean()
        
        # OBV
        df['OBV'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        
        # Williams %R
        high_14 = df['high'].rolling(window=14).max()
        low_14 = df['low'].rolling(window=14).min()
        df['Williams_%R'] = -100 * (high_14 - df['close']) / (high_14 - low_14)
        
        # MACD
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_histograma'] = df['MACD'] - df['MACD_signal']
        
        # Stochastic
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['%K'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
        df['%D'] = df['%K'].rolling(window=3).mean()
        
        # Volatilidad
        df['returns'] = df['close'].pct_change()
        df['volatility_5'] = df['returns'].rolling(window=5).std() * np.sqrt(252)
        df['volatility_20'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
        
        # Detectar señales alcistas
        progress_bar.progress(60)
        status_text.text("🎯 Detectando señales alcistas...")
        
        # Condiciones para señal alcista
        df['setup_alcista'] = (
            (df['RSI'] < 30) &  # Sobreventa
            (df['close'] <= df['BB_lower']) &  # Toca banda inferior
            (df['ADX'] > 20) &  # Tendencia definida
            (df['+DI'] > df['-DI']) &  # Presión compradora
            (df['MACD_histograma'] > df['MACD_histograma'].shift()) &  # MACD mejorando
            (df['%K'] < 20)  # Stochastic sobreventa
        )
        
        # Buscar días con señal alcista
        signal_dates = df[df['setup_alcista']].index
        
        if len(signal_dates) == 0:
            st.warning(f"⚠️ No se encontraron señales alcistas fuertes en {ticker}")
            progress_bar.progress(100)
            return pd.DataFrame()
        
        # Analizar opciones PUT para cada señal
        progress_bar.progress(80)
        status_text.text("💰 Analizando opciones PUT en señales alcistas...")
        
        resultados = []
        total_signals = len(signal_dates)
        
        for idx, signal_date in enumerate(signal_dates):
            # Actualizar progreso
            progress = 80 + (20 * (idx + 1) / total_signals)
            progress_bar.progress(int(progress))
            
            # Obtener precio del stock en la señal
            precio_stock = df.loc[signal_date, 'close']
            
            # Calcular ganancia de la opción PUT
            resultado_opcion = calcular_ganancia_real_opcion(
                client,
                ticker,
                signal_date.date(),
                precio_stock
            )
            
            # Obtener indicadores del día
            indicadores = {
                'RSI': df.loc[signal_date, 'RSI'],
                'ADX': df.loc[signal_date, 'ADX'],
                'Williams_%R': df.loc[signal_date, 'Williams_%R'],
                'Volatilidad_20d': df.loc[signal_date, 'volatility_20'],
                'Distancia_BB': ((df.loc[signal_date, 'close'] - df.loc[signal_date, 'BB_lower']) / 
                                df.loc[signal_date, 'BB_lower'] * 100)
            }
            
            resultados.append({
                'Fecha': signal_date.date(),
                'Precio_Stock': precio_stock,
                'Strike_PUT': resultado_opcion['strike'],
                'Prima_Entrada': resultado_opcion['prima_entrada'],
                'Prima_Max_D1': resultado_opcion['prima_maxima'],
                'Ganancia_D1_%': resultado_opcion['ganancia_pct'],
                'Exito_D1': resultado_opcion['exito'],
                'Prima_Max_D2': resultado_opcion['prima_maxima_dia2'],
                'Ganancia_D2_%': resultado_opcion['ganancia_dia_siguiente'],
                'Exito_D2': resultado_opcion['exito_dia2'],
                'RSI': indicadores['RSI'],
                'ADX': indicadores['ADX'],
                'Williams_%R': indicadores['Williams_%R'],
                'Volatilidad_20d': indicadores['Volatilidad_20d'],
                'Distancia_BB_%': indicadores['Distancia_BB']
            })
        
        progress_bar.progress(100)
        status_text.text("✅ Análisis completado")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        
        return pd.DataFrame(resultados)
        
    except Exception as e:
        st.error(f"❌ Error analizando {ticker}: {str(e)}")
        progress_bar.empty()
        status_text.empty()
        return pd.DataFrame()

def realizar_backtest():
    """Realiza backtest sobre múltiples tickers"""
    
    st.header("🔄 Backtest Histórico")
    st.info("💡 Analiza señales alcistas históricas y el rendimiento de opciones PUT")
    
    # Selección de tickers
    col1, col2 = st.columns([3, 1])
    with col1:
        tickers_disponibles = list(RANGOS_PRIMA.keys())
        tickers_seleccionados = st.multiselect(
            "Selecciona tickers:",
            tickers_disponibles,
            default=['SPY', 'QQQ']
        )
    
    with col2:
        if st.button("🚀 Iniciar", use_container_width=True):
            if not tickers_seleccionados:
                st.error("❌ Selecciona al menos un ticker")
                return
            
            # Contenedor para resultados
            resultados_totales = []
            
            # Analizar cada ticker
            for ticker in tickers_seleccionados:
                with st.expander(f"📊 {ticker}", expanded=True):
                    df_resultado = analizar_ticker_historico(ticker)
                    
                    if not df_resultado.empty:
                        resultados_totales.append(df_resultado)
                        
                        # Mostrar métricas
                        col1, col2, col3 = st.columns(3)
                        
                        total_signals = len(df_resultado)
                        exitos_d1 = len(df_resultado[df_resultado['Exito_D1'] == '✅'])
                        exitos_d2 = len(df_resultado[df_resultado['Exito_D2'] == '✅'])
                        
                        with col1:
                            st.metric("Señales", total_signals)
                        with col2:
                            tasa_d1 = (exitos_d1/total_signals*100) if total_signals > 0 else 0
                            st.metric("Éxito D1", f"{tasa_d1:.1f}%", f"{exitos_d1}/{total_signals}")
                        with col3:
                            tasa_d2 = (exitos_d2/total_signals*100) if total_signals > 0 else 0
                            st.metric("Éxito D2", f"{tasa_d2:.1f}%", f"{exitos_d2}/{total_signals}")
                        
                        # Tabla de resultados
                        if len(df_resultado) > 0:
                            st.dataframe(
                                df_resultado[['Fecha', 'Precio_Stock', 'Prima_Entrada', 
                                            'Ganancia_D1_%', 'Exito_D1', 'Ganancia_D2_%', 'Exito_D2']],
                                use_container_width=True,
                                height=300
                            )
            
            # Resumen global
            if resultados_totales:
                st.header("📊 Resumen Global")
                
                df_total = pd.concat(resultados_totales, ignore_index=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Señales", len(df_total))
                
                with col2:
                    exitos_totales_d1 = len(df_total[df_total['Exito_D1'] == '✅'])
                    tasa_global_d1 = (exitos_totales_d1/len(df_total)*100) if len(df_total) > 0 else 0
                    st.metric("Tasa Éxito D1", f"{tasa_global_d1:.1f}%")
                
                with col3:
                    exitos_totales_d2 = len(df_total[df_total['Exito_D2'] == '✅'])
                    tasa_global_d2 = (exitos_totales_d2/len(df_total)*100) if len(df_total) > 0 else 0
                    st.metric("Tasa Éxito D2", f"{tasa_global_d2:.1f}%")
                
                with col4:
                    ganancia_promedio = df_total['Ganancia_D1_%'].mean()
                    st.metric("Ganancia Prom D1", f"{ganancia_promedio:.1f}%")

def buscar_oportunidades_hoy():
    """Busca oportunidades para hoy"""
    
    st.header("🎯 Oportunidades de Hoy")
    
    # Obtener fecha actual
    hoy = datetime.now().date()
    fecha_desde = (hoy - timedelta(days=30)).strftime('%Y-%m-%d')
    fecha_hasta = hoy.strftime('%Y-%m-%d')
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Analizar todos los tickers
    tickers = list(RANGOS_PRIMA.keys())
    total_tickers = len(tickers)
    oportunidades = []
    
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
            
            df = pd.DataFrame(data).set_index('timestamp').sort_index()
            
            # Calcular indicadores (simplificado)
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Bandas de Bollinger
            ma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            bb_lower = ma20 - (std20 * 2)
            
            # Valores actuales
            precio_actual = df['close'].iloc[-1]
            rsi_actual = rsi.iloc[-1]
            bb_lower_actual = bb_lower.iloc[-1]
            
            # Volatilidad
            returns = df['close'].pct_change()
            vol_20d = returns.rolling(window=20).std().iloc[-1] * np.sqrt(252)
            
            # Detectar oportunidad
            if rsi_actual < 35 and precio_actual <= bb_lower_actual * 1.02:
                # Calcular opción PUT
                resultado_opcion = calcular_ganancia_real_opcion(
                    client,
                    ticker,
                    hoy,
                    precio_actual
                )
                
                if resultado_opcion['prima_entrada'] > 0:
                    oportunidades.append({
                        'Ticker': ticker,
                        'Precio': precio_actual,
                        'RSI': rsi_actual,
                        'Dist_BB_%': ((precio_actual - bb_lower_actual) / bb_lower_actual * 100),
                        'Vol_20d': vol_20d,
                        'Strike_PUT': resultado_opcion['strike'],
                        'Prima': resultado_opcion['prima_entrada'],
                        'Target_20%': resultado_opcion['prima_entrada'] * 1.20
                    })
            
        except Exception as e:
            continue
    
    progress_bar.empty()
    status_text.empty()
    
    # Mostrar resultados
    if oportunidades:
        st.success(f"✅ {len(oportunidades)} oportunidades encontradas")
        
        df_oportunidades = pd.DataFrame(oportunidades)
        df_oportunidades = df_oportunidades.sort_values('RSI').reset_index(drop=True)
        
        # Formatear columnas
        for col in ['Precio', 'Strike_PUT', 'Prima', 'Target_20%']:
            if col in df_oportunidades.columns:
                df_oportunidades[col] = df_oportunidades[col].round(2)
        
        for col in ['RSI', 'Dist_BB_%', 'Vol_20d']:
            if col in df_oportunidades.columns:
                df_oportunidades[col] = df_oportunidades[col].round(1)
        
        st.dataframe(df_oportunidades, use_container_width=True)
        
        # Detalles por ticker
        st.subheader("📋 Detalles por Ticker")
        for _, row in df_oportunidades.iterrows():
            with st.expander(f"{row['Ticker']} - RSI: {row['RSI']:.1f}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Precio Stock:** ${row['Precio']:.2f}")
                    st.write(f"**Strike PUT:** ${row['Strike_PUT']:.2f}")
                    st.write(f"**Volatilidad 20d:** {row['Vol_20d']:.1%}")
                
                with col2:
                    st.write(f"**Prima entrada:** ${row['Prima']:.2f}")
                    st.write(f"**Target (+20%):** ${row['Target_20%']:.2f}")
                    st.write(f"**Distancia BB:** {row['Dist_BB_%']:.1f}%")
                
                # Tipo de opción según el ticker
                tipo_venc = RANGOS_PRIMA[row['Ticker']]['vencimiento']
                if tipo_venc == 'siguiente_dia':
                    st.info("⏰ Opción de vencimiento al siguiente día hábil")
                else:
                    st.info("📅 Opción de vencimiento el próximo viernes")
    else:
        st.warning("⚠️ No se encontraron oportunidades claras para hoy")
        st.info("💡 Los mercados no muestran condiciones de sobreventa significativa")

# ===== INTERFAZ PRINCIPAL =====
st.title("📱 AG SPY System V90b")
st.caption("Sistema de Análisis de Opciones PUT - Versión Móvil")

# Tabs principales
tab1, tab2, tab3 = st.tabs(["🎯 Hoy", "📊 Backtest", "ℹ️ Info"])

with tab1:
    buscar_oportunidades_hoy()

with tab2:
    realizar_backtest()

with tab3:
    st.header("ℹ️ Información del Sistema")
    
    st.subheader("📋 Rangos de Prima por Ticker")
    
    df_rangos = pd.DataFrame.from_dict(RANGOS_PRIMA, orient='index')
    df_rangos.index.name = 'Ticker'
    df_rangos['Rango'] = df_rangos.apply(lambda x: f"${x['min']:.2f} - ${x['max']:.2f}", axis=1)
    df_rangos['Vencimiento'] = df_rangos['vencimiento'].replace({
        'siguiente_dia': '1 día',
        'viernes': 'Viernes'
    })
    
    st.dataframe(
        df_rangos[['Rango', 'Vencimiento']],
        use_container_width=True
    )
    
    st.subheader("📊 Indicadores Utilizados")
    
    indicadores = {
        'RSI < 35': 'Sobreventa',
        'Precio ≤ BB inferior': 'Extremo estadístico',
        'ADX > 20': 'Tendencia definida',
        'MACD mejorando': 'Momentum positivo',
        'Stochastic < 20': 'Sobreventa extrema'
    }
    
    for indicador, descripcion in indicadores.items():
        st.write(f"• **{indicador}:** {descripcion}")
    
    st.subheader("🎯 Estrategia")
    
    st.write("""
    1. **Identificar sobreventa:** RSI < 35 + toca banda inferior
    2. **Comprar PUT OTM:** Strike ~3% por debajo del precio actual
    3. **Target:** +20% en la prima
    4. **Timeframe:** 
       - SPY/QQQ: Vencimiento al día siguiente
       - Otros: Vencimiento el viernes
    5. **Stop Loss:** -50% en la prima
    """)
    
    with st.expander("⚠️ Advertencias"):
        st.warning("""
        **IMPORTANTE:** 
        - Este sistema es para fines educativos
        - Las opciones son instrumentos de alto riesgo
        - Puedes perder el 100% de la inversión
        - Los resultados pasados no garantizan resultados futuros
        - Siempre usa gestión de riesgo apropiada
        """)
    
    st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Footer
st.markdown("---")
st.caption("AG SPY System V90b - Mobile Optimized | Desarrollado para análisis de opciones PUT")