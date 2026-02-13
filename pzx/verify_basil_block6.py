#!/usr/bin/env python3
"""
Verifica los offsets completos del bloque GDB #6 de Basil
"""

import struct
import math
import os

filepath = os.path.join(os.path.dirname(__file__), 'pzxsamples', 'gdb', 'Basil the Great Mouse Detective.tzx')

with open(filepath, 'rb') as f:
    data = f.read()

offset = 0x00026C
print(f"=== ANÁLISIS COMPLETO BLOQUE GDB #6 ===\n")

# Header
block_id = data[offset]
block_size = struct.unpack('<I', data[offset+1:offset+5])[0]
pause = struct.unpack('<H', data[offset+5:offset+7])[0]

print(f"Block ID: 0x{block_id:02X}")
print(f"Block size: {block_size} bytes")
print(f"Pause: {pause}ms\n")

# Parameters
TOTP = struct.unpack('<I', data[offset+7:offset+11])[0]
NPP = data[offset+11]
ASP = data[offset+12]
TOTD = struct.unpack('<I', data[offset+13:offset+17])[0]
NPD = data[offset+17]
ASD = data[offset+18]

print(f"PILOT/SYNC: TOTP={TOTP}, NPP={NPP}, ASP={ASP}")
print(f"DATA: TOTD={TOTD}, NPD={NPD}, ASD={ASD}\n")

# Parse SYMDEF Pilot/Sync
pos = offset + 19
print(f"SYMDEF PILOT/SYNC @ 0x{pos:06X}:")
for s in range(ASP):
    flag = data[pos]
    pos += 1
    pulses = []
    for p in range(NPP):
        pulse = struct.unpack('<H', data[pos:pos+2])[0]
        pulses.append(pulse)
        pos += 2
    polarity = ['toggle', 'keep', 'low', 'high'][flag & 0x03]
    print(f"  Sym[{s}]: flag=0x{flag:02X} ({polarity}), pulses={pulses}")

# Parse SYMDEF Data
print(f"\nSYMDEF DATA @ 0x{pos:06X}:")
for s in range(ASD):
    flag = data[pos]
    pos += 1
    pulses = []
    for p in range(NPD):
        pulse = struct.unpack('<H', data[pos:pos+2])[0]
        pulses.append(pulse)
        pos += 2
    polarity = ['toggle', 'keep', 'low', 'high'][flag & 0x03]
    print(f"  Sym[{s}]: flag=0x{flag:02X} ({polarity}), pulses={pulses}")

# PRLE Pilot Stream
nb_pilot = math.ceil(math.log2(ASP)) if ASP > 1 else 1
pilot_stream_bytes = math.ceil((TOTP * nb_pilot) / 8)
print(f"\nPRLE PILOT STREAM @ 0x{pos:06X}:")
print(f"  NB bits per symbol: {nb_pilot}")
print(f"  Total symbols: {TOTP}")
print(f"  Stream size: {pilot_stream_bytes} bytes")
print(f"  First 16 bytes: {data[pos:pos+16].hex()}")

# Decodificar los primeros símbolos PRLE
print(f"  Primeros 10 símbolos PRLE:")
bit_pos = 0
for i in range(min(10, TOTP)):
    byte_idx = bit_pos // 8
    bit_offset = bit_pos % 8
    
    # Leer NB bits
    symbol_id = 0
    for b in range(nb_pilot):
        byte_pos = (bit_pos + b) // 8
        bit_in_byte = (bit_pos + b) % 8
        bit_value = (data[pos + byte_pos] >> bit_in_byte) & 1
        symbol_id |= (bit_value << b)
    
    print(f"    PRLE[{i}]: symbolID={symbol_id}")
    bit_pos += nb_pilot

pos += pilot_stream_bytes

# DATA Stream
nb_data = math.ceil(math.log2(ASD)) if ASD > 1 else 1
data_stream_bytes = math.ceil((TOTD * nb_data) / 8)
print(f"\nDATA STREAM @ 0x{pos:06X}:")
print(f"  NB bits per symbol: {nb_data}")
print(f"  Total symbols: {TOTD}")
print(f"  Stream size: {data_stream_bytes} bytes")
print(f"  First 16 bytes: {data[pos:pos+16].hex()}")

# Decodificar los primeros símbolos DATA
print(f"  Primeros 20 símbolos DATA:")
bit_pos = 0
for i in range(min(20, TOTD)):
    # Leer NB bits
    symbol_id = 0
    for b in range(nb_data):
        byte_pos = (bit_pos + b) // 8
        bit_in_byte = (bit_pos + b) % 8
        bit_value = (data[pos + byte_pos] >> bit_in_byte) & 1
        symbol_id |= (bit_value << b)
    
    print(f"    DATA[{i}]: symbolID={symbol_id}", end='')
    if i % 10 == 9:
        print()
    else:
        print(", ", end='')
if TOTD > 0:
    print()

pos += data_stream_bytes

# Pause
pause_value = struct.unpack('<H', data[pos:pos+2])[0]
print(f"\nPAUSE @ 0x{pos:06X}: {pause_value}ms")
pos += 2

# Verificar que llegamos al final del bloque
expected_end = offset + 1 + 4 + block_size
print(f"\nVERIFICACIÓN:")
print(f"  Posición final calculada: 0x{pos:06X}")
print(f"  Posición final esperada: 0x{expected_end:06X}")
print(f"  ¿Coinciden? {'SÍ ✓' if pos == expected_end else 'NO ✗ ERROR'}")

# Siguiente bloque
next_block_id = data[pos]
print(f"\nSiguiente bloque @ 0x{pos:06X}: ID 0x{next_block_id:02X}")
