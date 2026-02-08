#!/usr/bin/env python3
"""Verificar estructura del bloque 6 GDB de Dan Dare 2"""
import struct
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")

with open(tzx_file, 'rb') as f:
    data = f.read()

# Bloque 6 está en offset 10434
offset = 10434
block_id = data[offset]
print(f'Offset {offset}: Block ID: 0x{block_id:02X}')

# El ID ya está en offset, los datos empiezan en offset+1
pos = offset + 1

block_len = struct.unpack_from('<I', data, pos)[0]
print(f'Block length: {block_len} bytes')
pos += 4

pause = struct.unpack_from('<H', data, pos)[0]
print(f'Pause: {pause} ms')
pos += 2

totp = struct.unpack_from('<I', data, pos)[0]
print(f'TOTP: {totp}')
pos += 4

npp = data[pos]
print(f'NPP: {npp}')
pos += 1

asp = data[pos]
print(f'ASP: {asp}')
pos += 1

totd = struct.unpack_from('<I', data, pos)[0]
print(f'TOTD: {totd}')
pos += 4

npd = data[pos]
print(f'NPD: {npd}')
pos += 1

asd = data[pos]
print(f'ASD: {asd}')
pos += 1

print(f'\n=== PILOT SYMBOL TABLE (pos={pos}, ASP={asp} symbols) ===')

# SYMDEF structure for each symbol:
# +0x00  BYTE    Symbol flags  
# +0x01  WORD    Number of pulses
# +0x03  WORD[]  Pulse durations (number of pulses entries)

pilot_symbols_info = []
for sym_idx in range(asp):
    sym_flags = data[pos]
    num_pulses = struct.unpack_from('<H', data, pos+1)[0]
    
    print(f'Symbol {sym_idx} @ {pos}: flags=0x{sym_flags:02X}, num_pulses={num_pulses}')
    
    # Leer pulsos
    pulses = []
    for p in range(num_pulses):
        pulse = struct.unpack_from('<H', data, pos + 3 + p*2)[0]
        pulses.append(pulse)
    
    print(f'  Pulsos T-states: {pulses}')
    print(f'  Pulsos us: {[f"{p/3.5:.1f}" for p in pulses]}')
    
    pilot_symbols_info.append({
        'flags': sym_flags,
        'num_pulses': num_pulses,
        'pulses': pulses
    })
    
    # Avanzar: 1 byte flags + 2 bytes num_pulses + num_pulses*2 bytes de pulsos
    pos += 3 + num_pulses * 2

print(f'\n=== PRLE STREAM (pos={pos}, TOTP={totp}) ===')
# PRLE = Symbol + Repetitions (2 bytes)
prle_data = []
remaining = totp
while remaining > 0:
    symbol = data[pos]
    reps = struct.unpack_from('<H', data, pos+1)[0]
    print(f'  Symbol {symbol} x {reps}')
    prle_data.append((symbol, reps))
    remaining -= reps
    pos += 3

print(f'\n=== DATA SYMBOL TABLE (pos={pos}, ASD={asd} symbols) ===')
data_symbols_info = []
for sym_idx in range(asd):
    sym_flags = data[pos]
    num_pulses = struct.unpack_from('<H', data, pos+1)[0]
    
    print(f'Symbol {sym_idx} @ {pos}: flags=0x{sym_flags:02X}, num_pulses={num_pulses}')
    
    # Leer pulsos
    pulses = []
    for p in range(num_pulses):
        pulse = struct.unpack_from('<H', data, pos + 3 + p*2)[0]
        pulses.append(pulse)
    
    print(f'  Pulsos T-states: {pulses}')
    print(f'  Pulsos us: {[f"{p/3.5:.1f}" for p in pulses]}')
    
    data_symbols_info.append({
        'flags': sym_flags,
        'num_pulses': num_pulses,
        'pulses': pulses
    })
    
    pos += 3 + num_pulses * 2

# Calcular total de pulsos
print(f'\n=== CÁLCULO DE PULSOS TOTALES ===')
total_pilot_pulses = 0
for sym, reps in prle_data:
    pulses_per = pilot_symbols_info[sym]['num_pulses']
    total_pilot_pulses += reps * pulses_per
    print(f'  Pilot symbol {sym} x {reps} = {reps * pulses_per} pulses')

print(f'Total pilot pulses: {total_pilot_pulses}')

# Para datos, cada símbolo se usa una vez por bit
total_data_pulses = totd * data_symbols_info[0]['num_pulses']  # Asumiendo símbolos tienen mismo num_pulses
print(f'Total data symbols: {totd}')
print(f'Pulses per data symbol: {data_symbols_info[0]["num_pulses"]}')
print(f'Total data pulses: {total_data_pulses}')

grand_total = total_pilot_pulses + total_data_pulses
print(f'\nGRAND TOTAL: {grand_total} pulses')
print(f'Paridad: {"PAR (termina igual que empezó)" if grand_total % 2 == 0 else "IMPAR (termina invertido)"}')

# El pulso de 16ms que vimos en el WAV
print(f'\n=== BÚSQUEDA DE PULSO LARGO (16ms = ~56000 T-states) ===')
for i, sym in enumerate(pilot_symbols_info):
    for p_idx, pulse in enumerate(sym['pulses']):
        if pulse > 20000:
            print(f'  Pilot symbol {i}, pulse {p_idx}: {pulse} T-states = {pulse/3.5:.1f}us = {pulse/3500:.1f}ms')
            
for i, sym in enumerate(data_symbols_info):
    for p_idx, pulse in enumerate(sym['pulses']):
        if pulse > 20000:
            print(f'  Data symbol {i}, pulse {p_idx}: {pulse} T-states = {pulse/3.5:.1f}us = {pulse/3500:.1f}ms')
