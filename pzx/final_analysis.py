#!/usr/bin/env python3
"""
Final analysis: Compare TZX interpretation with WAV pulses
Focus on identifying the exact cause of the 7058 pulse difference
"""
import struct
import os
import wave
import math

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")
wav_file = os.path.join(script_dir, "pzxsamples", "gdb", "Dan Dare 2.wav")

print("="*70)
print("ANALYSIS: TZX GDB Block vs WAV")
print("="*70)

# === TZX Analysis ===
with open(tzx_file, 'rb') as f:
    tzx_data = f.read()

pos = 919
totp = struct.unpack_from('<I', tzx_data, pos+7)[0]
npp = tzx_data[pos+11]
asp = tzx_data[pos+12]
totd = struct.unpack_from('<I', tzx_data, pos+13)[0]
npd = tzx_data[pos+17]
asd = tzx_data[pos+18]

print("\nTZX GDB Header:")
print(f"  TOTP={totp}, NPP={npp}, ASP={asp}")
print(f"  TOTD={totd}, NPD={npd}, ASD={asd}")

# Parse symbols
pilot_sym_start = pos + 19
pilot_sym_size = 1 + npp * 2
data_sym_start = pilot_sym_start + asp * pilot_sym_size
data_sym_size = 1 + npd * 2

pilot_symbols = []
for i in range(asp):
    off = pilot_sym_start + i * pilot_sym_size
    flags = tzx_data[off]
    durs = [struct.unpack_from('<H', tzx_data, off + 1 + j*2)[0] for j in range(npp)]
    pulses = sum(1 for d in durs if d > 0)
    pilot_symbols.append({'flags': flags, 'durs': durs, 'pulses': pulses})

data_symbols = []
for i in range(asd):
    off = data_sym_start + i * data_sym_size
    flags = tzx_data[off]
    durs = [struct.unpack_from('<H', tzx_data, off + 1 + j*2)[0] for j in range(npd)]
    pulses = sum(1 for d in durs if d > 0)
    data_symbols.append({'flags': flags, 'durs': durs, 'pulses': pulses})

print("\nPilot symbols:")
for i, s in enumerate(pilot_symbols):
    print(f"  [{i}] pulses={s['pulses']}, durs={s['durs']}")

print("\nData symbols:")
for i, s in enumerate(data_symbols):
    print(f"  [{i}] pulses={s['pulses']}, durs={s['durs']}")

# Parse PRLE
pilot_prle_start = data_sym_start + asd * data_sym_size

print(f"\nPilot PRLE ({totp} entries):")
prle_pos = pilot_prle_start
tzx_pilot_pulses = 0
tzx_pilot_duration = 0

for i in range(totp):
    sym = tzx_data[prle_pos]
    reps = struct.unpack_from('<H', tzx_data, prle_pos+1)[0]
    
    if sym < asp and reps > 0:
        pulses = reps * pilot_symbols[sym]['pulses']
        duration = reps * sum(d for d in pilot_symbols[sym]['durs'] if d > 0)
        tzx_pilot_pulses += pulses
        tzx_pilot_duration += duration
        status = "OK"
    elif reps == 0:
        pulses = 0
        duration = 0
        status = "SKIP (rep=0)"
    else:
        pulses = 0
        duration = 0
        status = f"INVALID (sym {sym} >= {asp})"
    
    print(f"  [{i}] sym={sym}, reps={reps}, pulses={pulses}, {status}")
    prle_pos += 3

# Data pulses
tzx_data_pulses = totd * 2  # Each symbol = 2 pulses

print(f"\nTZX Summary:")
print(f"  Pilot pulses: {tzx_pilot_pulses}")
print(f"  Data pulses: {tzx_data_pulses}")
print(f"  TOTAL: {tzx_pilot_pulses + tzx_data_pulses}")

# === WAV Analysis ===
print("\n" + "="*70)
print("WAV Analysis:")
with wave.open(wav_file, 'rb') as w:
    sample_rate = w.getframerate()
    frames = w.readframes(w.getnframes())

samples = [s - 128 for s in frames]

# Find edges
threshold = 0
edges = []
prev_level = 1 if samples[0] > threshold else 0
prev_idx = 0

for i, s in enumerate(samples[1:], 1):
    curr_level = 1 if s > threshold else 0
    if curr_level != prev_level:
        pulse_us = (i - prev_idx) * 1000000 / sample_rate
        edges.append({
            'sample': i,
            'time_ms': i * 1000 / sample_rate,
            'pulse_us': pulse_us
        })
        prev_idx = i
        prev_level = curr_level

# Find block 4 boundaries
BLOCK_THRESHOLD_US = 10000
block_starts = []
for i, e in enumerate(edges):
    if e['pulse_us'] > BLOCK_THRESHOLD_US:
        block_starts.append(i)

# Block 4 is between block_starts[3] and block_starts[4]
b4_start = block_starts[3] + 1
b4_end = block_starts[4]
wav_block4_pulses = b4_end - b4_start

print(f"  Block 4 pulses: {wav_block4_pulses}")
print(f"  Block 4 duration: {edges[b4_end-1]['time_ms'] - edges[b4_start]['time_ms']:.1f}ms")

# === Comparison ===
print("\n" + "="*70)
print("COMPARISON:")
tzx_total = tzx_pilot_pulses + tzx_data_pulses
diff = wav_block4_pulses - tzx_total
print(f"  TZX calculated: {tzx_total} pulses")
print(f"  WAV measured:   {wav_block4_pulses} pulses")
print(f"  DIFFERENCE:     {diff} pulses")
print(f"  Missing symbols (if 2 pulses each): {diff // 2}")

# === Investigate the difference ===
print("\n" + "="*70)
print("INVESTIGATION:")

# Count pilot pulses in WAV (pulses ~619us)
PILOT_TOLERANCE = 100  # us
PILOT_TARGET = 619     # us (2168 T-states)

pilot_like_count = 0
other_count = 0
for e in edges[b4_start:b4_end]:
    if abs(e['pulse_us'] - PILOT_TARGET) < PILOT_TOLERANCE:
        pilot_like_count += 1
    else:
        other_count += 1

print(f"  Pulses ~619us (pilot-like): {pilot_like_count}")
print(f"  Other pulses: {other_count}")

# Count data-like pulses
DATA_SYM0_A = 1599 / 3.5  # ~457us
DATA_SYM0_B = 513 / 3.5   # ~147us  
DATA_SYM1_A = 258 / 3.5   # ~74us
DATA_SYM1_B = 768 / 3.5   # ~219us

print(f"\n  Expected data pulse durations:")
print(f"    Symbol 0: {DATA_SYM0_A:.0f}us, {DATA_SYM0_B:.0f}us")
print(f"    Symbol 1: {DATA_SYM1_A:.0f}us, {DATA_SYM1_B:.0f}us")

# Analyze first 1000 pulses of block 4 to understand structure
print("\n  First 20 pulses of block 4:")
for i in range(20):
    e = edges[b4_start + i]
    print(f"    [{i}] {e['pulse_us']:.0f}us @ {e['time_ms']:.1f}ms")
