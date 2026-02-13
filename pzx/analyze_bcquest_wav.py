#!/usr/bin/env python3
"""
Analiza el WAV de referencia de BC's Quest generado por una aplicación robusta
para entender cómo debe funcionar correctamente el powaDCR
"""
import wave
import struct
import numpy as np

def analyze_wav(filename):
    print("=" * 80)
    print(f"ANÁLISIS DE {filename}")
    print("=" * 80)
    
    with wave.open(filename, 'rb') as wav:
        # Información básica del WAV
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        framerate = wav.getframerate()
        nframes = wav.getnframes()
        
        print(f"\n=== INFORMACIÓN BÁSICA ===")
        print(f"Canales: {channels}")
        print(f"Sample width: {sample_width} bytes ({sample_width * 8} bits)")
        print(f"Sample rate: {framerate} Hz")
        print(f"Total frames: {nframes}")
        print(f"Duración: {nframes / framerate:.2f} segundos")
        
        # Leer todas las muestras
        raw_data = wav.readframes(nframes)
        
        # Convertir a array de numpy según el sample width
        if sample_width == 1:
            samples = np.frombuffer(raw_data, dtype=np.uint8)
            samples = samples.astype(np.int16) - 128  # Convertir a signed
        elif sample_width == 2:
            samples = np.frombuffer(raw_data, dtype=np.int16)
        else:
            print(f"ERROR: Sample width {sample_width} no soportado")
            return
        
        # Si es estéreo, tomar solo un canal
        if channels == 2:
            samples = samples[::2]  # Tomar canal izquierdo
            print(f"Usando canal izquierdo (samples: {len(samples)})")
        
        print(f"\n=== ANÁLISIS DE SEÑAL ===")
        print(f"Valor mínimo: {samples.min()}")
        print(f"Valor máximo: {samples.max()}")
        print(f"Valor medio: {samples.mean():.2f}")
        
        # Detectar transiciones (cruces por cero o cambios significativos)
        # Umbral para detectar nivel alto/bajo
        threshold = (samples.max() + samples.min()) / 2
        
        # Binarizar la señal
        binary_signal = (samples > threshold).astype(int)
        
        # Detectar flancos (transiciones)
        edges = np.diff(binary_signal)
        rising_edges = np.where(edges == 1)[0]
        falling_edges = np.where(edges == -1)[0]
        
        total_edges = len(rising_edges) + len(falling_edges)
        
        print(f"\n=== TRANSICIONES ===")
        print(f"Flancos ascendentes: {len(rising_edges)}")
        print(f"Flancos descendentes: {len(falling_edges)}")
        print(f"Total transiciones: {total_edges}")
        
        # Calcular anchos de pulso entre transiciones
        all_edges = np.sort(np.concatenate([rising_edges, falling_edges]))
        pulse_widths = np.diff(all_edges)
        
        if len(pulse_widths) > 0:
            print(f"\n=== ANCHOS DE PULSO ===")
            print(f"Mínimo: {pulse_widths.min()} samples ({pulse_widths.min() / framerate * 1e6:.2f} µs)")
            print(f"Máximo: {pulse_widths.max()} samples ({pulse_widths.max() / framerate * 1e6:.2f} µs)")
            print(f"Promedio: {pulse_widths.mean():.2f} samples ({pulse_widths.mean() / framerate * 1e6:.2f} µs)")
            print(f"Mediana: {np.median(pulse_widths):.2f} samples ({np.median(pulse_widths) / framerate * 1e6:.2f} µs)")
            
            # Histograma de anchos de pulso más comunes (agrupados)
            # Agrupar por rangos de ~10 samples
            bins = np.arange(0, pulse_widths.max() + 10, 10)
            hist, bin_edges = np.histogram(pulse_widths, bins=bins)
            
            print(f"\n=== ANCHOS DE PULSO MÁS COMUNES (agrupados en rangos de 10 samples) ===")
            # Ordenar por frecuencia
            sorted_indices = np.argsort(hist)[::-1]
            for i in sorted_indices[:10]:  # Top 10
                if hist[i] > 0:
                    mid_samples = (bin_edges[i] + bin_edges[i+1]) / 2
                    mid_us = mid_samples / framerate * 1e6
                    mid_tstates = mid_us * 3.5  # 3.5 MHz ZX Spectrum
                    print(f"  {int(bin_edges[i]):4d}-{int(bin_edges[i+1]):4d} samples "
                          f"({mid_us:6.2f}µs, ~{int(mid_tstates):4d}T): {hist[i]:6d} pulsos")
        
        # Buscar pausas largas (más de 1000 samples sin transición)
        large_gaps = pulse_widths[pulse_widths > 1000]
        if len(large_gaps) > 0:
            print(f"\n=== PAUSAS LARGAS (>1000 samples) ===")
            print(f"Encontradas: {len(large_gaps)}")
            for idx, gap in enumerate(large_gaps[:5]):  # Primeras 5
                gap_ms = gap / framerate * 1000
                print(f"  Pausa {idx+1}: {gap} samples ({gap_ms:.2f} ms)")
        
        # Analizar el inicio (primeros 10000 samples = pilot tone)
        print(f"\n=== ANÁLISIS DEL INICIO (PILOT TONE) ===")
        pilot_samples = min(10000, len(samples))
        pilot_edges = all_edges[all_edges < pilot_samples]
        
        if len(pilot_edges) > 10:
            pilot_widths = np.diff(pilot_edges)
            print(f"Transiciones en pilot: {len(pilot_edges)}")
            print(f"Ancho promedio: {pilot_widths.mean():.2f} samples")
            print(f"  = {pilot_widths.mean() / framerate * 1e6:.2f} µs")
            print(f"  ≈ {pilot_widths.mean() / framerate * 1e6 * 3.5:.0f} T-states")
            
            # Verificar consistencia del pilot
            pilot_std = pilot_widths.std()
            print(f"Desviación estándar: {pilot_std:.2f} samples (consistencia: {'BUENA' if pilot_std < 5 else 'MALA'})")
        
        # Analizar el final (últimos 10000 samples = pausa final)
        print(f"\n=== ANÁLISIS DEL FINAL ===")
        final_samples = min(10000, len(samples))
        final_signal = samples[-final_samples:]
        final_mean = final_signal.mean()
        final_std = final_signal.std()
        
        print(f"Últimos {final_samples} samples:")
        print(f"  Nivel medio: {final_mean:.2f}")
        print(f"  Desviación estándar: {final_std:.2f}")
        print(f"  Estado: {'SILENCIO' if final_std < 100 else 'SEÑAL ACTIVA'}")
        
        if final_std < 100:
            # Detectar si es nivel alto o bajo
            nivel = "ALTO" if final_mean > 0 else "BAJO"
            print(f"  Nivel de silencio: {nivel}")
        
        # Buscar sync pulses (típicamente después del pilot, antes de datos)
        # Sync es más corto que pilot
        if len(pulse_widths) > 100:
            # Asumir pilot en primeros 3223*2 = 6446 pulsos aprox
            sync_start = 6400
            sync_end = 6450
            if sync_end < len(pulse_widths):
                sync_widths = pulse_widths[sync_start:sync_end]
                print(f"\n=== POSIBLES SYNC PULSES (después del pilot) ===")
                print(f"Analizando pulsos {sync_start}-{sync_end}")
                for idx, width in enumerate(sync_widths[:10]):
                    width_us = width / framerate * 1e6
                    width_t = width_us * 3.5
                    print(f"  Pulso {idx}: {width:.0f} samples ({width_us:.2f}µs, {width_t:.0f}T)")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        analyze_wav(sys.argv[1])
    else:
        analyze_wav('BCquest.wav')
