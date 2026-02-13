#!/usr/bin/env python3
"""
Lectura EXACTA de los bytes del GDB de BC's Quest
para verificar los valores reales
"""

def hexdump(data, start, length, title=""):
    print(f"\n{title} (offset {start}):")
    for i in range(0, length, 16):
        hex_str = ' '.join(f'{data[start+i+j]:02X}' for j in range(min(16, length-i)))
        print(f"  {start+i:04X}: {hex_str}")

with open("BC's Quest for Tires.tzx", 'rb') as f:
    data = f.read()

# Offset del bloque GDB
gdb_offset = 590
print(f"Block ID at {gdb_offset}: 0x{data[gdb_offset]:02X}")

# Leer header del GDB
pos = gdb_offset + 1

# Block length (4 bytes)
block_len = data[pos] | (data[pos+1]<<8) | (data[pos+2]<<16) | (data[pos+3]<<24)
print(f"\nBlock length: {block_len} bytes")
pos += 4

# Pause (2 bytes)
pause = data[pos] | (data[pos+1]<<8)
print(f"Pause: {pause} ms")
pos += 2

# TOTP (4 bytes)
totp = data[pos] | (data[pos+1]<<8) | (data[pos+2]<<16) | (data[pos+3]<<24)
print(f"TOTP: {totp}")
pos += 4

# NPP (1 byte)
npp = data[pos]
print(f"NPP: {npp}")
pos += 1

# ASP (1 byte)
asp = data[pos]
print(f"ASP: {asp}")
pos += 1

# TOTD (4 bytes)
totd = data[pos] | (data[pos+1]<<8) | (data[pos+2]<<16) | (data[pos+3]<<24)
print(f"TOTD: {totd}")
pos += 4

# NPD (1 byte)
npd = data[pos]
print(f"NPD: {npd}")
pos += 1

# ASD (1 byte)
asd = data[pos]
print(f"ASD: {asd}")
pos += 1

print(f"\nCurrent position after header: {pos}")

# Mostrar hexdump de la tabla de símbolos de piloto
pilot_table_size = asp * (1 + npp * 2)  # flags + pulses
print(f"\nPilot symbol table size: {pilot_table_size} bytes")
hexdump(data, pos, pilot_table_size, "PILOT SYMBOL TABLE")

# Decodificar piloto manualmente
print("\n--- PILOT SYMBOLS DECODED ---")
pilot_pos = pos
for i in range(asp):
    flags = data[pilot_pos]
    pilot_pos += 1
    pulses = []
    for p in range(npp):
        pulse = data[pilot_pos] | (data[pilot_pos+1] << 8)
        pulses.append(pulse)
        pilot_pos += 2
    print(f"  Symbol {i}: flags=0x{flags:02X}, pulses={pulses}")

pos = pilot_pos

# Stream de piloto
import math
bits_per_pilot = max(1, math.ceil(math.log2(asp))) if asp > 1 else 1
pilot_stream_bytes = (totp * bits_per_pilot + 7) // 8
print(f"\nPilot stream: {pilot_stream_bytes} bytes at offset {pos}")
hexdump(data, pos, pilot_stream_bytes, "PILOT STREAM")
pos += pilot_stream_bytes

# Tabla de símbolos de datos
data_table_size = asd * (1 + npd * 2)
print(f"\nData symbol table at offset {pos}, size: {data_table_size} bytes")
hexdump(data, pos, data_table_size, "DATA SYMBOL TABLE")

# Decodificar datos manualmente
print("\n--- DATA SYMBOLS DECODED ---")
data_pos = pos
for i in range(asd):
    flags = data[data_pos]
    data_pos += 1
    pulses = []
    for p in range(npd):
        pulse = data[data_pos] | (data[data_pos+1] << 8)
        pulses.append(pulse)
        data_pos += 2
    
    # Calcular tiempos
    total_t = sum(pulses)
    time_us = total_t / 3.5
    
    # Verificar simetría
    if len(pulses) == 2 and pulses[0] > 0:
        ratio = pulses[1] / pulses[0]
        sym_type = "SYMMETRIC" if pulses[0] == pulses[1] else f"ASYMMETRIC (ratio {ratio:.2f})"
    else:
        sym_type = "N/A"
    
    print(f"  Symbol {i}: flags=0x{flags:02X}, pulses={pulses}")
    print(f"           Total: {total_t}T = {time_us:.1f}µs, {sym_type}")

# Ahora vamos a verificar qué dice realmente el formato
print("\n" + "="*70)
print("VERIFICACIÓN CONTRA ESPECIFICACIÓN TZX 1.20")
print("="*70)

print("""
Según TZX spec, para bloque GDB (0x19):

Symbol Definition Table:
- Byte 0: Symbol flags
  * bit 0: Polarity of first pulse (0=low first, 1=high first)
  * bit 1-7: Reserved, must be 0
- Following NPP/NPD words: Pulse durations in T-states

BC's Quest Symbol 0 flags = 0x97:
  Esto NO es válido según la especificación.
  Solo bit 0 debería usarse.

¿Posible causa?
1. El archivo TZX está corrupto
2. Usa extensión no documentada
3. Error en la herramienta que creó el TZX
""")

# Verificar si hay otro TZX de BC's Quest con datos diferentes
print("\n" + "="*70)
print("COMPARACIÓN CON VALORES ESPERADOS DE PADLOCK")
print("="*70)

print("""
PADLOCK típicamente usa estos timings:
- Pilot: ~2168 T-states (como ROM estándar)
- Sync: valores custom
- Data 0: ~780-810 T-states por semi-pulso
- Data 1: ~1560-1620 T-states por semi-pulso (2x Data 0)

BC's Quest TZX muestra:
- Pilot sym 0: [2168, 0] ✓ OK
- Pilot sym 1: [667, 735] - sync corto
- Pilot sym 2: [780, 1170] - ¿sync o dato?
- Data sym 0: flags=0x97, [268, 1] - ¡MUY EXTRAÑO!
- Data sym 1: flags=0x02, [4, 3072] - ¡MUY EXTRAÑO!

Los valores de datos NO coinciden con PADLOCK típico.
Esto sugiere que el TZX fue creado con una herramienta
que codifica los datos de manera diferente.
""")
