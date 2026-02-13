#!/usr/bin/env python3
"""
Análisis detallado de los FLAGS de símbolos GDB
Los flags determinan cómo se interpreta cada símbolo
"""

def analyze_symbol_flags(flags):
    """
    Según la especificación TZX 1.20:
    Bit 0: Polarity of the first pulse (0=LOW, 1=HIGH)
    Bit 1: Polarity of the last pulse level (0=LOW, 1=HIGH)
    Bit 2-3: Reserved
    Bit 4-7: Number of valid bits in the last byte (0 = 8 bits)
    
    Para símbolos de datos:
    - Los bits 0-1 definen la polaridad inicial/final
    - Si ambos bits son iguales, el símbolo mantiene polaridad
    - Si son diferentes, el símbolo cambia polaridad
    """
    first_polarity = "HIGH" if (flags & 0x01) else "LOW"
    last_level = "HIGH" if (flags & 0x02) else "LOW"
    reserved = (flags >> 2) & 0x03
    valid_bits = (flags >> 4) & 0x0F
    
    polarity_change = (flags & 0x01) != ((flags & 0x02) >> 1)
    
    return {
        'flags_hex': f"0x{flags:02X}",
        'flags_bin': f"{flags:08b}",
        'first_polarity': first_polarity,
        'last_level': last_level,
        'reserved': reserved,
        'valid_bits_last_byte': valid_bits if valid_bits > 0 else 8,
        'polarity_changes': polarity_change
    }

print("="*70)
print("ANÁLISIS DE FLAGS DE SÍMBOLOS GDB")
print("="*70)

# Dan Dare 2 - Símbolos de datos
print("\n--- DAN DARE 2 (FUNCIONA) ---")
print("\nSímbolo 0 (bit 0): pulses=[512, 1], flags=0x02")
info = analyze_symbol_flags(0x02)
for k, v in info.items():
    print(f"  {k}: {v}")

print("\nSímbolo 1 (bit 1): pulses=[1, 258], flags=0x03")
info = analyze_symbol_flags(0x03)
for k, v in info.items():
    print(f"  {k}: {v}")

# BC's Quest - Símbolos de datos
print("\n--- BC's QUEST (FALLA) ---")
print("\nSímbolo 0 (bit 0): pulses=[268, 1], flags=0x97")
info = analyze_symbol_flags(0x97)
for k, v in info.items():
    print(f"  {k}: {v}")

print("\nSímbolo 1 (bit 1): pulses=[4, 3072], flags=0x02")
info = analyze_symbol_flags(0x02)
for k, v in info.items():
    print(f"  {k}: {v}")

print("\n" + "="*70)
print("ANÁLISIS CRÍTICO")
print("="*70)

print("""
¡IMPORTANTE! Los flags en BC's Quest son MUY diferentes:

BC's Quest Bit 0 flags = 0x97 = 10010111 en binario:
  - Bit 0 (first_polarity) = 1 → Empieza en HIGH
  - Bit 1 (last_level)     = 1 → Termina en HIGH  
  - Bit 2-3 (reserved)     = 01 → ¡NO CERO! 
  - Bit 4-7 (valid_bits)   = 1001 = 9 → ¡FUERA DE RANGO (0-8)!

Esto sugiere que los flags 0x97 tienen un significado especial
o están siendo interpretados incorrectamente.

Dan Dare 2 usa flags "normales":
  - 0x02: Empieza LOW, termina HIGH
  - 0x03: Empieza HIGH, termina HIGH

La diferencia CLAVE es:
  - BC's Quest tiene flags con bits 4-7 no cero
  - Esto podría indicar codificación especial o compresión
""")

# Analizar los datos reales de BC's Quest más detalladamente
print("\n" + "="*70)
print("RE-LECTURA DE BC's Quest GDB desde archivo")
print("="*70)

def read_word(data, offset):
    return data[offset] | (data[offset+1] << 8)

def read_dword(data, offset):
    return data[offset] | (data[offset+1] << 8) | (data[offset+2] << 16) | (data[offset+3] << 24)

with open("BC's Quest for Tires.tzx", 'rb') as f:
    data = f.read()

# El GDB está en offset 590
pos = 590 + 1  # +1 para saltar el ID del bloque
block_len = read_dword(data, pos)
pos += 4

pause = read_word(data, pos)
pos += 2

totp = read_dword(data, pos)
pos += 4

npp = data[pos]
pos += 1

asp = data[pos]
pos += 1

totd = read_dword(data, pos)
pos += 4

npd = data[pos]
pos += 1

asd = data[pos]
pos += 1

print(f"\nGDB Block Info:")
print(f"  Block length: {block_len}")
print(f"  Pause: {pause} ms")
print(f"  TOTP: {totp}, NPP: {npp}, ASP: {asp}")
print(f"  TOTD: {totd}, NPD: {npd}, ASD: {asd}")

# Leer tabla de símbolos de piloto
print(f"\n--- PILOT SYMBOL TABLE (raw bytes) ---")
for i in range(asp):
    flags = data[pos]
    pos += 1
    pulses_raw = []
    for p in range(npp):
        p_lo = data[pos]
        p_hi = data[pos + 1]
        pulse = p_lo | (p_hi << 8)
        pulses_raw.append((p_lo, p_hi, pulse))
        pos += 2
    print(f"  Symbol {i}: flags=0x{flags:02X}, raw={pulses_raw}")

# Calcular tamaño del stream de piloto
import math
bits_per_pilot = max(1, math.ceil(math.log2(asp))) if asp > 1 else 1
pilot_stream_bytes = (totp * bits_per_pilot + 7) // 8
print(f"\n  Pilot stream: {pilot_stream_bytes} bytes")
pos += pilot_stream_bytes

# Leer tabla de símbolos de datos
print(f"\n--- DATA SYMBOL TABLE (raw bytes) ---")
for i in range(asd):
    flags = data[pos]
    print(f"  Symbol {i} offset: {pos}, flags byte: 0x{flags:02X}")
    pos += 1
    
    pulses_raw = []
    for p in range(npd):
        p_lo = data[pos]
        p_hi = data[pos + 1]
        pulse = p_lo | (p_hi << 8)
        pulses_raw.append({
            'lo': f"0x{p_lo:02X}",
            'hi': f"0x{p_hi:02X}",
            'value': pulse,
            'T_states': pulse
        })
        pos += 2
    
    print(f"    Pulses: {pulses_raw}")
    
    # Verificar si los valores tienen sentido
    total_t = sum(p['value'] for p in pulses_raw)
    time_us = total_t / 3.5
    print(f"    Total: {total_t}T = {time_us:.1f}µs")

print("\n" + "="*70)
print("HIPÓTESIS ACTUALIZADA")
print("="*70)
print("""
Los datos RAW muestran valores extraños para BC's Quest:
  - Símbolo 0: [268, 1] - muy corto
  - Símbolo 1: [4, 3072] - muy largo y asimétrico

Comparado con Dan Dare 2:
  - Símbolo 0: [512, 1] - similar patrón
  - Símbolo 1: [1, 258] - patrón invertido

¡CLAVE! Ambos archivos tienen símbolos con un pulso muy corto (1-4 T).
Un pulso de 1T a 3.5MHz = 0.28µs = ¡prácticamente instantáneo!

Esto sugiere que el TZX está codificado de manera especial,
posiblemente usando pulsos "virtuales" de 1T para marcar cambios
de estado sin generar audio real.

El problema podría estar en cómo playCustomSymbol() maneja
pulsos tan cortos (1-4 T-states).
""")
