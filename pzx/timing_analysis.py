"""
Análisis detallado del timing de BC's Quest para identificar por qué falla en hardware real
"""
import math

# Parámetros del GDB de BC's Quest
CPU_FREQ = 3500000  # 3.5 MHz ZX Spectrum
SAMPLING_RATES = [44100, 48000, 32000, 22050]

# Símbolos de datos
DATA_SYMBOLS = {
    0: [780, 780],    # Bit 0
    1: [780, 1560],   # Bit 1
}

# Símbolos de pilot/sync
PILOT_SYMBOLS = {
    0: [2168, 0],     # Pilot tone (single pulse)
    1: [667, 735],    # Sync
    2: [780, 1170],   # Extended sync?
}

# Secuencia pilot/sync
PRLE = [
    (0, 3223),  # Pilot: 3223 repeticiones de Symbol 0
    (1, 1),     # Sync: 1 repetición de Symbol 1
    (2, 4),     # Extended sync: 4 repeticiones de Symbol 2
]

print("=" * 70)
print("BC's Quest for Tires - Timing Analysis")
print("=" * 70)

def tstates_to_samples(tstates, sample_rate):
    """Convierte T-states a samples con el error de redondeo"""
    exact = (tstates / CPU_FREQ) * sample_rate
    rounded = round(exact)
    error = exact - rounded
    error_percent = (error / exact) * 100 if exact > 0 else 0
    return rounded, error, error_percent

print("\n1. DATA SYMBOL TIMING")
print("-" * 70)

for sr in SAMPLING_RATES:
    print(f"\nSampling Rate: {sr} Hz")
    print(f"  {'Symbol':<10} {'Pulse':<10} {'T-states':<10} {'Samples':<10} {'Error %':<10}")
    
    for sym_id, pulses in DATA_SYMBOLS.items():
        for pulse_idx, tstates in enumerate(pulses):
            samples, error, error_pct = tstates_to_samples(tstates, sr)
            print(f"  Sym{sym_id}[{pulse_idx}]    {pulse_idx:<10} {tstates:<10} {samples:<10} {error_pct:+.2f}%")
    
    # Calcular duración total de cada símbolo
    sym0_total = sum(DATA_SYMBOLS[0])
    sym1_total = sum(DATA_SYMBOLS[1])
    
    sam0, _, err0 = tstates_to_samples(sym0_total, sr)
    sam1, _, err1 = tstates_to_samples(sym1_total, sr)
    
    print(f"  Total Symbol 0: {sym0_total}T -> {sam0} samples")
    print(f"  Total Symbol 1: {sym1_total}T -> {sam1} samples")
    print(f"  Ratio real: {sym1_total/sym0_total:.2f}x")
    print(f"  Ratio samples: {sam1/sam0:.2f}x")

print("\n" + "=" * 70)
print("2. PILOT/SYNC TIMING")
print("-" * 70)

for sr in SAMPLING_RATES:
    print(f"\nSampling Rate: {sr} Hz")
    
    total_pilot_samples = 0
    
    for sym_id, repeat in PRLE:
        pulses = PILOT_SYMBOLS[sym_id]
        sym_samples = 0
        
        for pulse_idx, tstates in enumerate(pulses):
            if tstates > 0:
                samples, _, _ = tstates_to_samples(tstates, sr)
                sym_samples += samples
        
        total_sym_samples = sym_samples * repeat
        total_pilot_samples += total_sym_samples
        
        print(f"  Symbol {sym_id}: {pulses} x{repeat} = {total_sym_samples} samples")
    
    duration_ms = (total_pilot_samples / sr) * 1000
    print(f"  Total pilot/sync: {total_pilot_samples} samples = {duration_ms:.2f} ms")

print("\n" + "=" * 70)
print("3. CRITICAL ANALYSIS")
print("-" * 70)

print("\nThe loader uses asymmetric encoding:")
print("  - First pulse of both symbols is IDENTICAL (780T)")
print("  - The loader syncs on the FIRST edge")
print("  - Then measures time to SECOND edge to determine bit value")
print()
print("Critical timing points:")
print("  - Bit 0: 780T delay, then 780T pulse = 780T between edges 1-2")
print("  - Bit 1: 780T delay, then 1560T pulse = 780T between edges 1-2... WAIT!")
print()
print("Actually, each SYMBOL consists of TWO semi-pulses that create edges:")
print()
print("For Symbol 0 [780, 780]:")
print("  - Pulse 1 (780T): Creates EDGE 1 -> EDGE 2")
print("  - Pulse 2 (780T): Creates EDGE 2 -> EDGE 3")
print("  Total: 1560T from start to end")
print()
print("For Symbol 1 [780, 1560]:")
print("  - Pulse 1 (780T): Creates EDGE 1 -> EDGE 2 (same as Symbol 0!)")
print("  - Pulse 2 (1560T): Creates EDGE 2 -> EDGE 3")
print("  Total: 2340T from start to end")
print()
print("The loader likely works like this:")
print("  1. Wait for rising/falling edge (EDGE 1)")
print("  2. Wait for next edge (EDGE 2) - this takes 780T for BOTH symbols")
print("  3. Measure time to EDGE 3:")
print("     - If ~780T -> Bit 0")
print("     - If ~1560T -> Bit 1")

print("\n" + "=" * 70)
print("4. POTENTIAL ISSUES")
print("-" * 70)

print("\nAt 44100 Hz sampling rate:")
sr = 44100
# Edge 2 to Edge 3 timing is critical
bit0_edge23 = 780
bit1_edge23 = 1560

sam0, _, _ = tstates_to_samples(bit0_edge23, sr)
sam1, _, _ = tstates_to_samples(bit1_edge23, sr)

# Calculate actual T-states from samples
actual0 = (sam0 / sr) * CPU_FREQ
actual1 = (sam1 / sr) * CPU_FREQ

print(f"  Bit 0 edge2-3: Expected {bit0_edge23}T, Generated {sam0} samples = {actual0:.1f}T")
print(f"  Bit 1 edge2-3: Expected {bit1_edge23}T, Generated {sam1} samples = {actual1:.1f}T")
print(f"  Threshold for loader: ~{(bit0_edge23 + bit1_edge23) / 2:.0f}T = {(actual0 + actual1) / 2:.1f}T")
print()
print(f"  Bit 0 error: {actual0 - bit0_edge23:+.1f}T ({(actual0/bit0_edge23 - 1)*100:+.2f}%)")
print(f"  Bit 1 error: {actual1 - bit1_edge23:+.1f}T ({(actual1/bit1_edge23 - 1)*100:+.2f}%)")

print("\n" + "=" * 70)
print("5. COMPARISON WITH DAN DARE 2 (which WORKS)")
print("-" * 70)

DD2_SYMBOLS = {
    0: [555, 555],    # Bit 0
    1: [1110, 1110],  # Bit 1
}

print("\nDan Dare 2 symbols:")
for sym_id, pulses in DD2_SYMBOLS.items():
    print(f"  Symbol {sym_id}: {pulses}")

print("\nKey difference:")
print("  Dan Dare 2: SYMMETRIC encoding (both pulses same length)")
print("  BC's Quest: ASYMMETRIC encoding (first pulse same, second differs)")
print()
print("  Dan Dare 2 loader can sync on ANY edge")
print("  BC's Quest loader MUST sync correctly and measure the SECOND interval")
print()
print("This makes BC's Quest more sensitive to timing errors!")
