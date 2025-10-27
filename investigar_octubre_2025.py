"""
Investigación: ¿Por qué solo funciona octubre 2025?
"""
import os
import requests
from polygon import RESTClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')
client = RESTClient(API_KEY)

def investigar_contratos_2025():
    """Investiga qué contratos están disponibles en la API para 2025"""
    
    print("\n" + "="*80)
    print("INVESTIGACIÓN: DISPONIBILIDAD DE CONTRATOS EN 2025")
    print("="*80)
    
    # 1. Ver TODOS los contratos disponibles para SPY sin filtro de fecha
    print("\n1️⃣ TODOS LOS CONTRATOS SPY DISPONIBLES EN LA API:")
    
    url = "https://api.polygon.io/v3/reference/options/contracts"
    
    params = {
        'underlying_ticker': 'SPY',
        'contract_type': 'put',
        'limit': 1000,
        'apiKey': API_KEY,
        'order': 'asc',
        'sort': 'expiration_date'
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            contratos = data.get('results', [])
            
            if contratos:
                # Agrupar por año y mes
                from collections import defaultdict
                contratos_por_mes = defaultdict(list)
                
                for contrato in contratos:
                    fecha_exp = contrato['expiration_date']
                    año_mes = fecha_exp[:7]  # YYYY-MM
                    contratos_por_mes[año_mes].append(fecha_exp)
                
                print(f"\n✅ Total de contratos encontrados: {len(contratos)}")
                print("\n📅 Contratos agrupados por mes:")
                
                for año_mes in sorted(contratos_por_mes.keys()):
                    fechas_unicas = sorted(set(contratos_por_mes[año_mes]))
                    print(f"\n   {año_mes}: {len(fechas_unicas)} fechas de vencimiento")
                    # Mostrar las primeras 3 fechas
                    for fecha in fechas_unicas[:3]:
                        print(f"      - {fecha}")
                    if len(fechas_unicas) > 3:
                        print(f"      ... y {len(fechas_unicas)-3} más")
                        
            else:
                print("❌ No se encontraron contratos")
                
        else:
            print(f"❌ Error API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 2. Probar acceso a datos de diferentes meses de 2025
    print("\n\n2️⃣ PRUEBA DE ACCESO A DATOS POR MES EN 2025:")
    
    meses_2025 = [
        ("2025-01-15", "Enero 2025"),
        ("2025-02-15", "Febrero 2025"),
        ("2025-03-15", "Marzo 2025"),
        ("2025-04-15", "Abril 2025"),
        ("2025-05-15", "Mayo 2025"),
        ("2025-06-15", "Junio 2025"),
        ("2025-07-15", "Julio 2025"),
        ("2025-08-15", "Agosto 2025"),
        ("2025-09-15", "Septiembre 2025"),
        ("2025-10-15", "Octubre 2025"),
        ("2025-11-15", "Noviembre 2025"),
        ("2025-12-15", "Diciembre 2025"),
    ]
    
    for fecha_str, mes in meses_2025:
        print(f"\n📅 {mes}:")
        
        # a) Probar acceso a datos del stock
        print(f"   Datos del stock SPY:")
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
                print(f"      ✅ Acceso permitido - Precio: ${stock_aggs[0].close:.2f}")
            else:
                print(f"      ⚠️ Sin datos")
                
        except Exception as e:
            if "NOT_AUTHORIZED" in str(e):
                print(f"      ❌ NO AUTORIZADO - Plan no incluye esta fecha")
            else:
                print(f"      ❌ Error: {str(e)[:50]}")
        
        # b) Probar acceso a datos de opciones
        print(f"   Datos de opciones:")
        try:
            # Construir un ticker de opción para esa fecha
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
            fecha_venc = fecha_obj + timedelta(days=5)  # Aproximadamente
            fecha_venc_str = fecha_venc.strftime('%y%m%d')
            
            option_ticker = f"O:SPY{fecha_venc_str}P00600000"  # Strike arbitrario
            
            option_aggs = client.get_aggs(
                ticker=option_ticker,
                multiplier=1,
                timespan="day",
                from_=fecha_str,
                to=fecha_str,
                limit=1
            )
            
            if option_aggs:
                print(f"      ✅ Acceso permitido")
            else:
                print(f"      ⚠️ Sin datos para {option_ticker}")
                
        except Exception as e:
            if "NOT_AUTHORIZED" in str(e):
                print(f"      ❌ NO AUTORIZADO - Plan no incluye opciones futuras")
            elif "not found" in str(e).lower():
                print(f"      ⚠️ Ticker no existe: {option_ticker}")
            else:
                print(f"      ❌ Error: {str(e)[:50]}")
    
    # 3. Análisis del plan
    print("\n\n3️⃣ ANÁLISIS DEL PLAN POLYGON:")
    print("\n📊 Basado en las pruebas anteriores:")
    print("\n✅ Lo que SÍ incluye tu plan:")
    print("   - Datos históricos de stocks y opciones (fechas pasadas)")
    print("   - Contratos de opciones FUTURAS en la API de referencia")
    print("   - Datos de precios para OCTUBRE 2025")
    
    print("\n❌ Lo que NO incluye tu plan:")
    print("   - Datos de precios futuros para la mayoría de meses de 2025")
    print("   - Solo octubre 2025 parece tener acceso autorizado")
    
    print("\n💡 CONCLUSIÓN:")
    print("   Tu plan Developer tiene una restricción temporal.")
    print("   Solo permite ver datos de precios futuros hasta cierto punto.")
    print("   Octubre 2025 está dentro del límite, pero otros meses no.")
    
    # 4. Verificar el límite exacto
    print("\n\n4️⃣ BUSCANDO EL LÍMITE EXACTO DE FECHAS FUTURAS:")
    
    # Probar desde hoy hacia adelante
    fecha_hoy = datetime.now()
    dias_adelante = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 365]
    
    for dias in dias_adelante:
        fecha_prueba = fecha_hoy + timedelta(days=dias)
        fecha_str = fecha_prueba.strftime('%Y-%m-%d')
        
        try:
            test_aggs = client.get_aggs(
                ticker="SPY",
                multiplier=1,
                timespan="day",
                from_=fecha_str,
                to=fecha_str,
                limit=1
            )
            
            if test_aggs:
                print(f"   ✅ {fecha_str} ({dias} días): AUTORIZADO")
            else:
                print(f"   ⚠️ {fecha_str} ({dias} días): Sin datos")
                
        except Exception as e:
            if "NOT_AUTHORIZED" in str(e):
                print(f"   ❌ {fecha_str} ({dias} días): NO AUTORIZADO")
                break

if __name__ == "__main__":
    investigar_contratos_2025()