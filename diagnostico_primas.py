"""
Diagnóstico de problemas con las primas
"""
import os
from polygon import RESTClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# API Key
API_KEY = os.getenv('POLYGON_API_KEY')
client = RESTClient(API_KEY)

def diagnosticar_problema(ticker='SPY', fecha_str='2024-10-21'):
    """Diagnostica por qué no se encuentran primas en el rango"""
    
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO COMPLETO PARA {ticker}")
    print(f"{'='*60}")
    
    # Configuración
    rango_prima = {'min': 0.25, 'max': 0.30}  # Para SPY
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
    precio_stock = 0
    
    # 1. Obtener precio del stock
    print(f"\n1️⃣ OBTENIENDO PRECIO DEL STOCK...")
    try:
        stock_aggs = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=fecha_str,
            to=fecha_str,
            limit=1
        )
        
        if stock_aggs:
            precio_stock = stock_aggs[0].open
            print(f"✅ Precio de {ticker}: ${precio_stock:.2f}")
        else:
            print(f"❌ No hay datos del stock para {fecha_str}")
            return
    except Exception as e:
        print(f"❌ Error obteniendo precio: {e}")
        return
    
    # 2. Calcular fecha de vencimiento
    print(f"\n2️⃣ CALCULANDO FECHA DE VENCIMIENTO...")
    if ticker in ['SPY', 'QQQ']:
        # D+1 para SPY/QQQ
        fecha_venc = fecha + timedelta(days=1)
        while fecha_venc.weekday() >= 5:  # Skip weekends
            fecha_venc += timedelta(days=1)
    else:
        # Viernes para otros
        dias_hasta_viernes = (4 - fecha.weekday()) % 7
        if dias_hasta_viernes == 0:
            dias_hasta_viernes = 7
        fecha_venc = fecha + timedelta(days=dias_hasta_viernes)
    
    fecha_venc_str = fecha_venc.strftime('%Y-%m-%d')
    print(f"✅ Fecha de vencimiento: {fecha_venc_str}")
    
    # 3. Buscar contratos disponibles
    print(f"\n3️⃣ BUSCANDO CONTRATOS DE OPCIONES...")
    import requests
    
    # Primero, buscar TODOS los contratos disponibles sin filtrar por fecha
    print("\n🔍 Paso 1: Buscando TODOS los contratos PUT disponibles...")
    
    url = "https://api.polygon.io/v3/reference/options/contracts"
    params = {
        'underlying_ticker': ticker,
        'contract_type': 'put',
        'limit': 100,
        'apiKey': API_KEY,
        'order': 'asc',
        'sort': 'expiration_date'
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"❌ Error en API: {response.status_code}")
        print(f"Respuesta: {response.text}")
        return
    
    data = response.json()
    todos_contratos = data.get('results', [])
    
    if todos_contratos:
        # Mostrar todas las fechas de vencimiento disponibles
        fechas_disponibles = sorted(set(c['expiration_date'] for c in todos_contratos))
        print(f"✅ Encontradas {len(todos_contratos)} opciones PUT")
        print(f"\n📅 Fechas de vencimiento disponibles (primeras 10):")
        for f in fechas_disponibles[:10]:
            print(f"   - {f}")
        
        # Ahora buscar la fecha específica o la más cercana
        print(f"\n🎯 Buscando contratos para {fecha_venc_str}...")
        
        contratos = [c for c in todos_contratos if c['expiration_date'] == fecha_venc_str]
        
        if not contratos:
            # Buscar la fecha más cercana
            from datetime import datetime as dt
            fecha_obj = dt.strptime(fecha_venc_str, '%Y-%m-%d')
            
            fechas_cercanas = sorted(fechas_disponibles, 
                key=lambda x: abs((dt.strptime(x, '%Y-%m-%d') - fecha_obj).days))
            
            fecha_mas_cercana = fechas_cercanas[0] if fechas_cercanas else None
            
            if fecha_mas_cercana:
                print(f"⚠️ No hay contratos exactos para {fecha_venc_str}")
                print(f"🎯 Usando fecha más cercana: {fecha_mas_cercana}")
                contratos = [c for c in todos_contratos if c['expiration_date'] == fecha_mas_cercana]
                fecha_venc_str = fecha_mas_cercana
            else:
                print("❌ No se encontraron contratos cercanos")
                return
        
        print(f"✅ Encontrados {len(contratos)} contratos para {fecha_venc_str}")
    else:
        print("❌ No hay contratos PUT disponibles")
        return
    
    # 4. Analizar primas de los primeros contratos
    print(f"\n4️⃣ ANALIZANDO PRIMAS (primeros 5 contratos)...")
    print(f"🎯 Buscando primas en rango: ${rango_prima['min']:.2f} - ${rango_prima['max']:.2f}")
    
    contratos_con_prima = []
    
    for i, contrato in enumerate(contratos[:5]):
        option_ticker = contrato['ticker']
        strike = contrato['strike_price']
        
        print(f"\n📌 Contrato {i+1}: {option_ticker}")
        print(f"   Strike: ${strike:.2f}")
        
        try:
            # Obtener datos del día
            option_aggs = client.get_aggs(
                ticker=option_ticker,
                multiplier=30,
                timespan="minute",
                from_=fecha_str,
                to=fecha_str,
                limit=50
            )
            
            if option_aggs:
                precios = []
                for agg in option_aggs[:3]:  # Solo primeras 3 velas
                    precios.extend([agg.open, agg.high, agg.low, agg.close])
                
                min_precio = min(precios)
                max_precio = max(precios)
                
                print(f"   Rango de precios: ${min_precio:.2f} - ${max_precio:.2f}")
                
                # Verificar si está en rango
                en_rango = any(rango_prima['min'] <= p <= rango_prima['max'] for p in precios)
                
                if en_rango:
                    print(f"   ✅ PRIMA EN RANGO!")
                    contratos_con_prima.append({
                        'ticker': option_ticker,
                        'strike': strike,
                        'min': min_precio,
                        'max': max_precio
                    })
                else:
                    print(f"   ❌ Fuera de rango")
            else:
                print(f"   ⚠️ Sin datos de precios")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 5. Resumen
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN DEL DIAGNÓSTICO")
    print(f"{'='*60}")
    print(f"Ticker: {ticker}")
    print(f"Fecha análisis: {fecha_str}")
    print(f"Precio stock: ${precio_stock:.2f}")
    print(f"Vencimiento buscado: {fecha_venc_str}")
    print(f"Rango prima objetivo: ${rango_prima['min']:.2f} - ${rango_prima['max']:.2f}")
    print(f"Contratos totales encontrados: {len(contratos)}")
    print(f"Contratos con prima en rango: {len(contratos_con_prima)}")
    
    if contratos_con_prima:
        print(f"\n✅ CONTRATOS EN RANGO ENCONTRADOS:")
        for c in contratos_con_prima:
            print(f"   - Strike ${c['strike']:.2f}: ${c['min']:.2f} - ${c['max']:.2f}")
    else:
        print(f"\n⚠️ POSIBLES PROBLEMAS:")
        print(f"1. La fecha {fecha_str} podría no tener liquidez")
        print(f"2. El rango ${rango_prima['min']:.2f}-${rango_prima['max']:.2f} podría ser muy restrictivo")
        print(f"3. Los datos podrían no estar disponibles para esa fecha")
        print(f"4. Verificar que el plan Developer esté activo")

if __name__ == "__main__":
    # Probar con diferentes fechas
    print("PROBANDO CON DIFERENTES FECHAS...")
    
    fechas_prueba = [
        '2024-10-21',  # Lunes octubre 2024
        '2024-10-18',  # Viernes octubre 2024
        '2024-10-17',  # Jueves octubre 2024
        '2024-09-20',  # Viernes septiembre 2024
    ]
    
    for fecha in fechas_prueba[:1]:  # Solo la primera por ahora
        diagnosticar_problema('SPY', fecha)