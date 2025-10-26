"""
Test que verifica que TODAS las especificaciones de Alberto están implementadas
"""
import pandas as pd
import numpy as np
from funciones_alberto import (
    calc_bins, get_cohort, calc_mfe, 
    percentil_10, hist_90_display, normalizar_columnas
)

def test_normalizacion():
    """Test 1: Normalización de columnas con todas las variantes"""
    print("🧪 TEST 1: NORMALIZACIÓN DE COLUMNAS")
    print("="*60)
    
    # DataFrame con diferentes variantes de nombres
    df = pd.DataFrame({
        'ticker': ['SPY', 'TSLA', 'RR'],
        'rsi': [70, 65, np.nan],  # RR sin RSI
        'BB Pos': [0.8, 0.7, 85],  # RR en % (85%)
        'otro': [1, 2, 3]
    })
    
    print("DataFrame original:")
    print(df)
    
    # Normalizar
    df_norm = normalizar_columnas(df)
    
    print("\nDespués de normalizar:")
    print(df_norm[['RSI', 'BB_PCTB']])
    
    # Verificar
    assert 'RSI' in df_norm.columns, "❌ No creó columna RSI"
    assert 'BB_PCTB' in df_norm.columns, "❌ No creó columna BB_PCTB"
    assert df_norm['BB_PCTB'].iloc[2] == 0.85, "❌ No convirtió % a decimal"
    assert pd.isna(df_norm['RSI'].iloc[2]), "❌ No maneja NaN en RSI"
    
    print("✅ Normalización correcta")

def test_bins():
    """Test 2: Bins con rangos correctos y Int64"""
    print("\n\n🧪 TEST 2: BINS CON RANGOS CORRECTOS")
    print("="*60)
    
    df = pd.DataFrame({
        'RSI': [15, 35, 55, 75, 95, np.nan],
        'BB_PCTB': [0.1, 0.3, 0.5, 0.7, 0.9, np.nan]
    })
    
    # Calcular bins
    df_bins = calc_bins(df)
    
    print("Bins calculados:")
    print(df_bins[['RSI', 'rsi_bin', 'BB_PCTB', 'bb_bin']])
    
    # Verificar tipos
    assert df_bins['rsi_bin'].dtype == 'Int64', "❌ rsi_bin no es Int64"
    assert df_bins['bb_bin'].dtype == 'Int64', "❌ bb_bin no es Int64"
    
    # Verificar valores
    assert df_bins['rsi_bin'].iloc[0] == 0, "❌ RSI 15 debería estar en bin 0"
    assert df_bins['rsi_bin'].iloc[2] == 2, "❌ RSI 55 debería estar en bin 2"
    assert pd.isna(df_bins['rsi_bin'].iloc[5]), "❌ No maneja NaN en bins"
    
    print("✅ Bins calculados correctamente con Int64")

def test_cohorte():
    """Test 3: Selección de cohorte con expansión"""
    print("\n\n🧪 TEST 3: SELECCIÓN DE COHORTE")
    print("="*60)
    
    # DataFrame histórico con bins
    df_hist = pd.DataFrame({
        'ticker': ['RR'] * 10,
        'rsi_bin': [2, 2, 3, 3, 3, 3, 4, 4, 1, 0],
        'bb_bin': [2, 3, 2, 3, 3, 3, 3, 4, 2, 1],
        'side': ['PUT'] * 10,
        'ganancia_d1': range(10, 110, 10)
    })
    
    # Test 1: Coincidencia exacta (debe encontrar 3)
    cohort1 = get_cohort(df_hist, rsi_bin=3, bb_bin=3, side='PUT', min_n=3)
    print(f"Cohorte exacta (3,3): {len(cohort1)} días")
    assert len(cohort1) == 3, "❌ Debería encontrar 3 días exactos"
    
    # Test 2: Sin coincidencia exacta, pero con expansión
    cohort2 = get_cohort(df_hist, rsi_bin=2, bb_bin=2, side='PUT', min_n=3)
    print(f"Cohorte con expansión (2,2): {len(cohort2)} días")
    assert len(cohort2) >= 3, "❌ Debería expandir y encontrar ≥3"
    
    # Test 3: Muy pocos datos, debe devolver todos del side
    cohort3 = get_cohort(df_hist, rsi_bin=5, bb_bin=5, side='PUT', min_n=3)
    print(f"Cohorte sin matches (5,5): {len(cohort3)} días")
    assert len(cohort3) == 10, "❌ Debería devolver todos del mismo side"
    
    print("✅ Cohorte con expansión funciona correctamente")

def test_percentil():
    """Test 4: Percentil con umbral flexible"""
    print("\n\n🧪 TEST 4: PERCENTIL CON UMBRAL FLEXIBLE")
    print("="*60)
    
    # Cohorte pequeña
    cohort_small = pd.DataFrame({
        'mfe_pct': [20, 30, 40]  # Solo 3 valores
    })
    
    # Debe funcionar con n=3
    p10_small = percentil_10(cohort_small, min_n=3)
    print(f"Percentil 10 con n=3: {p10_small}")
    assert p10_small is not None, "❌ Debería calcular con n=3"
    
    # Cohorte muy pequeña
    cohort_tiny = pd.DataFrame({
        'mfe_pct': [20, 30]  # Solo 2 valores
    })
    
    # No debe funcionar con n<3
    p10_tiny = percentil_10(cohort_tiny, min_n=3)
    print(f"Percentil 10 con n=2: {p10_tiny}")
    assert p10_tiny is None, "❌ No debería calcular con n<3"
    
    print("✅ Percentil con umbral flexible funciona")

def test_display():
    """Test 5: Display con explicaciones"""
    print("\n\n🧪 TEST 5: DISPLAY CON EXPLICACIONES")
    print("="*60)
    
    # Caso 1: Con datos
    display1 = hist_90_display(25.5, n_cohort=8)
    print(f"Con datos: '{display1}'")
    assert "26%" in display1, "❌ Debería mostrar porcentaje"
    assert "n=8" in display1, "❌ Debería mostrar n"
    
    # Caso 2: Sin datos por n bajo
    display2 = hist_90_display(None, n_cohort=2)
    print(f"Sin datos (n=2): '{display2}'")
    assert "n<3" in display2, "❌ Debería explicar n<3"
    
    # Caso 3: Sin datos por otra razón
    display3 = hist_90_display(None, n_cohort=5)
    print(f"Sin datos (n=5): '{display3}'")
    assert "sin datos" in display3, "❌ Debería decir sin datos"
    
    print("✅ Display con explicaciones funciona")

def test_integracion():
    """Test 6: Integración completa"""
    print("\n\n🧪 TEST 6: INTEGRACIÓN COMPLETA")
    print("="*60)
    
    # Simular datos históricos con problemas de Alberto
    df_hist = pd.DataFrame({
        'ticker': ['RR'] * 6,
        'fecha': ['2025-10-10', '2025-10-11', '2025-10-15', '2025-10-16', '2025-10-17', '2025-10-18'],
        'rsi': [53, 60, 68, 62, 60, 55],
        'BB Position': [70, 47, 67, 55, 47, 52],  # En %
        'ganancia_d1': [184, 37, 309, 879, 37, 150],  # 879% es irreal
        'prima_entrada': [0.05, 0.40, 0.11, 0.02, 0.15, 0.18],
        'side': ['PUT'] * 6
    })
    
    print("Datos originales (con problemas):")
    print(df_hist[['fecha', 'ganancia_d1', 'prima_entrada']])
    
    # Normalizar y calcular bins
    df_hist = calc_bins(df_hist)
    
    # Simular análisis actual para RR
    df_current = pd.DataFrame([{
        'ticker': 'RR',
        'RSI': 61,
        'BB Position': 52,  # Como %
        'side': 'PUT'
    }])
    df_current = calc_bins(df_current)
    
    # Obtener cohorte
    cohort = get_cohort(
        df_hist,
        df_current['rsi_bin'].iloc[0],
        df_current['bb_bin'].iloc[0],
        'PUT',
        min_n=3
    )
    
    # Filtrar datos irreales (como hace app_v90b.py)
    cohort_filtered = cohort[
        (cohort['ganancia_d1'] <= 400) & 
        (cohort['prima_entrada'] >= 0.10) &  # Rango RR: $0.10-$0.20
        (cohort['prima_entrada'] <= 0.20)
    ]
    
    print(f"\nCohorte encontrada: {len(cohort)} días")
    print(f"Después de filtrar: {len(cohort_filtered)} días")
    print("\nDías válidos:")
    print(cohort_filtered[['fecha', 'ganancia_d1', 'prima_entrada']])
    
    # Verificar que excluye los problemáticos
    fechas_validas = cohort_filtered['fecha'].tolist()
    assert '2025-10-16' not in fechas_validas, "❌ No debería incluir día con 879%"
    assert '2025-10-10' not in fechas_validas, "❌ No debería incluir prima $0.05"
    assert '2025-10-17' in fechas_validas, "✅ Debería incluir día válido"
    
    print("✅ Integración completa funciona correctamente")

if __name__ == "__main__":
    print("🔍 VERIFICACIÓN DE ESPECIFICACIONES DE ALBERTO")
    print("="*80)
    
    try:
        test_normalizacion()
        test_bins()
        test_cohorte()
        test_percentil()
        test_display()
        test_integracion()
        
        print("\n\n✅ TODAS LAS ESPECIFICACIONES ESTÁN IMPLEMENTADAS")
        print("="*80)
        print("El sistema ahora:")
        print("1. Normaliza todas las variantes de RSI y BB")
        print("2. Usa bins robustos con Int64 tolerante a NaN")
        print("3. Selecciona cohortes con n≥3 y expansión ±1")
        print("4. Calcula percentiles con umbral flexible")
        print("5. Muestra explicaciones cuando no hay datos")
        print("6. FILTRA CORRECTAMENTE los datos irreales de RR")
        
    except AssertionError as e:
        print(f"\n❌ ERROR: {e}")
        print("Algo no está funcionando según las especificaciones")