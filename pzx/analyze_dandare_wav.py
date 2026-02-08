#!/usr/bin/env python3
"""
Analiza el WAV de Dan Dare 2 para ver las transiciones y silencios
"""

import wave
import struct
import sys

def analyze_wav(filename):
    with wave.open(filename, 'rb') as wav:
        nchannels = wav.getnchannels()
        sampwidth = wav.getsampwidth()
        framerate = wav.getframerate()
        nframes = wav.getnframes()
        
        print(f"=== Análisis de {filename} ===")
        print(f"Canales: {nchannels}")
        print(f"Sample width: {sampwidth} bytes")
        print(f"Framerate: {framerate} Hz")
        print(f"Frames: {nframes}")
        print(f"Duración: {nframes/framerate:.2f} segundos")
        print()
        
        # Leer todos los datos
        raw_data = wav.readframes(nframes)
        
        if sampwidth == 1:
            samples = list(raw_data)
            # Convertir de unsigned a signed
            samples = [s - 128 for s in samples]
        elif sampwidth == 2:
            samples = list(struct.unpack(f'<{nframes * nchannels}h', raw_data))
        else:
            print(f"Unsupported sample width: {sampwidth}")
            return
        
        # Si es estéreo, tomar solo canal izquierdo
        if nchannels == 2:
            samples = samples[::2]
        
        # Detectar nivel (HIGH/LOW) usando umbral
        threshold = 0
        levels = ['H' if s > threshold else 'L' for s in samples]
        
        # Buscar transiciones (cambios de nivel)
        transitions = []
        current_level = levels[0]
        current_start = 0
        
        for i, level in enumerate(levels):
            if level != current_level:
                duration_samples = i - current_start
                duration_us = (duration_samples * 1000000) / framerate
                transitions.append({
                    'start': current_start,
                    'end': i,
                    'level': current_level,
                    'duration_samples': duration_samples,
                    'duration_us': duration_us
                })
                current_level = level
                current_start = i
        
        # Añadir último segmento
        transitions.append({
            'start': current_start,
            'end': len(samples),
            'level': current_level,
            'duration_samples': len(samples) - current_start,
            'duration_us': ((len(samples) - current_start) * 1000000) / framerate
        })
        
        print(f"Total transiciones: {len(transitions)}")
        print()
        
        # Buscar silencios (duraciones > 100ms = 100000us)
        SILENCE_THRESHOLD_US = 50000  # 50ms para considerar silencio
        
        print("=== SILENCIOS DETECTADOS (>50ms) ===")
        silence_count = 0
        for i, t in enumerate(transitions):
            if t['duration_us'] > SILENCE_THRESHOLD_US:
                silence_count += 1
                time_sec = (t['start'] / framerate)
                print(f"Silencio #{silence_count} @ {time_sec:.3f}s:")
                print(f"  Nivel: {t['level']}, Duración: {t['duration_us']/1000:.1f}ms")
                
                # Mostrar contexto: pulsos antes y después
                if i > 0:
                    prev = transitions[i-1]
                    print(f"  Pulso ANTERIOR: nivel={prev['level']}, dur={prev['duration_us']:.1f}us")
                if i < len(transitions) - 1:
                    next_t = transitions[i+1]
                    print(f"  Pulso SIGUIENTE: nivel={next_t['level']}, dur={next_t['duration_us']:.1f}us")
                print()
        
        # Analizar zona específica del bloque 6->7 (basado en pausas de 1776ms tras bloque 6)
        print("\n=== BÚSQUEDA DE TRANSICIÓN BLOQUE 6->7 ===")
        print("(Buscando pausa de ~1776ms)")
        
        for i, t in enumerate(transitions):
            # Buscar pausas cercanas a 1776ms
            if 1500000 < t['duration_us'] < 2000000:  # Entre 1.5s y 2s
                time_sec = (t['start'] / framerate)
                print(f"\n*** PAUSA ENCONTRADA @ {time_sec:.3f}s ***")
                print(f"  Nivel: {t['level']}, Duración: {t['duration_us']/1000:.1f}ms")
                
                # Mostrar últimos 20 pulsos antes del silencio
                print("\n  Últimos 20 pulsos ANTES del silencio:")
                start_idx = max(0, i - 20)
                for j in range(start_idx, i):
                    pt = transitions[j]
                    print(f"    [{j-i}] {pt['level']}: {pt['duration_us']:.1f}us")
                
                # Mostrar primeros 20 pulsos después del silencio
                print("\n  Primeros 20 pulsos DESPUÉS del silencio:")
                end_idx = min(len(transitions), i + 21)
                for j in range(i + 1, end_idx):
                    pt = transitions[j]
                    print(f"    [{j-i}] {pt['level']}: {pt['duration_us']:.1f}us")

if __name__ == "__main__":
    wav_file = r"pzxsamples\gdb\Dan Dare 2.wav"
    analyze_wav(wav_file)
