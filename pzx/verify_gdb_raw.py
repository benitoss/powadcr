#!/usr/bin/env python3
"""Verifica los bytes raw del pilot stream del GDB"""

import struct

filepath = r"pzxsamples\gdb\Book Of The Dead - Part 1 (CRL).tzx"

with open(filepath, 'rb') as f:
    data = f.read()

# El bloque GDB está en offset 0x000A6A
gdb_start = 0x0A6A
print(f"Bloque GDB @ 0x{gdb_start:06X}")

# ID + Length
print(f"ID: 0x{data[gdb_start]:02X}")
length = struct.unpack('<I', data[gdb_start+1:gdb_start+5])[0]
print(f"Length: {length}")

gdb_data = gdb_start + 5

# Cabecera GDB
pause = struct.unpack('<H', data[gdb_data:gdb_data+2])[0]
totp = struct.unpack('<I', data[gdb_data+2:gdb_data+6])[0]
npp = data[gdb_data+6]
asp = data[gdb_data+7]

print(f"\nPause: {pause}")
print(f"TOTP: {totp} (raw bytes: {data[gdb_data+2:gdb_data+6].hex()})")
print(f"NPP: {npp}")
print(f"ASP: {asp}")

# Offset de las definiciones de símbolos
symdef_start = gdb_data + 14
print(f"\nSymbol definitions @ offset 0x{symdef_start:06X}")

# Symbol 0
print(f"\nSymbol 0:")
print(f"  Flags: 0x{data[symdef_start]:02X}")
pulse0_0 = struct.unpack('<H', data[symdef_start+1:symdef_start+3])[0]
pulse0_1 = struct.unpack('<H', data[symdef_start+3:symdef_start+5])[0]
print(f"  Pulse 0: {pulse0_0} (raw: {data[symdef_start+1:symdef_start+3].hex()})")
print(f"  Pulse 1: {pulse0_1} (raw: {data[symdef_start+3:symdef_start+5].hex()})")

# Symbol 1
sym1_start = symdef_start + 1 + npp * 2
print(f"\nSymbol 1 @ offset 0x{sym1_start:06X}:")
print(f"  Flags: 0x{data[sym1_start]:02X}")
pulse1_0 = struct.unpack('<H', data[sym1_start+1:sym1_start+3])[0]
pulse1_1 = struct.unpack('<H', data[sym1_start+3:sym1_start+5])[0]
print(f"  Pulse 0: {pulse1_0} (raw: {data[sym1_start+1:sym1_start+3].hex()})")
print(f"  Pulse 1: {pulse1_1} (raw: {data[sym1_start+3:sym1_start+5].hex()})")

# Pilot stream
pilot_stream_start = sym1_start + 1 + npp * 2
print(f"\n=== PILOT STREAM @ offset 0x{pilot_stream_start:06X} ===")

for i in range(totp):
    entry_offset = pilot_stream_start + i * 3
    symbol = data[entry_offset]
    repeat_bytes = data[entry_offset+1:entry_offset+3]
    repeat = struct.unpack('<H', repeat_bytes)[0]
    print(f"Entry {i} @ 0x{entry_offset:06X}: symbol={symbol}, repeat={repeat} (raw: {repeat_bytes.hex()})")

# Verificar si el repeat es 8063 o 8064
print(f"\n=== VERIFICACIÓN ===")
print(f"8063 en hex little-endian: {struct.pack('<H', 8063).hex()}")
print(f"8064 en hex little-endian: {struct.pack('<H', 8064).hex()}")
