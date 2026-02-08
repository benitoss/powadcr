#!/usr/bin/env python3
"""Check PRLE structure in Dan Dare 2 GDB block"""
import struct
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")

with open(tzx_file, 'rb') as f:
    data = f.read()

pos = 919
npp = data[pos+11]
asp = data[pos+12]
npd = data[pos+17]
asd = data[pos+18]
totp = struct.unpack_from('<I', data, pos+7)[0]
totd = struct.unpack_from('<I', data, pos+13)[0]

print(f"GDB Header:")
print(f"  NPP={npp}, ASP={asp}, TOTP={totp}")
print(f"  NPD={npd}, ASD={asd}, TOTD={totd}")

# Calculate offsets
pilot_sym_start = pos + 19
pilot_sym_size = 1 + npp * 2  # 1 byte flags + NPP words
pilot_table_size = asp * pilot_sym_size

data_sym_start = pilot_sym_start + pilot_table_size
data_sym_size = 1 + npd * 2  # 1 byte flags + NPD words
data_table_size = asd * data_sym_size

prle_start = data_sym_start + data_table_size
data_prle_start = prle_start + totp * 3  # Each PRLE is 3 bytes (1+2)

print(f"\nOffsets:")
print(f"  Pilot symbols: {pilot_sym_start}")
print(f"  Data symbols: {data_sym_start}")
print(f"  Pilot PRLE: {prle_start}")
print(f"  Data PRLE: {data_prle_start}")

# Read PRLE entries
print(f"\nPilot PRLE (first {min(totp, 10)} entries of {totp}):")
prle_pos = prle_start
total_pilot_pulses = 0
for i in range(min(totp, 10)):
    symbol = data[prle_pos]
    reps = struct.unpack_from('<H', data, prle_pos+1)[0]
    
    # Get pulses for this symbol (count non-zero durations)
    sym_offset = pilot_sym_start + symbol * pilot_sym_size + 1
    pulses_in_sym = 0
    for j in range(npp):
        dur = struct.unpack_from('<H', data, sym_offset + j*2)[0]
        if dur > 0:
            pulses_in_sym += 1
    
    total_this = reps * pulses_in_sym
    total_pilot_pulses += total_this
    print(f"  [{i}] Symbol {symbol} x {reps} = {total_this} pulses")
    prle_pos += 3

print(f"\nTotal pilot pulses from PRLE: {total_pilot_pulses}")

# Read data PRLE
print(f"\nData PRLE (first {min(totd, 10)} entries of {totd}):")
prle_pos = data_prle_start
total_data_pulses = 0
for i in range(min(totd, 10)):
    symbol = data[prle_pos]
    reps = struct.unpack_from('<H', data, prle_pos+1)[0]
    
    # Get pulses for this symbol
    sym_offset = data_sym_start + symbol * data_sym_size + 1
    pulses_in_sym = 0
    for j in range(npd):
        dur = struct.unpack_from('<H', data, sym_offset + j*2)[0]
        if dur > 0:
            pulses_in_sym += 1
    
    total_this = reps * pulses_in_sym
    total_data_pulses += total_this
    print(f"  [{i}] Symbol {symbol} x {reps} = {total_this} pulses")
    prle_pos += 3

print(f"\nTotal data pulses from PRLE (first {min(totd, 10)}): {total_data_pulses}")
