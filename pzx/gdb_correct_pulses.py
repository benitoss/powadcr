#!/usr/bin/env python3
"""Correct pulse count for Dan Dare 2 first GDB block"""
import struct
import os
import math

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")

with open(tzx_file, 'rb') as f:
    data = f.read()

pos = 919  # First GDB block

# Header
block_len = struct.unpack_from('<I', data, pos+1)[0]
pause = struct.unpack_from('<H', data, pos+5)[0]
totp = struct.unpack_from('<I', data, pos+7)[0]
npp = data[pos+11]
asp = data[pos+12]
totd = struct.unpack_from('<I', data, pos+13)[0]
npd = data[pos+17]
asd = data[pos+18]

print("="*60)
print("GDB Block @ offset 919 - Correct Analysis")
print("="*60)
print(f"Block length: {block_len}")
print(f"Pause after: {pause}ms")
print(f"TOTP (pilot PRLE entries): {totp}")
print(f"NPP (max pulses per pilot symbol): {npp}")
print(f"ASP (number of pilot symbols): {asp}")
print(f"TOTD (total data symbols): {totd}")
print(f"NPD (max pulses per data symbol): {npd}")
print(f"ASD (number of data symbols): {asd}")

# Parse pilot symbol table
pilot_sym_start = pos + 19
pilot_sym_size = 1 + npp * 2

print(f"\n--- PILOT SYMBOL TABLE ---")
pilot_symbols = []
for i in range(asp):
    sym_offset = pilot_sym_start + i * pilot_sym_size
    flags = data[sym_offset]
    durations = []
    for j in range(npp):
        dur = struct.unpack_from('<H', data, sym_offset + 1 + j*2)[0]
        durations.append(dur)  # Keep all, including zeros
    # Count non-zero durations = number of pulses
    pulse_count = sum(1 for d in durations if d > 0)
    pilot_symbols.append({'flags': flags, 'durations': durations, 'pulses': pulse_count})
    print(f"Symbol {i}: flags=0x{flags:02x}, durations={durations}, pulses={pulse_count}")

# Parse data symbol table
data_sym_start = pilot_sym_start + asp * pilot_sym_size
data_sym_size = 1 + npd * 2

print(f"\n--- DATA SYMBOL TABLE ---")
data_symbols = []
for i in range(asd):
    sym_offset = data_sym_start + i * data_sym_size
    flags = data[sym_offset]
    durations = []
    for j in range(npd):
        dur = struct.unpack_from('<H', data, sym_offset + 1 + j*2)[0]
        durations.append(dur)
    pulse_count = sum(1 for d in durations if d > 0)
    data_symbols.append({'flags': flags, 'durations': durations, 'pulses': pulse_count})
    print(f"Symbol {i}: flags=0x{flags:02x}, durations={durations}, pulses={pulse_count}")

# Parse pilot PRLE
pilot_prle_start = data_sym_start + asd * data_sym_size

print(f"\n--- PILOT PRLE ({totp} entries) ---")
prle_pos = pilot_prle_start
total_pilot_pulses = 0

for i in range(totp):
    symbol = data[prle_pos]
    reps = struct.unpack_from('<H', data, prle_pos+1)[0]
    
    # Skip invalid entries (symbol out of range)
    if symbol >= asp:
        print(f"Entry {i}: Symbol {symbol} INVALID (>= {asp}), reps={reps} - SKIPPED")
        prle_pos += 3
        continue
    
    # Skip zero repetitions
    if reps == 0:
        print(f"Entry {i}: Symbol {symbol} x 0 - SKIPPED")
        prle_pos += 3
        continue
    
    pulses_per_sym = pilot_symbols[symbol]['pulses']
    total_pulses = reps * pulses_per_sym
    total_pilot_pulses += total_pulses
    
    # Calculate time
    sym_duration_t = sum(d for d in pilot_symbols[symbol]['durations'] if d > 0)
    total_time_t = reps * sym_duration_t
    total_time_ms = total_time_t / 3500  # Convert to ms
    
    print(f"Entry {i}: Symbol {symbol} x {reps} = {total_pulses} pulses ({total_time_ms:.1f}ms)")
    prle_pos += 3

print(f"\nTotal pilot pulses: {total_pilot_pulses}")

# Count data pulses
# Each symbol in data stream has a fixed number of pulses
# All data symbols have 2 pulses each (NPD=2 and both non-zero)
print(f"\n--- DATA STREAM ---")
print(f"TOTD (symbols): {totd}")
print(f"Pulses per symbol: {data_symbols[0]['pulses']} (same for all)")

total_data_pulses = totd * 2  # Each symbol = 2 pulses
print(f"Total data pulses: {total_data_pulses}")

# Grand totals
total_pulses = total_pilot_pulses + total_data_pulses
print(f"\n{'='*60}")
print(f"GRAND TOTAL: {total_pulses} pulses")
print(f"Expected from WAV (Block 4): ~152,638 pulses")
print(f"Difference: {abs(total_pulses - 152638)} pulses")
print(f"Parity: {'IMPAR (ODD)' if total_pulses % 2 == 1 else 'PAR (EVEN)'}")
print(f"{'='*60}")
