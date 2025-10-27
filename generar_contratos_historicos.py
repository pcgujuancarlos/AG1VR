def generar_contratos_historicos(ticker, fecha_vencimiento, precio_stock):
    """
    Genera manualmente los contratos de opciones para fechas históricas
    cuando la API no los devuelve
    """
    contratos = []
    
    # Formato del ticker de opción: O:SPY241022P00580000
    # O: = Opción
    # SPY = Ticker subyacente
    # 241022 = Fecha YYMMDD
    # P = Put (C = Call)
    # 00580000 = Strike * 1000 (580.00 -> 00580000)
    
    fecha_str = fecha_vencimiento.strftime('%y%m%d')
    
    # Generar strikes alrededor del precio actual
    # Para PUT, queremos strikes por debajo y cerca del precio
    
    # Calcular rango de strikes (desde 10% ITM hasta 5% OTM)
    strike_min = int(precio_stock * 0.90)  # 10% ITM
    strike_max = int(precio_stock * 1.05)  # 5% OTM
    
    # Generar strikes cada $1 para SPY/QQQ, cada $5 para otros
    if ticker in ['SPY', 'QQQ']:
        step = 1
    else:
        step = 5
    
    print(f"🔧 Generando contratos para {ticker} vencimiento {fecha_vencimiento.strftime('%Y-%m-%d')}")
    print(f"   Precio stock: ${precio_stock:.2f}")
    print(f"   Rango strikes: ${strike_min} - ${strike_max}")
    
    for strike in range(strike_min, strike_max + 1, step):
        # Construir el ticker de la opción
        option_ticker = f"O:{ticker}{fecha_str}P{strike*1000:08d}"
        
        contrato = {
            'ticker': option_ticker,
            'underlying_ticker': ticker,
            'contract_type': 'put',
            'expiration_date': fecha_vencimiento.strftime('%Y-%m-%d'),
            'strike_price': strike,
            'generado_manualmente': True
        }
        
        contratos.append(contrato)
    
    print(f"✅ Generados {len(contratos)} contratos")
    
    # Mostrar algunos ejemplos
    if contratos:
        print("📋 Ejemplos:")
        for c in contratos[::10]:  # Cada 10 contratos
            print(f"   - {c['ticker']} (Strike: ${c['strike_price']})")
    
    return contratos