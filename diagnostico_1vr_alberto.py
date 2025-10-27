"""
Diagnóstico específico para los problemas de 1VR reportados por Alberto
Oct 23: GLD y XOM deberían ser 1VR pero no se detectaron
Oct 24: USO NO debería ser 1VR pero sí se detectó
"""
import os
from datetime import datetime
from polygon import RESTClient
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')
client = RESTClient(API_KEY)

def obtener_datos_dia(ticker, fecha):
    """Obtiene datos de un día específico con contexto histórico"""
    try:
        # Necesitamos 30 días antes para calcular indicadores
        fecha_inicio = datetime(2024, 9, 20)  # 30 días antes aprox
        fecha_fin = fecha
        
        aggs = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=fecha_inicio.strftime('%Y-%m-%d'),
            to=fecha_fin.strftime('%Y-%m-%d'),
            limit=50
        )
        
        if not aggs:
            return None
            
        # Convertir a DataFrame
        data = []
        for agg in aggs:
            data.append({
                'fecha': datetime.fromtimestamp(agg.timestamp/1000).date(),
                'open': agg.open,
                'high': agg.high,
                'low': agg.low,
                'close': agg.close,
                'volume': agg.volume
            })
        
        df = pd.DataFrame(data)
        
        # Calcular RSI manualmente
        df['change'] = df['close'].diff()
        df['gain'] = df['change'].where(df['change'] > 0, 0)
        df['loss'] = -df['change'].where(df['change'] < 0, 0)
        
        # RSI de 14 períodos
        avg_gain = df['gain'].rolling(14).mean()
        avg_loss = df['loss'].rolling(14).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['sma20'] = df['close'].rolling(20).mean()
        df['std20'] = df['close'].rolling(20).std()
        df['bb_upper'] = df['sma20'] + (2 * df['std20'])
        df['bb_lower'] = df['sma20'] - (2 * df['std20'])
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Identificar velas rojas/verdes
        df['es_roja'] = df['close'] < df['open']
        df['es_verde'] = df['close'] > df['open']
        
        return df
        
    except Exception as e:
        print(f"Error obteniendo datos: {e}")
        return None

def diagnosticar_1vr(ticker, fecha_str, deberia_ser_1vr):
    """Diagnostica por qué un ticker fue o no fue detectado como 1VR"""
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO: {ticker} - {fecha_str}")
    print(f"Expectativa: {'SÍ' if deberia_ser_1vr else 'NO'} debería ser 1VR")
    print(f"{'='*60}")
    
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
    df = obtener_datos_dia(ticker, fecha)
    
    if df is None or df.empty:
        print("❌ No se pudieron obtener datos")
        return
    
    # Obtener las últimas 3 velas
    ultimas_3 = df.tail(3)
    print("\nÚltimas 3 velas:")
    print(ultimas_3[['fecha', 'open', 'close', 'es_roja', 'rsi', 'bb_position']].to_string())
    
    # Verificar la última vela (fecha objetivo)
    ultima = df[df['fecha'] == fecha.date()]
    if ultima.empty:
        print(f"\n❌ No hay datos para la fecha exacta {fecha_str}")
        return
    
    ultima = ultima.iloc[0]
    print(f"\n📊 VELA DEL {fecha_str}:")
    print(f"   Open: ${ultima['open']:.2f}")
    print(f"   Close: ${ultima['close']:.2f}")
    print(f"   Es roja: {'SÍ' if ultima['es_roja'] else 'NO'} ({'Roja' if ultima['es_roja'] else 'Verde'})")
    print(f"   RSI: {ultima['rsi']:.1f}")
    print(f"   BB Position: {ultima['bb_position']:.2f}")
    
    # Verificar vela anterior
    idx = df[df['fecha'] == fecha.date()].index[0]
    if idx > 0:
        anterior = df.iloc[idx-1]
        print(f"\n📊 VELA ANTERIOR ({anterior['fecha']}):")
        print(f"   Open: ${anterior['open']:.2f}")
        print(f"   Close: ${anterior['close']:.2f}")
        print(f"   Es verde: {'SÍ' if anterior['es_verde'] else 'NO'} ({'Verde' if anterior['es_verde'] else 'Roja'})")
    
    # Diagnóstico de condiciones 1VR
    print(f"\n🔍 CONDICIONES PARA 1VR:")
    
    condiciones = {
        "1. Vela actual es ROJA": ultima['es_roja'],
        "2. Vela anterior es VERDE": anterior['es_verde'] if idx > 0 else False,
        "3. RSI > 70": ultima['rsi'] > 70,
        "4. BB Position > 0.8": ultima['bb_position'] > 0.8
    }
    
    for condicion, cumple in condiciones.items():
        print(f"   {condicion}: {'✅ SÍ' if cumple else '❌ NO'}")
    
    # Veredicto
    todas_cumplen = all(condiciones.values())
    print(f"\n📍 VEREDICTO: {'ES' if todas_cumplen else 'NO ES'} Primera Vela Roja")
    
    if todas_cumplen and not deberia_ser_1vr:
        print("⚠️ PROBLEMA: Se detectó como 1VR pero NO debería")
    elif not todas_cumplen and deberia_ser_1vr:
        print("⚠️ PROBLEMA: NO se detectó como 1VR pero SÍ debería")
    else:
        print("✅ CORRECTO: La detección coincide con lo esperado")

def main():
    print("🔍 DIAGNÓSTICO DE PRIMERA VELA ROJA")
    print("Analizando casos problemáticos reportados por Alberto")
    
    # Casos del 23 de octubre
    print("\n" + "="*80)
    print("OCTUBRE 23, 2024 - Casos que SÍ deberían ser 1VR")
    print("="*80)
    
    diagnosticar_1vr('GLD', '2024-10-23', deberia_ser_1vr=True)
    diagnosticar_1vr('XOM', '2024-10-23', deberia_ser_1vr=True)
    
    # Caso del 24 de octubre  
    print("\n" + "="*80)
    print("OCTUBRE 24, 2024 - Caso que NO debería ser 1VR")
    print("="*80)
    
    diagnosticar_1vr('USO', '2024-10-24', deberia_ser_1vr=False)
    
    # Verificar también los otros casos mencionados
    print("\n" + "="*80)
    print("OTROS CASOS DEL 24 DE OCTUBRE")
    print("="*80)
    
    diagnosticar_1vr('POWI', '2024-10-24', deberia_ser_1vr=True)  # No sabemos si debería
    diagnosticar_1vr('GLD', '2024-10-24', deberia_ser_1vr=True)   # Para ver el problema de ganancia

if __name__ == "__main__":
    main()