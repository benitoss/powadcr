#!/usr/bin/env python3
"""Complete GDB analysis for Dan Dare 2 @ offset 919"""
import struct
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")

with open(tzx_file, 'rb') as f:
    data = f.read()

pos = 919  # First GDB block

print("="*60)
print("GDB Block Analysis - Dan Dare 2 @ offset 919")
print("="*60)

# Header (relative to pos)
# pos+0: block ID (0x19)
# pos+1-4: block length (4 bytes)
# pos+5-6: pause (2 bytes)
# pos+7-10: TOTP (4 bytes)
# pos+11: NPP (1 byte)
# pos+12: ASP (1 byte)
# pos+13-16: TOTD (4 bytes)
# pos+17: NPD (1 byte)
# pos+18: ASD (1 byte)
# pos+19: symbols start

block_len = struct.unpack_from('<I', data, pos+1)[0]
pause = struct.unpack_from('<H', data, pos+5)[0]
totp = struct.unpack_from('<I', data, pos+7)[0]
npp = data[pos+11]
asp = data[pos+12]
totd = struct.unpack_from('<I', data, pos+13)[0]
npd = data[pos+17]
asd = data[pos+18]

print(f"\nHeader:")
print(f"  Block length: {block_len}")
print(f"  Pause after: {pause}ms")
print(f"  TOTP (pilot PRLE entries): {totp}")
print(f"  NPP (max pulses per pilot symbol): {npp}")
print(f"  ASP (number of pilot symbols): {asp}")
print(f"  TOTD (data PRLE entries): {totd}")
print(f"  NPD (max pulses per data symbol): {npd}")
print(f"  ASD (number of data symbols): {asd}")

# Pilot symbol definitions
pilot_sym_start = pos + 19
pilot_sym_size = 1 + npp * 2

print(f"\nPILOT SYMBOLS ({asp} symbols, {pilot_sym_size} bytes each):")
pilot_symbols = []
for i in range(asp):
    sym_offset = pilot_sym_start + i * pilot_sym_size
    flags = data[sym_offset]
    durations = []
    for j in range(npp):
        dur = struct.unpack_from('<H', data, sym_offset + 1 + j*2)[0]
        if dur > 0:
            durations.append(dur)
    pilot_symbols.append({'flags': flags, 'durations': durations, 'pulses': len(durations)})
    dur_str = ', '.join([f"{d} T ({d/3.5:.1f}us)" for d in durations])
    print(f"  Symbol {i}: flags=0x{flags:02x}, {len(durations)} pulse(s): [{dur_str}]")

# Data symbol definitions
data_sym_start = pilot_sym_start + asp * pilot_sym_size
data_sym_size = 1 + npd * 2

print(f"\nDATA SYMBOLS ({asd} symbols, {data_sym_size} bytes each):")
data_symbols = []
for i in range(asd):
    sym_offset = data_sym_start + i * data_sym_size
    flags = data[sym_offset]
    durations = []
    for j in range(npd):
        dur = struct.unpack_from('<H', data, sym_offset + 1 + j*2)[0]
        if dur > 0:
            durations.append(dur)
    data_symbols.append({'flags': flags, 'durations': durations, 'pulses': len(durations)})
    dur_str = ', '.join([f"{d} T ({d/3.5:.1f}us)" for d in durations])
    print(f"  Symbol {i}: flags=0x{flags:02x}, {len(durations)} pulse(s): [{dur_str}]")

# PRLE starts after symbol tables
pilot_prle_start = data_sym_start + asd * data_sym_size

print(f"\nPILOT PRLE ({totp} entries starting @ {pilot_prle_start}):")
prle_pos = pilot_prle_start
total_pilot_pulses = 0
for i in range(totp):
    symbol = data[prle_pos]
    reps = struct.unpack_from('<H', data, prle_pos+1)[0]
    
    if symbol < len(pilot_symbols):
        pulses_count = pilot_symbols[symbol]['pulses']
    else:
        print(f"  ERROR: Symbol {symbol} out of range!")
        pulses_count = 0
    
    total_this = reps * pulses_count
    total_pilot_pulses += total_this
    
    print(f"  Entry {i}: Symbol {symbol} x {reps} = {total_this} pulses")
    prle_pos += 3

# Data PRLE
data_prle_start = pilot_prle_start + totp * 3

print(f"\nDATA PRLE ({totd} entries starting @ {data_prle_start}):")
print(f"  Showing first 10 entries...")
prle_pos = data_prle_start
total_data_pulses = 0
for i in range(totd):
    symbol = data[prle_pos]
    reps = struct.unpack_from('<H', data, prle_pos+1)[0]
    
    if symbol < len(data_symbols):
        pulses_count = data_symbols[symbol]['pulses']
    else:
        print(f"  ERROR: Symbol {symbol} out of range!")
        pulses_count = 0
    
    total_this = reps * pulses_count
    total_data_pulses += total_this
    
    if i < 10:
        print(f"  Entry {i}: Symbol {symbol} x {reps} = {total_this} pulses")
    prle_pos += 3

print(f"  ... ({totd - 10} more entries)")

print(f"\n{'='*60}")
print(f"TOTALS:")
print(f"  Pilot pulses: {total_pilot_pulses}")
print(f"  Data pulses: {total_data_pulses}")
print(f"  GRAND TOTAL: {total_pilot_pulses + total_data_pulses}")
parity = "IMPAR (ODD)" if (total_pilot_pulses + total_data_pulses) % 2 == 1 else "PAR (EVEN)"
print(f"  Parity: {parity}")

# Calculate expected block end
expected_end = data_prle_start + totd * 3
print(f"\nExpected block end: {expected_end}")
print(f"Actual block end (pos + 1 + block_len): {pos + 1 + block_len}")
