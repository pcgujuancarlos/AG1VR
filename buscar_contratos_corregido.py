def buscar_contratos_disponibles(client, ticker, fecha_vencimiento, fecha_analisis=None):
    """
    Busca contratos de opciones PUT disponibles
    IMPORTANTE: Debe buscar contratos que EXISTÍAN en la fecha de análisis
    """
    import requests
    from datetime import datetime, timedelta
    
    fecha_venc_str = fecha_vencimiento.strftime('%Y-%m-%d')
    
    # Si tenemos fecha de análisis, buscar contratos que existían en ese momento
    if fecha_analisis:
        fecha_analisis_str = fecha_analisis.strftime('%Y-%m-%d')
        print(f"🔍 Buscando contratos que existían el {fecha_analisis_str}")
    
    # URL de la API v3 de Polygon
    url = "https://api.polygon.io/v3/reference/options/contracts"
    
    # IMPORTANTE: Para fechas históricas (2024), necesitamos buscar 
    # contratos que vencían en ese período, no en el futuro
    if fecha_analisis and fecha_analisis.year < 2025:
        # Para análisis histórico: buscar contratos del mismo año
        print(f"📅 Análisis histórico detectado: buscando contratos de {fecha_analisis.year}")
        
        # Ajustar fecha de vencimiento al mismo año que el análisis
        fecha_venc_ajustada = fecha_vencimiento.replace(year=fecha_analisis.year)
        
        # Si la fecha ajustada ya pasó, buscar la siguiente semana
        if fecha_venc_ajustada < fecha_analisis:
            # Para SPY/QQQ buscar vencimientos diarios
            if ticker in ['SPY', 'QQQ']:
                fecha_venc_ajustada = fecha_analisis + timedelta(days=1)
                while fecha_venc_ajustada.weekday() >= 5:
                    fecha_venc_ajustada += timedelta(days=1)
            else:
                # Para otros, buscar el próximo viernes
                dias_hasta_viernes = (4 - fecha_analisis.weekday()) % 7
                if dias_hasta_viernes == 0:
                    dias_hasta_viernes = 7
                fecha_venc_ajustada = fecha_analisis + timedelta(days=dias_hasta_viernes)
        
        fecha_venc_str = fecha_venc_ajustada.strftime('%Y-%m-%d')
        print(f"📆 Fecha de vencimiento ajustada: {fecha_venc_str}")
    
    # Buscar con rango de fechas para mayor flexibilidad
    fecha_desde = (datetime.strptime(fecha_venc_str, '%Y-%m-%d') - timedelta(days=3)).strftime('%Y-%m-%d')
    fecha_hasta = (datetime.strptime(fecha_venc_str, '%Y-%m-%d') + timedelta(days=3)).strftime('%Y-%m-%d')
    
    params = {
        'underlying_ticker': ticker,
        'contract_type': 'put',
        'expiration_date.gte': fecha_desde,
        'expiration_date.lte': fecha_hasta,
        'limit': 250,
        'apiKey': API_KEY,
        'order': 'asc',
        'sort': 'strike_price'
    }
    
    try:
        print(f"🌐 Consultando API de Polygon...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error API: {response.status_code}")
            # Intento alternativo: buscar cualquier contrato PUT reciente
            params_alt = {
                'underlying_ticker': ticker,
                'contract_type': 'put',
                'limit': 100,
                'apiKey': API_KEY,
                'order': 'asc',
                'sort': 'expiration_date'
            }
            response = requests.get(url, params=params_alt, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            contratos = data.get('results', [])
            
            if contratos:
                # Filtrar por fechas relevantes
                contratos_filtrados = []
                for c in contratos:
                    exp_date = datetime.strptime(c['expiration_date'], '%Y-%m-%d')
                    
                    # Para análisis histórico, solo usar contratos del mismo año
                    if fecha_analisis and fecha_analisis.year < 2025:
                        if exp_date.year == fecha_analisis.year and exp_date >= fecha_analisis:
                            contratos_filtrados.append(c)
                    else:
                        contratos_filtrados.append(c)
                
                if contratos_filtrados:
                    fechas_unicas = sorted(set(c['expiration_date'] for c in contratos_filtrados))
                    print(f"✅ Encontrados {len(contratos_filtrados)} contratos")
                    print(f"📅 Vencimientos disponibles: {', '.join(fechas_unicas[:3])}")
                    return contratos_filtrados
                else:
                    print(f"⚠️ No hay contratos para el período {fecha_analisis.year if fecha_analisis else 'actual'}")
            
            return []
        
    except Exception as e:
        print(f"❌ Error buscando contratos: {str(e)}")
    
    return []