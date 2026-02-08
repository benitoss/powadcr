#!/usr/bin/env python3
"""Analyze Dan Dare 2 WAV to understand block structure"""
import wave
import os
import struct

script_dir = os.path.dirname(os.path.abspath(__file__))
wav_file = os.path.join(script_dir, "pzxsamples", "gdb", "Dan Dare 2.wav")

with wave.open(wav_file, 'rb') as w:
    channels = w.getnchannels()
    sample_width = w.getsampwidth()
    sample_rate = w.getframerate()
    num_frames = w.getnframes()
    print(f"WAV Info:")
    print(f"  Channels: {channels}")
    print(f"  Sample width: {sample_width} bytes")
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Frames: {num_frames}")
    print(f"  Duration: {num_frames / sample_rate:.2f} seconds")
    
    frames = w.readframes(num_frames)

# Parse samples (8-bit unsigned)
if sample_width == 1:
    samples = list(frames)  # 8-bit unsigned
    samples = [s - 128 for s in samples]  # Convert to signed
else:
    samples = list(struct.unpack(f'<{num_frames}h', frames))

# Find edges and measure pulse lengths
threshold = 0
edges = []
prev_level = 1 if samples[0] > threshold else 0
prev_sample_idx = 0

for i, s in enumerate(samples[1:], 1):
    curr_level = 1 if s > threshold else 0
    if curr_level != prev_level:
        pulse_samples = i - prev_sample_idx
        pulse_us = pulse_samples * 1000000 / sample_rate
        edges.append({
            'sample': i,
            'time_ms': i * 1000 / sample_rate,
            'from_level': prev_level,
            'to_level': curr_level,
            'pulse_us': pulse_us
        })
        prev_sample_idx = i
        prev_level = curr_level

print(f"\nTotal edges: {len(edges)}")

# Analyze silences (long periods without edges)
# A silence is typically > 1ms
SILENCE_THRESHOLD_US = 1000  # 1ms

print("\nLooking for silences (pauses > 1ms):")
silence_count = 0
for i, edge in enumerate(edges[:100]):  # First 100 edges
    if edge['pulse_us'] > SILENCE_THRESHOLD_US:
        silence_count += 1
        print(f"  Edge {i} @ {edge['time_ms']:.1f}ms: pulse {edge['pulse_us']:.0f}us, {edge['from_level']}->{edge['to_level']}")

# Find blocks based on long silences
print("\n\nBlock boundaries (silences > 10ms):")
BLOCK_THRESHOLD_US = 10000  # 10ms

block_start = 0
block_num = 0
for i, edge in enumerate(edges):
    if edge['pulse_us'] > BLOCK_THRESHOLD_US:
        if block_num < 15:  # First 15 blocks
            # Count pulses in this block
            pulses_in_block = i - block_start
            duration_ms = edge['time_ms'] - (edges[block_start]['time_ms'] if block_start < len(edges) else 0)
            
            print(f"Block {block_num}: starts @ {edges[block_start]['time_ms']:.1f}ms, {pulses_in_block} pulses, duration ~{duration_ms:.0f}ms")
            
            # Analyze pilot tone
            if pulses_in_block > 100 and block_num < 5:
                pilot_pulses = edges[block_start:block_start+100]
                avg_pulse = sum(p['pulse_us'] for p in pilot_pulses) / 100
                print(f"  Pilot tone avg pulse: {avg_pulse:.0f}us ({avg_pulse*3.5:.0f} T-states)")
        
        block_start = i + 1
        block_num += 1

print(f"\nTotal blocks found: {block_num}")

# Analyze first block in detail
print("\n\nFirst block detail (first 50 pulses):")
for i in range(min(50, len(edges))):
    e = edges[i]
    print(f"  Pulse {i}: {e['pulse_us']:.1f}us ({e['from_level']}->{e['to_level']})")
