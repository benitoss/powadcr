#!/usr/bin/env python3
"""
Analiza bytes crudos del bloque GDB #6 de Basil
"""

import struct
import os

filepath = os.path.join(os.path.dirname(__file__), 'pzxsamples', 'gdb', 'Basil the Great Mouse Detective.tzx')

with open(filepath, 'rb') as f:
    data = f.read()

# El bloque GDB #6 está en offset 0x00026C
offset = 0x00026C

print(f"Bloque GDB #6 @ offset 0x{offset:06X}")
print(f"\nPrimeros 50 bytes (hex):")
hex_data = data[offset:offset+50]
for i in range(0, len(hex_data), 16):
    hex_str = ' '.join(f'{b:02X}' for b in hex_data[i:i+16])
    print(f"  {offset+i:06X}: {hex_str}")

print(f"\nAnálisis:")
print(f"  Byte 0: ID = 0x{data[offset]:02X}")
block_size = struct.unpack('<I', data[offset+1:offset+5])[0]
print(f"  Bytes 1-4: Block size = {block_size} (0x{block_size:08X})")
pause = struct.unpack('<H', data[offset+5:offset+7])[0]
print(f"  Bytes 5-6: Pause = {pause}ms")

TOTP = struct.unpack('<I', data[offset+7:offset+11])[0]
print(f"  Bytes 7-10: TOTP = {TOTP}")
NPP = data[offset+11]
print(f"  Byte 11: NPP = {NPP}")
ASP = data[offset+12]
print(f"  Byte 12: ASP = {ASP}")

TOTD = struct.unpack('<I', data[offset+13:offset+17])[0]
print(f"  Bytes 13-16: TOTD = {TOTD}")
NPD = data[offset+17]
print(f"  Byte 17: NPD = {NPD}")
ASD = data[offset+18]
print(f"  Byte 18: ASD = {ASD}")

print(f"\nSímbolos PILOT/SYNC (ASP={ASP}, NPP={NPP}):")
pos = offset + 19
for s in range(ASP):
    flag = data[pos]
    print(f"  Sym[{s}]: flag=0x{flag:02X} @ pos 0x{pos:06X}")
    pos += 1
    for p in range(NPP):
        pulse = struct.unpack('<H', data[pos:pos+2])[0]
        print(f"    Pulse[{p}]: {pulse}T (0x{pulse:04X}) @ pos 0x{pos:06X}")
        pos += 2

print(f"\nSímbolos DATA (ASD={ASD}, NPD={NPD}):")
for s in range(ASD):
    flag = data[pos]
    print(f"  Sym[{s}]: flag=0x{flag:02X} @ pos 0x{pos:06X}")
    pos += 1
    for p in range(NPD):
        pulse = struct.unpack('<H', data[pos:pos+2])[0]
        pulse_bytes = data[pos:pos+2]
        print(f"    Pulse[{p}]: {pulse}T (0x{pulse:04X}, bytes: {pulse_bytes.hex()}) @ pos 0x{pos:06X}")
        pos += 2

print(f"\nPosición después de símbolos: 0x{pos:06X}")
print(f"Siguiente byte (debe ser PRLE pilot stream): 0x{data[pos]:02X}")
