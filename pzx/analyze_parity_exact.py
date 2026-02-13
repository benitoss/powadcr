#!/usr/bin/env python3
"""
Cálculo exacto de paridad de pulsos para Book of the Dead
"""

print("="*70)
print("Análisis de paridad de pulsos - Book of the Dead TZX")
print("="*70)

# Estado inicial
level = "down"

def toggle(lv):
    return "up" if lv == "down" else "down"

def generate_pulses(num_pulses, name):
    global level
    start = level
    for i in range(num_pulses):
        level = toggle(level)
    print(f"  {name}: {num_pulses} pulsos, {start} -> {level}")

print("\n--- BLOQUE 2 (Standard Header) ---")
print(f"Inicio: {level}")
generate_pulses(8063, "Pilot")
generate_pulses(1, "SYNC1")
generate_pulses(1, "SYNC2")
generate_pulses(19 * 8 * 2, "Data (19 bytes)")
# Pausa 1ms -> debería generar terminador si necesario y quedar en LOW
# Pero con el bug actual...
print(f"Antes de pausa: {level}")
print(">>> PAUSA 1ms <<<")
# Con changeNextEARedge=true, se alterna
level = toggle(level)
print(f"Silencio generado en: {level}")
print(f"Después de pausa: {level}")

print("\n--- BLOQUE 3 (Standard Data) ---")
print(f"Inicio: {level}")
generate_pulses(3223, "Pilot")
generate_pulses(1, "SYNC1")
generate_pulses(1, "SYNC2")
generate_pulses(446 * 8 * 2, "Data (446 bytes)")
# Pausa 0ms -> NO hay silencio
print(f"Antes de pausa: {level}")
print(">>> PAUSA 0ms - NO SE GENERA SILENCIO <<<")
print(f"Después de pausa: {level}")

print("\n--- BLOQUE 4 (Standard Header) ---")
print(f"Inicio: {level}")
generate_pulses(8063, "Pilot")
generate_pulses(1, "SYNC1")
generate_pulses(1, "SYNC2")
generate_pulses(19 * 8 * 2, "Data (19 bytes)")
print(f"Antes de pausa: {level}")
print(">>> PAUSA 1ms <<<")
level = toggle(level)
print(f"Silencio generado en: {level}")
print(f"Después de pausa: {level}")

print("\n--- BLOQUE 5 (Standard Data) ---")
print(f"Inicio: {level}")
generate_pulses(3223, "Pilot")
generate_pulses(1, "SYNC1")
generate_pulses(1, "SYNC2")
generate_pulses(1109 * 8 * 2, "Data (1109 bytes)")
print(f"Antes de pausa: {level}")
print(">>> PAUSA 2ms <<<")
level = toggle(level)
print(f"Silencio generado en: {level}")
print(f"Después de pausa: {level}")

print("\n--- BLOQUE 6 (Standard Header con flag 0x07) ---")
print(f"Inicio: {level}")
generate_pulses(8063, "Pilot")
generate_pulses(1, "SYNC1")
generate_pulses(1, "SYNC2")
generate_pulses(1002 * 8 * 2, "Data (1002 bytes)")
print(f"Antes de pausa: {level}")
print(">>> PAUSA 2677ms <<<")
level = toggle(level)
print(f"Silencio generado en: {level}")
print(f"Después de pausa: {level}")

print("\n--- BLOQUE 7 (GDB) ---")
print(f"Inicio: {level}")
# GDB: Symbol 0 tiene 1 pulso, repetido 8063 veces
generate_pulses(8063, "Pilot (Symbol 0 x 8063)")
# Symbol 1 tiene 2 pulsos (SYNC), repetido 1 vez  
generate_pulses(2, "SYNC (Symbol 1 x 1)")
# Data: cada símbolo tiene 2 pulsos
generate_pulses(48906 * 2, "Data (48906 symbols)")
print(f"Antes de pausa: {level}")
print(">>> PAUSA 30741ms <<<")
level = toggle(level)
print(f"Silencio generado en: {level}")
print(f"Después de pausa: {level}")

print("\n" + "="*70)
print("PROBLEMA IDENTIFICADO:")
print("="*70)
print("""
El problema está en cómo se genera el silencio.

Según la especificación TZX v1.20:
- "A 'Pause' block consists of a 'low' pulse level"
- "At the end of a 'Pause' block the 'current pulse level' is low"

El código actual:
- Si EDGE_EAR_IS=up: genera silencio en LOW, deja EDGE_EAR_IS=down (CORRECTO)
- Si EDGE_EAR_IS=down: genera silencio en HIGH, deja EDGE_EAR_IS=up (INCORRECTO!)

El silencio SIEMPRE debe:
1. Generar un "terminador" (1ms en el nivel actual si es HIGH)
2. Generar el resto en nivel LOW
3. Dejar EDGE_EAR_IS=down

SOLUCIÓN:
Modificar pulseSilence() o silence() para que:
- Si el nivel actual es UP: generar terminador en HIGH (1ms), luego LOW
- Si el nivel actual es DOWN: generar directamente en LOW
- Al final: EDGE_EAR_IS = down (siempre)
""")
