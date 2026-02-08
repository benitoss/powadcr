#!/usr/bin/env python3
"""Complete analysis of Dan Dare 2 GDB block - count total pulses"""
import math
import struct
import os

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
print("GDB Block @ offset 919 - Dan Dare 2")
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

print(f"\n--- PILOT SYMBOL TABLE ({asp} symbols) ---")
pilot_symbols = []
for i in range(asp):
    sym_offset = pilot_sym_start + i * pilot_sym_size
    flags = data[sym_offset]
    durations = []
    for j in range(npp):
        dur = struct.unpack_from('<H', data, sym_offset + 1 + j*2)[0]
        if dur > 0:
            durations.append(dur)
    pilot_symbols.append({'flags': flags, 'durations': durations})
    print(f"Symbol {i}: flags=0x{flags:02x}, durations={durations} ({len(durations)} pulses)")

# Parse data symbol table
data_sym_start = pilot_sym_start + asp * pilot_sym_size
data_sym_size = 1 + npd * 2

print(f"\n--- DATA SYMBOL TABLE ({asd} symbols) ---")
data_symbols = []
for i in range(asd):
    sym_offset = data_sym_start + i * data_sym_size
    flags = data[sym_offset]
    durations = []
    for j in range(npd):
        dur = struct.unpack_from('<H', data, sym_offset + 1 + j*2)[0]
        if dur > 0:
            durations.append(dur)
    data_symbols.append({'flags': flags, 'durations': durations})
    print(f"Symbol {i}: flags=0x{flags:02x}, durations={durations} ({len(durations)} pulses)")

# Parse pilot PRLE
pilot_prle_start = data_sym_start + asd * data_sym_size

print(f"\n--- PILOT PRLE ({totp} entries) ---")
prle_pos = pilot_prle_start
total_pilot_pulses = 0
total_pilot_duration = 0

for i in range(totp):
    symbol = data[prle_pos]
    reps = struct.unpack_from('<H', data, prle_pos+1)[0]
    
    pulses_per_sym = len(pilot_symbols[symbol]['durations'])
    total_pulses = reps * pulses_per_sym
    total_pilot_pulses += total_pulses
    
    # Calculate duration
    sym_duration = sum(pilot_symbols[symbol]['durations'])
    total_duration = reps * sym_duration
    total_pilot_duration += total_duration
    
    print(f"Entry {i}: Symbol {symbol} x {reps} = {total_pulses} pulses ({total_duration} T-states = {total_duration/3500000*1000:.2f}ms)")
    prle_pos += 3

print(f"\nTotal pilot pulses: {total_pilot_pulses}")
print(f"Total pilot duration: {total_pilot_duration} T-states = {total_pilot_duration/3500000:.4f}s = {total_pilot_duration/3500000*1000:.2f}ms")

# Parse data stream
data_prle_start = prle_pos

# Calculate NB
nb = math.ceil(math.log2(asd)) if asd > 1 else 1
ds_bytes = math.ceil(nb * totd / 8)

print(f"\n--- DATA STREAM ---")
print(f"NB (bits per symbol): {nb}")
print(f"Data stream size: {ds_bytes} bytes")
print(f"TOTD (symbols to decode): {totd}")

# Read data stream bytes
data_stream = data[data_prle_start:data_prle_start + ds_bytes]

# Count data symbols and pulses
symbol_counts = [0] * asd
total_data_pulses = 0
total_data_duration = 0

bit_index = 0
symbols_read = 0

while symbols_read < totd:
    # Extract symbol ID
    symbol_id = 0
    for b in range(nb):
        byte_idx = bit_index // 8
        bit_pos = 7 - (bit_index % 8)
        bit_value = (data_stream[byte_idx] >> bit_pos) & 1
        symbol_id = (symbol_id << 1) | bit_value
        bit_index += 1
    
    if symbol_id < asd:
        symbol_counts[symbol_id] += 1
        total_data_pulses += len(data_symbols[symbol_id]['durations'])
        total_data_duration += sum(data_symbols[symbol_id]['durations'])
    
    symbols_read += 1

print(f"\nData symbol distribution:")
for i, count in enumerate(symbol_counts):
    print(f"  Symbol {i}: {count} times = {count * len(data_symbols[i]['durations'])} pulses")

print(f"\nTotal data pulses: {total_data_pulses}")
print(f"Total data duration: {total_data_duration} T-states = {total_data_duration/3500000:.4f}s = {total_data_duration/3500000*1000:.2f}ms")

# Grand totals
total_pulses = total_pilot_pulses + total_data_pulses
total_duration = total_pilot_duration + total_data_duration

print(f"\n{'='*60}")
print(f"GRAND TOTALS:")
print(f"  Total pulses: {total_pulses}")
print(f"  Total duration: {total_duration/3500000*1000:.2f}ms = {total_duration/3500000:.4f}s")
print(f"  Pause after: {pause}ms")
print(f"  Parity: {'IMPAR (ODD)' if total_pulses % 2 == 1 else 'PAR (EVEN)'}")
print(f"{'='*60}")
