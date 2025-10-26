def calcular_ganancia_real_opcion_v3(client, ticker, fecha, precio_stock):
    """
    NUEVA ESTRATEGIA: Buscar el strike que ofrece MAYOR GANANCIA PORCENTUAL
    dentro del rango de primas configurado
    """
    try:
        if ticker not in RANGOS_PRIMA:
            return crear_resultado_vacio('Sin rango definido')
        
        rango = RANGOS_PRIMA[ticker]
        fecha_vencimiento = calcular_fecha_vencimiento(fecha, ticker)
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        print(f"\n=== NUEVA ESTRATEGIA: BUSCANDO MAYOR GANANCIA % ===")
        print(f"Ticker: {ticker}")
        print(f"Fecha: {fecha_str}")
        print(f"Precio stock: ${precio_stock:.2f}")
        print(f"Rango prima objetivo: ${rango['min']:.2f} - ${rango['max']:.2f}")
        
        # Generar contratos
        if fecha.year >= 2025:
            contratos = buscar_contratos_api_v2(client, ticker, fecha_vencimiento)
            if not contratos:
                contratos = generar_contratos_historicos_v2(ticker, fecha_vencimiento, precio_stock)
        else:
            contratos = generar_contratos_historicos_v2(ticker, fecha_vencimiento, precio_stock)
        
        if not contratos:
            return crear_resultado_vacio('Sin contratos')
        
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
                            # Calcular ganancia máxima posible
                            ganancia_maxima_pct = ((max_precio - prima_entrada) / prima_entrada * 100)
                            
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
            return crear_resultado_vacio('Sin primas en rango')
        
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
        
        # Calcular ganancia día 2
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
                limit=500
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
        
        return {
            'ganancia_pct': round(mejor['ganancia_pct'], 1),
            'ganancia_dia_siguiente': round(ganancia_dia2, 1),
            'exito': '✅' if mejor['ganancia_pct'] >= 100 else '❌',
            'exito_dia2': '✅' if ganancia_dia2 >= 100 else '❌',
            'strike': mejor_contrato['strike_price'],
            'prima_entrada': round(prima_entrada, 2),
            'prima_maxima': round(mejor['prima_maxima'], 2),
            'prima_maxima_dia2': round(prima_maxima_dia2, 2),
            'mensaje': f"Strike ${mejor_contrato['strike_price']} - Mejor ganancia: {mejor['ganancia_pct']:.1f}%"
        }
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return crear_resultado_vacio(f'Error: {str(e)}')

# Funciones auxiliares necesarias
def crear_resultado_vacio(mensaje):
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