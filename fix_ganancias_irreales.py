"""
Fix para corregir ganancias irreales en el sistema
"""

def validar_ganancia(ganancia_pct):
    """
    Valida que la ganancia sea realista
    
    Las opciones raramente superan 500% en un día
    """
    if ganancia_pct > 500:
        print(f"⚠️ Ganancia irreal detectada: {ganancia_pct}%")
        return 0  # Retornar 0 si es irreal
    
    if ganancia_pct < -100:
        print(f"⚠️ Pérdida irreal detectada: {ganancia_pct}%")
        return -100  # Máxima pérdida es -100%
    
    return ganancia_pct

def corregir_calculo_ganancia(prima_entrada, prima_maxima):
    """
    Calcula la ganancia correctamente con validaciones
    """
    # Validar entradas
    if prima_entrada <= 0 or prima_entrada > 1000:
        print(f"❌ Prima entrada inválida: ${prima_entrada}")
        return 0
    
    if prima_maxima <= 0 or prima_maxima > 1000:
        print(f"❌ Prima máxima inválida: ${prima_maxima}")
        return 0
    
    # Calcular ganancia
    ganancia_pct = ((prima_maxima - prima_entrada) / prima_entrada) * 100
    
    # Validar resultado
    ganancia_pct = validar_ganancia(ganancia_pct)
    
    return round(ganancia_pct, 1)

# CÓDIGO A AÑADIR EN app_v90b.py:
"""
En la función calcular_ganancia_real_opcion, reemplazar:

# ANTES:
ganancia_dia1 = ((prima_maxima_dia1 - prima_entrada) / prima_entrada * 100) if prima_entrada > 0 else 0

# DESPUÉS:
if prima_entrada > 0 and prima_entrada < 100 and prima_maxima_dia1 < 100:
    ganancia_dia1 = ((prima_maxima_dia1 - prima_entrada) / prima_entrada * 100)
    # Validar que sea realista
    if ganancia_dia1 > 500:
        print(f"⚠️ Ganancia irreal: {ganancia_dia1}% - limitando a 0%")
        ganancia_dia1 = 0
else:
    ganancia_dia1 = 0
"""

# TAMBIÉN en calcular_ganancia_historica:
"""
# Filtrar ganancias irreales de los históricos
dias_similares = [g for g in dias_similares if 0 <= g <= 500]
"""

print("✅ Validaciones para evitar ganancias irreales:")
print("1. Máxima ganancia permitida: 500%")
print("2. Validar que prima_entrada > 0 y < $100")
print("3. Validar que prima_maxima < $100")
print("4. Si hay valores irreales, mostrar 0%")