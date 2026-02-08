#!/usr/bin/env python3
"""Ver bytes raw del bloque GDB"""
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")

with open(tzx_file, 'rb') as f:
    data = f.read()

# Bloque 4 @ 919 (primer GDB)
pos = 919
print(f'Bloque GDB en offset {pos}')
print(f'ID: 0x{data[pos]:02X}')

# Raw bytes del inicio del bloque
print(f'\nRaw bytes desde ID:')
print(f'Offset  Hex   Dec  Significado')
print(f'------  ----  ---  -----------')

i = 0
print(f'+{i:02d}     0x{data[pos+i]:02X}  {data[pos+i]:3d}  Block ID (0x19 = GDB)')
i = 1
block_len = data[pos+i] | (data[pos+i+1]<<8) | (data[pos+i+2]<<16) | (data[pos+i+3]<<24)
print(f'+{i:02d}-04  ...   ...  Block length = {block_len}')
i = 5
pause = data[pos+i] | (data[pos+i+1]<<8)
print(f'+{i:02d}-06  ...   ...  Pause = {pause} ms')
i = 7
totp = data[pos+i] | (data[pos+i+1]<<8) | (data[pos+i+2]<<16) | (data[pos+i+3]<<24)
print(f'+{i:02d}-10  ...   ...  TOTP = {totp}')
i = 11
print(f'+{i:02d}     0x{data[pos+i]:02X}  {data[pos+i]:3d}  NPP (max pulses per pilot symbol)')
i = 12
print(f'+{i:02d}     0x{data[pos+i]:02X}  {data[pos+i]:3d}  ASP (num pilot symbols in alphabet)')
i = 13
totd = data[pos+i] | (data[pos+i+1]<<8) | (data[pos+i+2]<<16) | (data[pos+i+3]<<24)
print(f'+{i:02d}-16  ...   ...  TOTD = {totd}')
i = 17
print(f'+{i:02d}     0x{data[pos+i]:02X}  {data[pos+i]:3d}  NPD (max pulses per data symbol)')
i = 18
print(f'+{i:02d}     0x{data[pos+i]:02X}  {data[pos+i]:3d}  ASD (num data symbols in alphabet)')

# Ahora la tabla de símbolos pilot
print(f'\n--- PILOT SYMBOL TABLE (ASP={data[pos+12]} entries) ---')
sym_pos = pos + 19
for s in range(data[pos+12]):
    print(f'\nSymbol {s} @ offset {sym_pos}:')
    print(f'  flags: 0x{data[sym_pos]:02X}')
    np = data[sym_pos+1] | (data[sym_pos+2]<<8)
    print(f'  num_pulses: {np} (bytes: 0x{data[sym_pos+1]:02X} 0x{data[sym_pos+2]:02X})')
    
    if np <= 20:
        print(f'  pulse durations:')
        for p in range(np):
            dur = data[sym_pos+3+p*2] | (data[sym_pos+3+p*2+1]<<8)
            print(f'    [{p}] {dur} T-states = {dur/3.5:.1f} us')
        sym_pos += 3 + np * 2
    else:
        print(f'  *** TOO MANY PULSES - CHECKING RAW BYTES ***')
        print(f'  Raw bytes at symbol start:')
        for b in range(20):
            print(f'    +{b}: 0x{data[sym_pos+b]:02X} ({data[sym_pos+b]:3d})')
        break
