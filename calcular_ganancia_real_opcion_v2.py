def calcular_ganancia_real_opcion_v2(client, ticker, fecha, precio_stock):
    """
    VERSIÓN MEJORADA que funciona para TODAS las fechas
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
        
        print(f"\n=== BUSCANDO OPCIÓN {ticker} - {fecha_str} ===")
        print(f"Precio stock: ${precio_stock:.2f}")
        print(f"Vencimiento: {fecha_vencimiento.strftime('%Y-%m-%d')}")
        print(f"Rango prima: ${rango['min']:.2f} - ${rango['max']:.2f}")
        
        # ESTRATEGIA DIFERENTE SEGÚN EL AÑO
        contratos_con_datos = []
        
        if fecha.year >= 2025:
            print("\n📅 Fecha FUTURA detectada - usando API de contratos")
            contratos = buscar_contratos_api(client, ticker, fecha_vencimiento)
        else:
            print("\n📅 Fecha PASADA detectada - generando contratos manualmente")
            contratos = generar_contratos_manual(ticker, fecha_vencimiento, precio_stock)
        
        if not contratos:
            print("❌ No hay contratos disponibles")
            return crear_resultado_vacio('Sin contratos')
        
        print(f"✅ {len(contratos)} contratos para analizar")
        
        # BUSCAR CONTRATOS CON PRIMA EN RANGO
        mejor_contrato = None
        prima_entrada = None
        contratos_probados = 0
        
        for contrato in contratos:
            if contratos_probados >= 50:  # Límite para no tardar demasiado
                break
                
            option_ticker = contrato['ticker']
            strike = contrato['strike_price']
            
            # Filtrar strikes razonables
            distancia_pct = ((strike - precio_stock) / precio_stock) * 100
            if distancia_pct < -15 or distancia_pct > 5:
                continue
            
            contratos_probados += 1
            
            # Obtener datos de la opción
            try:
                # Para fechas pasadas usar 1 minuto, para futuras 5 minutos
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
                    # Recolectar todos los precios
                    todos_precios = []
                    for agg in option_aggs:
                        todos_precios.extend([agg.open, agg.high, agg.low, agg.close])
                    
                    min_precio = min(todos_precios)
                    max_precio = max(todos_precios)
                    
                    # Verificar si hay precios en el rango
                    precios_en_rango = [p for p in todos_precios if rango['min'] <= p <= rango['max']]
                    
                    if precios_en_rango:
                        # ¡ENCONTRADO!
                        prima_entrada = precios_en_rango[0]  # Usar el primer precio en rango
                        mejor_contrato = contrato
                        
                        print(f"\n✅ ¡ENCONTRADO!")
                        print(f"   Strike: ${strike}")
                        print(f"   Prima en rango: ${prima_entrada:.2f}")
                        print(f"   Distancia: {distancia_pct:+.1f}%")
                        break
                    else:
                        # Guardar para análisis posterior
                        contratos_con_datos.append({
                            'contrato': contrato,
                            'min_precio': min_precio,
                            'max_precio': max_precio,
                            'promedio': sum(todos_precios) / len(todos_precios)
                        })
                        
                        if contratos_probados <= 5:
                            print(f"   Strike ${strike}: ${min_precio:.2f}-${max_precio:.2f}")
                            
            except Exception as e:
                if "NOT_AUTHORIZED" in str(e):
                    print(f"❌ Plan no incluye datos para {fecha_str}")
                    return crear_resultado_vacio('Plan no autorizado')
                continue
        
        # Si no encontramos prima exacta, buscar la más cercana
        if not mejor_contrato and contratos_con_datos:
            print("\n⚠️ No hay prima exacta en rango - buscando más cercana...")
            
            rango_medio = (rango['min'] + rango['max']) / 2
            
            # Ordenar por cercanía al rango
            contratos_con_datos.sort(
                key=lambda x: min(
                    abs(x['min_precio'] - rango_medio),
                    abs(x['max_precio'] - rango_medio),
                    abs(x['promedio'] - rango_medio)
                )
            )
            
            # Usar el más cercano
            mejor = contratos_con_datos[0]
            mejor_contrato = mejor['contrato']
            
            # Seleccionar prima apropiada
            if mejor['max_precio'] < rango['min']:
                prima_entrada = mejor['max_precio']
            elif mejor['min_precio'] > rango['max']:
                prima_entrada = mejor['min_precio']
            else:
                prima_entrada = mejor['promedio']
            
            print(f"✅ Seleccionado strike ${mejor_contrato['strike_price']} con prima ${prima_entrada:.2f}")
        
        if not mejor_contrato:
            return crear_resultado_vacio('Sin datos de primas')
        
        # CALCULAR GANANCIAS
        option_ticker = mejor_contrato['ticker']
        strike_real = mejor_contrato['strike_price']
        
        # Prima máxima día 1
        try:
            multiplier = 1 if fecha.year < 2025 else 5
            
            option_aggs_dia1 = client.get_aggs(
                ticker=option_ticker,
                multiplier=multiplier,
                timespan="minute",
                from_=fecha_str,
                to=fecha_str,
                limit=5000
            )
            
            if option_aggs_dia1:
                prima_maxima_dia1 = max([agg.high for agg in option_aggs_dia1])
                ganancia_dia1 = ((prima_maxima_dia1 - prima_entrada) / prima_entrada * 100)
            else:
                prima_maxima_dia1 = prima_entrada
                ganancia_dia1 = 0
                
        except:
            prima_maxima_dia1 = prima_entrada
            ganancia_dia1 = 0
        
        # Día 2
        fecha_dia2 = fecha + timedelta(days=1)
        while fecha_dia2.weekday() >= 5:
            fecha_dia2 += timedelta(days=1)
        
        try:
            option_aggs_dia2 = client.get_aggs(
                ticker=option_ticker,
                multiplier=multiplier,
                timespan="minute",
                from_=fecha_dia2.strftime('%Y-%m-%d'),
                to=fecha_dia2.strftime('%Y-%m-%d'),
                limit=5000
            )
            
            if option_aggs_dia2:
                prima_maxima_dia2 = max([agg.high for agg in option_aggs_dia2])
                ganancia_dia2 = ((prima_maxima_dia2 - prima_entrada) / prima_entrada * 100)
            else:
                prima_maxima_dia2 = 0
                ganancia_dia2 = 0
        except:
            prima_maxima_dia2 = 0
            ganancia_dia2 = 0
        
        print(f"\n📊 RESULTADOS:")
        print(f"   Strike: ${strike_real}")
        print(f"   Prima entrada: ${prima_entrada:.2f}")
        print(f"   Prima máx D1: ${prima_maxima_dia1:.2f}")
        print(f"   Ganancia D1: {ganancia_dia1:.1f}%")
        
        return {
            'ganancia_pct': round(ganancia_dia1, 1),
            'ganancia_dia_siguiente': round(ganancia_dia2, 1),
            'exito': '✅' if ganancia_dia1 >= 100 else '❌',
            'exito_dia2': '✅' if ganancia_dia2 >= 100 else '❌',
            'strike': strike_real,
            'prima_entrada': round(prima_entrada, 2),
            'prima_maxima': round(prima_maxima_dia1, 2),
            'prima_maxima_dia2': round(prima_maxima_dia2, 2),
            'mensaje': f'Strike ${strike_real} (prima ${prima_entrada:.2f})'
        }
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return crear_resultado_vacio(f'Error: {str(e)}')


def buscar_contratos_api(client, ticker, fecha_vencimiento):
    """Busca contratos usando la API (para fechas futuras)"""
    import requests
    
    url = "https://api.polygon.io/v3/reference/options/contracts"
    fecha_venc_str = fecha_vencimiento.strftime('%Y-%m-%d')
    
    # Buscar con rango de ±7 días
    params = {
        'underlying_ticker': ticker,
        'contract_type': 'put',
        'expiration_date.gte': (fecha_vencimiento - timedelta(days=7)).strftime('%Y-%m-%d'),
        'expiration_date.lte': (fecha_vencimiento + timedelta(days=7)).strftime('%Y-%m-%d'),
        'limit': 250,
        'apiKey': API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
    except:
        pass
    
    return []


def generar_contratos_manual(ticker, fecha_vencimiento, precio_stock):
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
    
    return contratos


def crear_resultado_vacio(mensaje):
    """Crea un resultado vacío con mensaje"""
    return {
        'ganancia_pct': 0,
        'ganancia_dia_siguiente': 0,
        'exito': '❌',
        'exito_dia2': '❌',
        'strike': 0,
        'prima_entrada': 0,
        'prima_maxima': 0,
        'prima_maxima_dia2': 0,
        'mensaje': mensaje
    }


# Importar las funciones necesarias
from datetime import timedelta

def calcular_fecha_vencimiento(fecha_senal, ticker):
    """Calcula la fecha de vencimiento correcta para el ticker"""
    rango = RANGOS_PRIMA.get(ticker, {})
    tipo_vencimiento = rango.get('vencimiento', 'viernes')
    
    if tipo_vencimiento == 'siguiente_dia':
        # D+1 para SPY/QQQ
        fecha_venc = fecha_senal + timedelta(days=1)
        while fecha_venc.weekday() >= 5:  # Skip weekends
            fecha_venc += timedelta(days=1)
    else:
        # Próximo viernes para otros
        dias_hasta_viernes = (4 - fecha_senal.weekday()) % 7
        if dias_hasta_viernes == 0:
            dias_hasta_viernes = 7
        fecha_venc = fecha_senal + timedelta(days=dias_hasta_viernes)
    
    return fecha_venc

# Copiar RANGOS_PRIMA del archivo original
RANGOS_PRIMA = {
    'SPY': {'min': 0.25, 'max': 0.30, 'vencimiento': 'siguiente_dia'},
    'QQQ': {'min': 0.25, 'max': 0.30, 'vencimiento': 'siguiente_dia'},
    # ... resto de tickers
}