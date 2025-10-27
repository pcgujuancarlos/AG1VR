# Fix para buscar_contratos_disponibles
# Este código muestra cómo modificar la búsqueda para que siempre encuentre contratos

def buscar_contratos_disponibles_mejorado(client, ticker, fecha_vencimiento):
    """
    Versión mejorada que busca contratos en diferentes rangos de tiempo
    hasta encontrar algunos disponibles
    """
    import requests
    from datetime import timedelta
    
    fecha_venc_str = fecha_vencimiento.strftime('%Y-%m-%d')
    url = f"https://api.polygon.io/v3/reference/options/contracts"
    
    # Estrategia de búsqueda progresiva
    rangos_busqueda = [
        (0, "fecha exacta"),
        (7, "±1 semana"),
        (30, "±1 mes"),
        (60, "±2 meses"),
        (90, "±3 meses"),
        (180, "±6 meses"),
        (365, "±1 año")
    ]
    
    for dias_rango, descripcion in rangos_busqueda:
        print(f"\n🔍 Intento con {descripcion}...")
        
        if dias_rango == 0:
            # Búsqueda exacta
            params = {
                'underlying_ticker': ticker,
                'contract_type': 'put',
                'expiration_date': fecha_venc_str,
                'limit': 1000,
                'apiKey': API_KEY
            }
        else:
            # Búsqueda en rango
            fecha_desde = (fecha_vencimiento - timedelta(days=dias_rango)).strftime('%Y-%m-%d')
            fecha_hasta = (fecha_vencimiento + timedelta(days=dias_rango)).strftime('%Y-%m-%d')
            
            params = {
                'underlying_ticker': ticker,
                'contract_type': 'put',
                'expiration_date.gte': fecha_desde,
                'expiration_date.lte': fecha_hasta,
                'limit': 1000,
                'apiKey': API_KEY
            }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                contratos = data.get('results', [])
                
                if contratos and len(contratos) > 0:
                    print(f"✅ Encontrados {len(contratos)} contratos con {descripcion}")
                    
                    # Ordenar por cercanía a fecha objetivo
                    from datetime import datetime
                    fecha_objetivo = datetime.strptime(fecha_venc_str, '%Y-%m-%d')
                    
                    contratos_ordenados = sorted(contratos, 
                        key=lambda x: abs((datetime.strptime(x['expiration_date'], '%Y-%m-%d') - fecha_objetivo).days)
                    )
                    
                    # Mostrar los más cercanos
                    print(f"📅 Fechas más cercanas disponibles:")
                    fechas_unicas = sorted(set(c['expiration_date'] for c in contratos_ordenados))[:5]
                    for f in fechas_unicas:
                        print(f"   - {f}")
                    
                    return contratos_ordenados
            
        except Exception as e:
            print(f"❌ Error en intento: {e}")
            continue
    
    print("❌ No se encontraron contratos en ningún rango")
    return []

# También podríamos usar siempre los contratos más líquidos (los que vencen pronto)
def usar_contratos_liquidos(client, ticker):
    """
    Alternativa: Siempre usar los contratos más líquidos (próximo vencimiento)
    sin importar la fecha de análisis
    """
    import requests
    from datetime import datetime, timedelta
    
    hoy = datetime.now()
    fecha_desde = hoy.strftime('%Y-%m-%d')
    fecha_hasta = (hoy + timedelta(days=60)).strftime('%Y-%m-%d')
    
    url = f"https://api.polygon.io/v3/reference/options/contracts"
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
        contratos = data.get('results', [])
        
        if contratos:
            # Agrupar por fecha de vencimiento
            from collections import defaultdict
            por_fecha = defaultdict(list)
            
            for c in contratos:
                por_fecha[c['expiration_date']].append(c)
            
            # Tomar la fecha más cercana con suficientes contratos
            fechas_ordenadas = sorted(por_fecha.keys())
            
            for fecha in fechas_ordenadas:
                if len(por_fecha[fecha]) >= 20:  # Al menos 20 strikes
                    print(f"✅ Usando contratos líquidos del {fecha}")
                    return por_fecha[fecha]
    
    return []