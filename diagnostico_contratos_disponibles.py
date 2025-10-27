"""
Diagnóstico para ver qué contratos están realmente disponibles en Polygon
"""
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')

def explorar_contratos_disponibles():
    """Explora qué contratos están disponibles en Polygon"""
    
    print("\n" + "="*60)
    print("EXPLORANDO CONTRATOS DISPONIBLES EN POLYGON")
    print("="*60)
    
    url = "https://api.polygon.io/v3/reference/options/contracts"
    
    # 1. Buscar CUALQUIER contrato de SPY sin filtrar por fecha
    print("\n1️⃣ Buscando TODOS los contratos PUT de SPY (sin filtro de fecha)...")
    
    params = {
        'underlying_ticker': 'SPY',
        'contract_type': 'put',
        'limit': 20,
        'apiKey': API_KEY,
        'order': 'asc',
        'sort': 'expiration_date'
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        contratos = data.get('results', [])
        
        if contratos:
            print(f"✅ Encontrados {len(contratos)} contratos")
            print("\n📅 Fechas de vencimiento disponibles:")
            
            fechas_unicas = sorted(set(c['expiration_date'] for c in contratos))
            for fecha in fechas_unicas[:10]:
                print(f"   - {fecha}")
            
            # Mostrar detalles del primer contrato
            primer_contrato = contratos[0]
            print(f"\n📋 Ejemplo de contrato:")
            print(f"   Ticker: {primer_contrato['ticker']}")
            print(f"   Strike: ${primer_contrato['strike_price']}")
            print(f"   Vencimiento: {primer_contrato['expiration_date']}")
            
            # Ahora intentar obtener datos históricos de este contrato
            print(f"\n2️⃣ Intentando obtener datos de precios para {primer_contrato['ticker']}...")
            
            from polygon import RESTClient
            client = RESTClient(API_KEY)
            
            # Probar diferentes fechas
            fechas_prueba = [
                datetime(2024, 10, 21),
                datetime(2024, 10, 18),
                datetime(2024, 10, 1),
                datetime(2024, 9, 1),
                datetime.now() - timedelta(days=1)
            ]
            
            for fecha in fechas_prueba:
                fecha_str = fecha.strftime('%Y-%m-%d')
                print(f"\n   Probando fecha {fecha_str}...")
                
                try:
                    aggs = client.get_aggs(
                        ticker=primer_contrato['ticker'],
                        multiplier=1,
                        timespan="day",
                        from_=fecha_str,
                        to=fecha_str,
                        limit=5
                    )
                    
                    if aggs:
                        print(f"   ✅ Datos encontrados: Precio ~${aggs[0].close:.2f}")
                        break
                    else:
                        print(f"   ❌ Sin datos")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    
        else:
            print("❌ No se encontraron contratos")
    else:
        print(f"❌ Error API: {response.status_code}")
        print(f"Respuesta: {response.text}")
    
    # 3. Buscar contratos con fechas específicas de 2024
    print("\n3️⃣ Buscando contratos históricos específicos de 2024...")
    
    # Construir ticker manualmente para una fecha conocida
    # Formato: O:SPY241018P00580000 = SPY Oct 18 2024 PUT $580
    tickers_prueba = [
        "O:SPY241018P00580000",  # 18 oct 2024
        "O:SPY241021P00580000",  # 21 oct 2024
        "O:SPY241022P00580000",  # 22 oct 2024
        "O:SPY241025P00580000",  # 25 oct 2024
    ]
    
    from polygon import RESTClient
    client = RESTClient(API_KEY)
    
    for ticker_opcion in tickers_prueba:
        print(f"\n🔍 Probando {ticker_opcion}...")
        
        try:
            # Intentar obtener datos del 21 de octubre 2024
            aggs = client.get_aggs(
                ticker=ticker_opcion,
                multiplier=1,
                timespan="minute",
                from_="2024-10-21",
                to="2024-10-21",
                limit=10
            )
            
            if aggs:
                precios = [agg.close for agg in aggs[:5]]
                print(f"   ✅ DATOS ENCONTRADOS!")
                print(f"   Precios muestra: {[f'${p:.2f}' for p in precios]}")
                print(f"   Rango: ${min(precios):.2f} - ${max(precios):.2f}")
            else:
                print(f"   ❌ Sin datos de precios")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    explorar_contratos_disponibles()