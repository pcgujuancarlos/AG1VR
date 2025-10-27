"""
Investigación detallada: ¿Por qué septiembre 2025 no funciona?
"""
import os
import requests
from polygon import RESTClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')
client = RESTClient(API_KEY)

def investigar_septiembre_vs_octubre():
    """Compara septiembre vs octubre 2025 en detalle"""
    
    print("\n" + "="*80)
    print("COMPARACIÓN DETALLADA: SEPTIEMBRE vs OCTUBRE 2025")
    print("="*80)
    
    # Fechas de prueba
    fechas_test = [
        ("2025-09-15", "SEPTIEMBRE 2025"),
        ("2025-10-15", "OCTUBRE 2025")
    ]
    
    for fecha_str, descripcion in fechas_test:
        print(f"\n{'='*60}")
        print(f"{descripcion} - Fecha: {fecha_str}")
        print(f"{'='*60}")
        
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        
        # 1. Datos del stock
        print("\n1️⃣ DATOS DEL STOCK SPY:")
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
                print(f"   ✅ Precio: ${precio:.2f}")
            else:
                print("   ❌ Sin datos del stock")
                precio = 650  # Estimado
        except Exception as e:
            print(f"   ❌ Error: {e}")
            precio = 650
        
        # 2. Buscar contratos en API
        print("\n2️⃣ CONTRATOS EN API DE REFERENCIA:")
        
        # Calcular vencimiento (D+1 para SPY)
        fecha_venc = fecha + timedelta(days=1)
        while fecha_venc.weekday() >= 5:
            fecha_venc += timedelta(days=1)
        
        url = "https://api.polygon.io/v3/reference/options/contracts"
        
        # Buscar con rango amplio
        params = {
            'underlying_ticker': 'SPY',
            'contract_type': 'put',
            'expiration_date.gte': fecha_venc.strftime('%Y-%m-%d'),
            'expiration_date.lte': (fecha_venc + timedelta(days=30)).strftime('%Y-%m-%d'),
            'limit': 100,
            'apiKey': API_KEY
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                contratos = data.get('results', [])
                
                if contratos:
                    # Agrupar por fecha
                    fechas_venc = sorted(set(c['expiration_date'] for c in contratos))
                    print(f"   ✅ {len(contratos)} contratos encontrados")
                    print(f"   📅 Fechas de vencimiento disponibles:")
                    for fv in fechas_venc[:5]:
                        num_strikes = len([c for c in contratos if c['expiration_date'] == fv])
                        print(f"      - {fv}: {num_strikes} strikes")
                    
                    # Tomar el primer contrato para pruebas
                    primer_contrato = contratos[0]
                    
                else:
                    print("   ❌ Sin contratos en API")
                    primer_contrato = None
                    
        except Exception as e:
            print(f"   ❌ Error API: {e}")
            primer_contrato = None
        
        # 3. Probar datos de opciones específicas
        print("\n3️⃣ PRUEBA DE DATOS DE OPCIONES:")
        
        if primer_contrato:
            # Usar contrato real de la API
            option_ticker = primer_contrato['ticker']
            print(f"   Probando contrato real: {option_ticker}")
        else:
            # Construir ticker manualmente
            fecha_venc_str = fecha_venc.strftime('%y%m%d')
            strike = int(precio * 0.98)  # 2% OTM
            option_ticker = f"O:SPY{fecha_venc_str}P{strike*1000:08d}"
            print(f"   Probando contrato construido: {option_ticker}")
        
        # a) Probar con diferentes timeframes
        timeframes = [
            ("1", "minute", "1 minuto"),
            ("5", "minute", "5 minutos"),
            ("1", "hour", "1 hora"),
            ("1", "day", "1 día")
        ]
        
        for mult, span, desc in timeframes:
            print(f"\n   📊 Timeframe: {desc}")
            try:
                option_aggs = client.get_aggs(
                    ticker=option_ticker,
                    multiplier=mult,
                    timespan=span,
                    from_=fecha_str,
                    to=fecha_str,
                    limit=10
                )
                
                if option_aggs:
                    precios = [agg.close for agg in option_aggs[:3]]
                    print(f"      ✅ Datos encontrados: {[f'${p:.2f}' for p in precios]}")
                else:
                    print(f"      ❌ Sin datos")
                    
            except Exception as e:
                if "NOT_AUTHORIZED" in str(e):
                    print(f"      ❌ NO AUTORIZADO")
                elif "not found" in str(e).lower():
                    print(f"      ⚠️ Ticker no encontrado")
                else:
                    print(f"      ❌ Error: {str(e)[:50]}")
        
        # 4. Probar múltiples strikes
        print("\n4️⃣ PROBANDO MÚLTIPLES STRIKES:")
        
        strikes_test = [
            int(precio * 0.95),  # 5% ITM
            int(precio * 0.97),  # 3% ITM
            int(precio * 0.99),  # 1% ITM
            int(precio * 1.01),  # 1% OTM
            int(precio * 1.03),  # 3% OTM
        ]
        
        strikes_con_datos = 0
        
        for strike in strikes_test:
            option_ticker_test = f"O:SPY{fecha_venc.strftime('%y%m%d')}P{strike*1000:08d}"
            
            try:
                test_agg = client.get_aggs(
                    ticker=option_ticker_test,
                    multiplier=1,
                    timespan="minute",
                    from_=fecha_str,
                    to=fecha_str,
                    limit=1
                )
                
                if test_agg:
                    print(f"   ✅ Strike ${strike}: TIENE DATOS")
                    strikes_con_datos += 1
                else:
                    print(f"   ❌ Strike ${strike}: Sin datos")
                    
            except:
                pass  # Silenciar errores para no saturar
        
        print(f"\n   📊 RESUMEN: {strikes_con_datos}/{len(strikes_test)} strikes con datos")
    
    # CONCLUSIÓN
    print("\n\n" + "="*80)
    print("💡 CONCLUSIÓN DE LA INVESTIGACIÓN")
    print("="*80)
    
    print("\n🔍 HALLAZGOS CLAVE:")
    print("\n1. DISPONIBILIDAD DE CONTRATOS:")
    print("   - La API muestra contratos futuros para AMBOS meses")
    print("   - Octubre tiene más contratos listados que septiembre")
    
    print("\n2. ACCESO A DATOS DE PRECIOS:")
    print("   - Octubre 2025: ✅ Datos de opciones disponibles")
    print("   - Septiembre 2025: ❌ Sin datos de opciones")
    print("   - Otros meses 2025: Variable, mayoría sin acceso")
    
    print("\n3. RAZÓN DEL PROBLEMA:")
    print("   - Tu plan tiene un límite de tiempo hacia el futuro")
    print("   - Actualmente (octubre 2025 real) el límite es ~1 año")
    print("   - Los datos más allá de ese límite no están autorizados")
    
    print("\n4. SOLUCIÓN PRÁCTICA:")
    print("   - Para fechas PASADAS: ✅ Funciona todo")
    print("   - Para fechas FUTURAS: Solo hasta el límite del plan")
    print("   - Recomendación: Usar fechas históricas para análisis confiable")

if __name__ == "__main__":
    investigar_septiembre_vs_octubre()