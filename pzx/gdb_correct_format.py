#!/usr/bin/env python3
"""Corrección: Interpretar GDB según especificación TZX v1.20"""
import struct
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")

with open(tzx_file, 'rb') as f:
    data = f.read()

# Bloque 4 @ 919 (primer GDB)
pos = 919
print(f'=== GDB Block @ offset {pos} ===')
print(f'ID: 0x{data[pos]:02X}')

# Header del GDB
block_len = struct.unpack_from('<I', data, pos+1)[0]
pause = struct.unpack_from('<H', data, pos+5)[0]
totp = struct.unpack_from('<I', data, pos+7)[0]
npp = data[pos+11]  # Max pulses per pilot symbol
asp = data[pos+12]  # Number of pilot symbols
totd = struct.unpack_from('<I', data, pos+13)[0]
npd = data[pos+17]  # Max pulses per data symbol
asd = data[pos+18]  # Number of data symbols

print(f'Block length: {block_len}')
print(f'Pause: {pause} ms')
print(f'TOTP: {totp}')
print(f'NPP (max pulses per pilot symbol): {npp}')
print(f'ASP (num pilot symbols): {asp}')
print(f'TOTD: {totd}')
print(f'NPD (max pulses per data symbol): {npd}')
print(f'ASD (num data symbols): {asd}')

# La tabla de símbolos pilot tiene ASP entradas
# Cada entrada es: 1 byte flags + NPP * 2 bytes de duraciones
# (Nota: si un símbolo tiene menos pulsos, el resto son 0)

print(f'\n=== PILOT SYMBOL TABLE (ASP={asp} symbols, NPP={npp}) ===')
sym_pos = pos + 19  # Empieza después del header fijo

# Cada SYMDEF tiene: 1 byte flags + NPP words de duraciones
symdef_size = 1 + npp * 2

pilot_symbols = []
for s in range(asp):
    flags = data[sym_pos]
    durations = []
    for p in range(npp):
        dur = struct.unpack_from('<H', data, sym_pos + 1 + p*2)[0]
        if dur > 0:
            durations.append(dur)
    
    print(f'Symbol {s} @ {sym_pos}: flags=0x{flags:02X}')
    print(f'  Durations (T-states): {durations}')
    print(f'  Durations (us): {[f"{d/3.5:.1f}" for d in durations]}')
    
    pilot_symbols.append({'flags': flags, 'durations': durations})
    sym_pos += symdef_size

print(f'\nPilot symbols table ends at offset {sym_pos}')

# PRLE stream para pilot/sync
print(f'\n=== PRLE STREAM (TOTP={totp}) ===')
prle_entries = []
remaining = totp
while remaining > 0:
    symbol = data[sym_pos]
    reps = struct.unpack_from('<H', data, sym_pos+1)[0]
    print(f'  Symbol {symbol} x {reps}')
    prle_entries.append((symbol, reps))
    remaining -= reps
    sym_pos += 3

print(f'\nPRLE stream ends at offset {sym_pos}')

# Data symbol table
print(f'\n=== DATA SYMBOL TABLE (ASD={asd} symbols, NPD={npd}) ===')
symdef_size_data = 1 + npd * 2

data_symbols = []
for s in range(asd):
    flags = data[sym_pos]
    durations = []
    for p in range(npd):
        dur = struct.unpack_from('<H', data, sym_pos + 1 + p*2)[0]
        if dur > 0:
            durations.append(dur)
    
    print(f'Symbol {s} @ {sym_pos}: flags=0x{flags:02X}')
    print(f'  Durations (T-states): {durations}')
    print(f'  Durations (us): {[f"{d/3.5:.1f}" for d in durations]}')
    
    data_symbols.append({'flags': flags, 'durations': durations})
    sym_pos += symdef_size_data

print(f'\nData symbols table ends at offset {sym_pos}')

# Calcular pulsos totales
print(f'\n=== PULSE COUNT ===')
total_pilot_pulses = 0
for symbol, reps in prle_entries:
    pulses_per = len(pilot_symbols[symbol]['durations'])
    total_pilot_pulses += reps * pulses_per
    print(f'  Pilot symbol {symbol} x {reps} = {reps * pulses_per} pulses')

# Para datos, cada símbolo tiene sus pulsos
# Los datos usan ceil(log2(ASD)) bits por símbolo
import math
bits_per_symbol = math.ceil(math.log2(asd)) if asd > 1 else 1
print(f'\nData: {totd} symbols, {bits_per_symbol} bits per symbol')
# Asumiendo todos los símbolos tienen el mismo número de pulsos
pulses_per_data_symbol = len(data_symbols[0]['durations'])
total_data_pulses = totd * pulses_per_data_symbol

print(f'Total pilot pulses: {total_pilot_pulses}')
print(f'Total data pulses: {total_data_pulses}')
grand_total = total_pilot_pulses + total_data_pulses
print(f'GRAND TOTAL: {grand_total} pulses')
print(f'Paridad: {"PAR" if grand_total % 2 == 0 else "IMPAR"}')
