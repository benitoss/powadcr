#!/usr/bin/env python3
"""
Simulador de polaridad GDB para verificar el comportamiento de PowaDCR.
Simula exactamente lo que hace el código C++ para contar pulsos y polaridad.
"""

# Definición del bloque 6 de Dan Dare 2 (que el usuario proporcionó)

# Pilot/sync symbol table
pilot_symbols = {
    0: {'flag': 0, 'pulses': [2168]},      # 1 pulso (el 0 termina la lista)
    1: {'flag': 0, 'pulses': [693, 693]},  # 2 pulsos
    2: {'flag': 0, 'pulses': [1420, 1420]},# 2 pulsos
    3: {'flag': 0, 'pulses': [2100, 2100]},# 2 pulsos
    4: {'flag': 0, 'pulses': [555, 555]},  # 2 pulsos
    5: {'flag': 0, 'pulses': [1110, 1110]},# 2 pulsos
}

# Data stream symbol table
data_symbols = {
    0: {'flag': 0, 'pulses': [555, 555]},   # 2 pulsos
    1: {'flag': 0, 'pulses': [1110, 1110]}, # 2 pulsos
}

# Pilot/Sync stream (PRLE): symbol, repeat
pilot_stream = [
    (0, 1599),
    (1, 2),
    (2, 1),
    (3, 3),
    (2, 1),
    (1, 1),
    (5, 3),
    (4, 1),
    (5, 1),
    (4, 1),
]

TOTD = 144  # Total data symbols

def count_pulses_in_symbol(sym_def):
    """Cuenta los pulsos no-cero en un símbolo"""
    return len([p for p in sym_def['pulses'] if p != 0])

def simulate_block():
    """Simula la reproducción de un bloque GDB y cuenta cambios de nivel"""
    
    # Empezamos con nivel LOW (down=0)
    level = 0  # 0=LOW, 1=HIGH
    total_pulses = 0
    total_toggles = 0
    
    print("=" * 60)
    print("SIMULACIÓN DE POLARIDAD GDB - BLOQUE 6 DAN DARE 2")
    print("=" * 60)
    print()
    
    # FASE 1: PILOT/SYNC
    print("--- PILOT/SYNC STREAM ---")
    print(f"Nivel inicial: {'HIGH' if level else 'LOW'}")
    print()
    
    pilot_pulses = 0
    for entry_idx, (sym_id, repeat) in enumerate(pilot_stream):
        sym_def = pilot_symbols[sym_id]
        polarity = sym_def['flag'] & 0x03
        num_pulses = count_pulses_in_symbol(sym_def)
        
        # En el código C++:
        # for (int rep = 0; rep < repeat; rep++)
        #   for each pulse in symbol:
        #     playCustomSymbol(pulseLength, 1)  -> semiPulse -> createPulse -> EDGE_EAR_IS ^= 1
        
        # Cada llamada a playCustomSymbol genera UN pulso y ALTERNA el nivel (si polarity=0)
        pulses_this_entry = num_pulses * repeat
        pilot_pulses += pulses_this_entry
        
        # Simular los toggles
        for _ in range(pulses_this_entry):
            if polarity == 0:  # Toggle
                level ^= 1
                total_toggles += 1
        
        print(f"  Entry {entry_idx}: sym={sym_id}, rep={repeat}, pulses={num_pulses}x{repeat}={pulses_this_entry}, nivel_ahora={'HIGH' if level else 'LOW'}")
    
    print()
    print(f"Total pilot pulses: {pilot_pulses}")
    print(f"Nivel después de pilot: {'HIGH' if level else 'LOW'}")
    print()
    
    # FASE 2: DATA STREAM
    print("--- DATA STREAM ---")
    print(f"TOTD = {TOTD} símbolos")
    
    data_pulses = 0
    # Para simplificar, asumimos que los datos alternan entre símbolo 0 y 1
    # En realidad depende del datastream, pero para contar pulsos:
    # Cada símbolo de datos tiene 2 pulsos
    for sym_idx in range(TOTD):
        # No sabemos el símbolo exacto, pero todos tienen 2 pulsos
        num_pulses = 2  # Tanto sym 0 como sym 1 tienen 2 pulsos
        data_pulses += num_pulses
        
        for _ in range(num_pulses):
            level ^= 1  # Cada pulso alterna
            total_toggles += 1
    
    print(f"Total data pulses: {data_pulses}")
    print(f"Nivel después de data: {'HIGH' if level else 'LOW'}")
    print()
    
    # RESUMEN
    total_pulses = pilot_pulses + data_pulses
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Total pilot pulses:  {pilot_pulses}")
    print(f"Total data pulses:   {data_pulses}")
    print(f"TOTAL PULSES:        {total_pulses}")
    print(f"Paridad:             {'IMPAR' if total_pulses % 2 == 1 else 'PAR'}")
    print()
    print(f"Nivel inicial:       LOW")
    print(f"Nivel final:         {'HIGH' if level else 'LOW'}")
    print()
    
    # Verificación
    if total_pulses % 2 == 1:
        expected_final = 1  # Si empezamos en LOW y hacemos IMPAR pulsos, terminamos en HIGH
    else:
        expected_final = 0  # Si empezamos en LOW y hacemos PAR pulsos, terminamos en LOW
    
    print(f"Verificación: {total_pulses} pulsos desde LOW -> nivel final esperado: {'HIGH' if expected_final else 'LOW'}")
    print(f"Nivel final simulado: {'HIGH' if level else 'LOW'}")
    print(f"¿Coincide? {'SÍ ✓' if level == expected_final else 'NO ✗'}")
    
    return total_pulses, level

def analyze_wav_expectations():
    """Analiza qué debería pasar después del bloque 6"""
    print()
    print("=" * 60)
    print("ANÁLISIS DE TRANSICIÓN BLOQUE 6 -> BLOQUE 7")
    print("=" * 60)
    print()
    print("Según el análisis:")
    print("- Bloque 6 tiene 1915 pulsos (IMPAR)")
    print("- Si empezamos en LOW, terminamos en HIGH")
    print("- El SILENCIO debería mantener el nivel HIGH")
    print()
    print("Si el siguiente bloque (7) empieza con polarity=0 (toggle):")
    print("- El primer pulso del bloque 7 debería empezar en el OPUESTO")
    print("- Es decir, desde HIGH, el primer pulso hará toggle -> LOW")
    print()
    print("¿Es esto lo que observas en el WAV que funciona?")

if __name__ == "__main__":
    total_pulses, final_level = simulate_block()
    analyze_wav_expectations()
