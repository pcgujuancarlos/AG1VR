"""
Diagnóstico completo para entender por qué solo funciona en octubre 2025
"""
import os
from polygon import RESTClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')
client = RESTClient(API_KEY)

def diagnosticar_todas_fechas():
    """Prueba con múltiples fechas para entender el patrón"""
    
    print("\n" + "="*80)
    print("DIAGNÓSTICO COMPLETO: ¿POR QUÉ SOLO FUNCIONA EN OCTUBRE 2025?")
    print("="*80)
    
    # Probar con diferentes fechas
    fechas_prueba = [
        # Fechas futuras (2025)
        ("2025-10-21", "Octubre 2025 - FUTURO"),
        ("2025-11-21", "Noviembre 2025 - FUTURO"),
        ("2025-09-21", "Septiembre 2025 - FUTURO"),
        ("2025-12-21", "Diciembre 2025 - FUTURO"),
        
        # Fechas pasadas (2024)
        ("2024-10-21", "Octubre 2024 - PASADO"),
        ("2024-11-21", "Noviembre 2024 - PASADO"),
        ("2024-09-20", "Septiembre 2024 - PASADO"),
        
        # Fecha actual
        (datetime.now().strftime('%Y-%m-%d'), "HOY"),
    ]
    
    for fecha_str, descripcion in fechas_prueba:
        print(f"\n{'='*60}")
        print(f"PROBANDO: {descripcion} - {fecha_str}")
        print(f"{'='*60}")
        
        # 1. Verificar datos del stock
        print("\n1️⃣ Datos del stock SPY:")
        try:
            stock_aggs = client.get_aggs(
                ticker="SPY",
                multiplier=1,
                timespan="day",
                from_=fecha_str,
                to=fecha_str,
                limit=1
            )
            
            if stock_aggs:
                precio = stock_aggs[0].close
                print(f"   ✅ Precio SPY: ${precio:.2f}")
            else:
                print(f"   ❌ Sin datos del stock")
                precio = 580  # Precio aproximado
        except Exception as e:
            print(f"   ❌ Error: {e}")
            precio = 580
        
        # 2. Buscar contratos disponibles en la API
        print("\n2️⃣ Contratos en API de referencia:")
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        
        # Para SPY, vencimiento es D+1
        fecha_venc = fecha_obj + timedelta(days=1)
        while fecha_venc.weekday() >= 5:
            fecha_venc += timedelta(days=1)
        
        url = "https://api.polygon.io/v3/reference/options/contracts"
        
        # Buscar con rango amplio
        params = {
            'underlying_ticker': 'SPY',
            'contract_type': 'put',
            'expiration_date.gte': (fecha_venc - timedelta(days=7)).strftime('%Y-%m-%d'),
            'expiration_date.lte': (fecha_venc + timedelta(days=7)).strftime('%Y-%m-%d'),
            'limit': 100,
            'apiKey': API_KEY
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                contratos = data.get('results', [])
                
                if contratos:
                    fechas_venc = sorted(set(c['expiration_date'] for c in contratos))
                    print(f"   ✅ {len(contratos)} contratos encontrados")
                    print(f"   📅 Vencimientos: {', '.join(fechas_venc[:3])}")
                else:
                    print(f"   ❌ Sin contratos en API")
            else:
                print(f"   ❌ Error API: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 3. Probar obtener datos de una opción específica
        print("\n3️⃣ Datos de opciones (ticker construido):")
        
        # Construir ticker manualmente
        strike = int(precio * 0.99)  # 1% OTM
        fecha_venc_str = fecha_venc.strftime('%y%m%d')
        option_ticker = f"O:SPY{fecha_venc_str}P{strike*1000:08d}"
        
        print(f"   🎯 Probando: {option_ticker}")
        print(f"   📅 Fecha análisis: {fecha_str}")
        
        try:
            option_aggs = client.get_aggs(
                ticker=option_ticker,
                multiplier=1,
                timespan="minute",
                from_=fecha_str,
                to=fecha_str,
                limit=10
            )
            
            if option_aggs:
                precios = [agg.close for agg in option_aggs[:5]]
                print(f"   ✅ Datos encontrados!")
                print(f"   💰 Precios muestra: {[f'${p:.2f}' for p in precios]}")
            else:
                print(f"   ❌ Sin datos de precios")
                
                # Intentar con diferentes strikes
                print("\n   🔄 Probando otros strikes:")
                strikes_prueba = [
                    int(precio * 0.97),
                    int(precio * 0.98),
                    int(precio),
                    int(precio * 1.01),
                    int(precio * 1.02)
                ]
                
                for strike_test in strikes_prueba[:2]:
                    option_ticker_test = f"O:SPY{fecha_venc_str}P{strike_test*1000:08d}"
                    try:
                        test_aggs = client.get_aggs(
                            ticker=option_ticker_test,
                            multiplier=1,
                            timespan="day",
                            from_=fecha_str,
                            to=fecha_str,
                            limit=1
                        )
                        if test_aggs:
                            print(f"      ✅ Strike ${strike_test}: Precio ${test_aggs[0].close:.2f}")
                            break
                        else:
                            print(f"      ❌ Strike ${strike_test}: Sin datos")
                    except:
                        pass
                        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN Y CONCLUSIONES")
    print("="*80)
    print("\n⚠️ PROBLEMAS IDENTIFICADOS:")
    print("1. La API de contratos solo muestra opciones FUTURAS (no históricas)")
    print("2. Para fechas pasadas, necesitamos construir los tickers manualmente")
    print("3. No todos los contratos tienen datos de precios disponibles")
    print("4. El código actual mezcla lógicas y no maneja bien todos los casos")
    
    print("\n✅ SOLUCIÓN PROPUESTA:")
    print("1. Detectar si es fecha pasada o futura")
    print("2. Para fechas pasadas: generar contratos y probar cuáles tienen datos")
    print("3. Para fechas futuras: usar la API de contratos")
    print("4. Implementar cache de contratos válidos por fecha")

if __name__ == "__main__":
    diagnosticar_todas_fechas()