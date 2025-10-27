def calcular_ganancia_real_opcion_NUEVA(client, ticker, fecha, precio_stock):
    """
    NUEVA LÓGICA: Busca por prima en rango + vencimiento → el strike sale automáticamente
    """
    try:
        if ticker not in RANGOS_PRIMA:
            return {'ganancia_pct': 0, 'mensaje': 'Sin rango'}
        
        rango = RANGOS_PRIMA[ticker]
        fecha_vencimiento = calcular_fecha_vencimiento(fecha, ticker)
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        print(f"\n=== BUSCANDO OPCIÓN PARA {ticker} ===")
        print(f"Fecha análisis: {fecha_str}")
        print(f"Precio stock: ${precio_stock:.2f}")
        print(f"Vencimiento objetivo: {fecha_vencimiento.strftime('%Y-%m-%d')}")
        print(f"Rango de prima buscado: ${rango['min']:.2f} - ${rango['max']:.2f}")
        
        # PASO 1: Buscar TODOS los contratos PUT del vencimiento
        contratos = buscar_contratos_disponibles(client, ticker, fecha_vencimiento)
        
        if not contratos:
            return {'ganancia_pct': 0, 'mensaje': 'Sin contratos'}
        
        print(f"\n✅ Encontrados {len(contratos)} contratos PUT")
        
        # PASO 2: Para cada contrato, obtener su prima actual/histórica
        contratos_con_prima = []
        
        for contrato in contratos:
            option_ticker = contrato['ticker']
            strike = contrato['strike_price']
            
            # Obtener datos de precios del día
            try:
                option_aggs = client.get_aggs(
                    ticker=option_ticker,
                    multiplier=30,  # 30 minutos
                    timespan="minute",
                    from_=fecha_str,
                    to=fecha_str,
                    limit=50000
                )
                
                if option_aggs and len(option_aggs) > 0:
                    # Buscar primas en TODOS los momentos del día
                    for agg in option_aggs:
                        # Verificar cada precio (open, high, low, close)
                        precios = [agg.open, agg.high, agg.low, agg.close]
                        
                        for precio in precios:
                            # Si la prima está en el rango, guardar
                            if rango['min'] <= precio <= rango['max']:
                                contratos_con_prima.append({
                                    'ticker': option_ticker,
                                    'strike': strike,
                                    'prima': precio,
                                    'timestamp': agg.timestamp,
                                    'distancia_otm': ((strike - precio_stock) / precio_stock) * 100
                                })
                                break  # Ya encontramos una prima válida para este contrato
                        
                        if contratos_con_prima and contratos_con_prima[-1]['ticker'] == option_ticker:
                            break  # Ya tenemos prima para este contrato, siguiente
                
            except Exception as e:
                print(f"⚠️ Error obteniendo datos de {option_ticker}: {e}")
                continue
        
        # PASO 3: Seleccionar el mejor contrato (con prima en rango)
        if not contratos_con_prima:
            print(f"❌ No se encontraron contratos con prima en el rango ${rango['min']:.2f}-${rango['max']:.2f}")
            
            # FALLBACK: Buscar la prima más cercana al rango
            todas_las_primas = []
            for contrato in contratos[:10]:  # Revisar los primeros 10 strikes
                option_ticker = contrato['ticker']
                strike = contrato['strike_price']
                
                try:
                    option_aggs = client.get_aggs(
                        ticker=option_ticker,
                        multiplier=30,
                        timespan="minute", 
                        from_=fecha_str,
                        to=fecha_str,
                        limit=100
                    )
                    
                    if option_aggs:
                        for agg in option_aggs:
                            todas_las_primas.append({
                                'ticker': option_ticker,
                                'strike': strike,
                                'prima': agg.close,  # Usar precio de cierre
                                'distancia_otm': ((strike - precio_stock) / precio_stock) * 100
                            })
                            break  # Solo necesitamos un precio por contrato
                except:
                    continue
            
            if todas_las_primas:
                # Ordenar por cercanía al rango
                rango_medio = (rango['min'] + rango['max']) / 2
                todas_las_primas.sort(key=lambda x: abs(x['prima'] - rango_medio))
                
                mejor_contrato = todas_las_primas[0]
                print(f"⚠️ Usando prima más cercana: ${mejor_contrato['prima']:.2f} (fuera de rango)")
            else:
                return {'ganancia_pct': 0, 'mensaje': 'Sin datos de primas'}
        else:
            # Ordenar por cercanía al centro del rango
            rango_medio = (rango['min'] + rango['max']) / 2
            contratos_con_prima.sort(key=lambda x: abs(x['prima'] - rango_medio))
            
            mejor_contrato = contratos_con_prima[0]
            print(f"✅ Contrato seleccionado:")
            print(f"   Ticker: {mejor_contrato['ticker']}")
            print(f"   Strike: ${mejor_contrato['strike']:.2f}")
            print(f"   Prima: ${mejor_contrato['prima']:.2f}")
            print(f"   Distancia OTM: {mejor_contrato['distancia_otm']:.1f}%")
        
        # PASO 4: Calcular ganancias con el contrato seleccionado
        option_ticker = mejor_contrato['ticker']
        prima_entrada = mejor_contrato['prima']
        strike_real = mejor_contrato['strike']
        
        # Obtener prima máxima del día
        try:
            option_aggs_dia1 = client.get_aggs(
                ticker=option_ticker,
                multiplier=30,
                timespan="minute",
                from_=fecha_str,
                to=fecha_str,
                limit=50000
            )
            
            if option_aggs_dia1:
                prima_maxima_dia1 = max([agg.high for agg in option_aggs_dia1])
                ganancia_dia1 = ((prima_maxima_dia1 - prima_entrada) / prima_entrada) * 100
            else:
                prima_maxima_dia1 = prima_entrada
                ganancia_dia1 = 0
                
        except:
            prima_maxima_dia1 = prima_entrada
            ganancia_dia1 = 0
        
        print(f"\n📊 RESULTADOS:")
        print(f"  Prima entrada: ${prima_entrada:.2f}")
        print(f"  Prima máxima día 1: ${prima_maxima_dia1:.2f}")
        print(f"  Ganancia día 1: {ganancia_dia1:.1f}%")
        
        return {
            'ganancia_pct': round(ganancia_dia1, 1),
            'strike': strike_real,
            'prima_entrada': prima_entrada,
            'prima_maxima': prima_maxima_dia1,
            'exito': '✅' if ganancia_dia1 >= 100 else '❌',
            'mensaje': f'Strike: ${strike_real:.2f}'
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {'ganancia_pct': 0, 'mensaje': f'Error: {str(e)}'}