#!/usr/bin/env python3
"""
Análisis detallado de la estructura del GDB en el WAV de BC's Quest
"""
import wave
import numpy as np

def detect_pulse_sequence(samples, framerate, start_pos, max_pulses=50):
    """Detecta una secuencia de pulsos y retorna sus anchos en T-states"""
    threshold = (samples.max() + samples.min()) / 2
    binary = (samples[start_pos:start_pos+5000] > threshold).astype(int)
    edges = np.where(np.diff(binary) != 0)[0]
    
    if len(edges) < 2:
        return []
    
    widths = np.diff(edges)
    widths_t = widths / framerate * 1e6 * 3.5  # Convertir a T-states
    
    return widths_t[:max_pulses]

def main():
    import os
    wav_file = os.path.join(os.path.dirname(__file__), 'BCquest.wav')
    with wave.open(wav_file, 'rb') as wav:
        framerate = wav.getframerate()
        nframes = wav.getnframes()
        raw_data = wav.readframes(nframes)
        
        samples = np.frombuffer(raw_data, dtype=np.uint8).astype(np.int16) - 128
        
    threshold = (samples.max() + samples.min()) / 2
    binary_signal = (samples > threshold).astype(int)
    edges = np.where(np.diff(binary_signal) != 0)[0]
    pulse_widths = np.diff(edges)
    widths_t = pulse_widths / framerate * 1e6 * 3.5
    
    print("=" * 80)
    print("ESTRUCTURA DEL BLOQUE GDB EN BC'S QUEST")
    print("=" * 80)
    
    # 1. PILOT TONE
    print("\n=== PILOT TONE (primeros pulsos) ===")
    pilot_pulses = widths_t[:100]
    pilot_mean = pilot_pulses.mean()
    print(f"Primeros 100 pulsos:")
    print(f"  Ancho promedio: {pilot_mean:.0f} T-states")
    print(f"  Esperado: 2168 T-states (según TZX)")
    print(f"  Diferencia: {pilot_mean - 2168:.0f} T-states")
    print(f"  Consistencia: {pilot_pulses.std():.2f} T-states")
    
    # Contar cuántos pulsos de pilot hay (~2168T)
    pilot_count = 0
    for w in widths_t:
        if 2100 < w < 2250:  # Rango de tolerancia
            pilot_count += 1
        else:
            break
    
    print(f"\nTotal pulsos pilot detectados: {pilot_count}")
    print(f"  Esperado según TZX: 3223 x 2 = 6446 (Symbol 0 con 2 pulsos, 1 es 0)")
    
    # 2. SYNC PULSES
    print("\n=== SYNC PULSES (después del pilot) ===")
    sync_start = pilot_count
    sync_pulses = widths_t[sync_start:sync_start+20]
    
    print(f"Pulsos después del pilot (posición {sync_start}):")
    for i, w in enumerate(sync_pulses[:10]):
        print(f"  Pulso {i}: {w:.0f} T")
    
    # Según TZX: Symbol 1 = [667, 735], Symbol 2 = [780, 1170] x4
    print(f"\nEsperado según TZX:")
    print(f"  Symbol 1 (sync1) x1: [667T, 735T]")
    print(f"  Symbol 2 (sync2) x4: [780T, 1170T] x 4 repeticiones")
    print(f"  Total sync: 2 + 8 = 10 pulsos")
    
    # 3. DATA STREAM
    data_start = sync_start + 10
    print(f"\n=== DATA STREAM (después de sync, posición {data_start}) ===")
    data_pulses = widths_t[data_start:data_start+100]
    
    # Separar en dos grupos: bit 0 y bit 1
    short_pulses = []
    long_pulses = []
    
    for w in data_pulses:
        if 700 < w < 900:
            short_pulses.append(w)
        elif 1400 < w < 1700:
            long_pulses.append(w)
    
    if short_pulses:
        print(f"Pulsos cortos (bit 0):")
        print(f"  Cantidad: {len(short_pulses)}")
        print(f"  Promedio: {np.mean(short_pulses):.0f} T")
        print(f"  Esperado: 780 T (Symbol 0 = [780, 780])")
    
    if long_pulses:
        print(f"\nPulsos largos (bit 1):")
        print(f"  Cantidad: {len(long_pulses)}")
        print(f"  Promedio: {np.mean(long_pulses):.0f} T")
        print(f"  Esperado: 780 T (primer pulso), 1560 T (segundo pulso)")
    
    # 4. PAUSAS
    print(f"\n=== PAUSAS ===")
    large_gaps = pulse_widths[pulse_widths > 1000]
    
    for idx, gap in enumerate(large_gaps):
        gap_ms = gap / framerate * 1000
        position = np.where(pulse_widths == gap)[0][0]
        print(f"Pausa {idx+1}:")
        print(f"  Posición: pulso {position}")
        print(f"  Duración: {gap_ms:.2f} ms")
        
        # Analizar nivel antes y después
        gap_pos = edges[position]
        before = binary_signal[max(0, gap_pos-10):gap_pos].mean()
        after = binary_signal[gap_pos:gap_pos+10].mean()
        
        print(f"  Nivel antes: {'HIGH' if before > 0.5 else 'LOW'}")
        print(f"  Nivel después: {'HIGH' if after > 0.5 else 'LOW'}")
    
    # 5. TERMINACIÓN
    print(f"\n=== TERMINACIÓN DEL BLOQUE ===")
    last_1000_samples = samples[-1000:]
    last_mean = last_1000_samples.mean()
    last_std = last_1000_samples.std()
    
    print(f"Últimos 1000 samples:")
    print(f"  Nivel medio: {last_mean:.2f}")
    print(f"  Desviación: {last_std:.2f}")
    print(f"  Estado: {'SILENCIO COMPLETO' if last_std < 1 else 'SEÑAL'}")
    
    if last_std < 1:
        nivel_final = "HIGH (positivo)" if last_mean > 0 else "LOW (negativo o cero)"
        print(f"  Nivel final: {nivel_final}")
    
    # 6. TRANSICIÓN PILOT -> SYNC
    print(f"\n=== TRANSICIÓN PILOT -> SYNC ===")
    trans_start = max(0, pilot_count - 5)
    trans_end = pilot_count + 5
    trans_pulses = widths_t[trans_start:trans_end]
    
    print(f"Pulsos alrededor de la transición (posición {pilot_count}):")
    for i, w in enumerate(trans_pulses):
        pos = trans_start + i
        marker = " <-- TRANSICIÓN" if pos == pilot_count else ""
        print(f"  Pulso {pos}: {w:.0f} T{marker}")

if __name__ == '__main__':
    main()
