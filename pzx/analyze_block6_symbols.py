#!/usr/bin/env python3
"""Análisis detallado del bloque 6 (GDB) de Dan Dare 2"""
import struct
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")

with open(tzx_file, 'rb') as f:
    data = f.read()

# Bloque 6 está en offset 10434
offset = 10434
block_id = data[offset]
print(f'Block ID: 0x{block_id:02X}')

if block_id == 0x19:  # GDB
    block_len = struct.unpack_from('<I', data, offset+1)[0]
    pause = struct.unpack_from('<H', data, offset+5)[0]
    totp = struct.unpack_from('<I', data, offset+7)[0]
    npp = data[offset+11]
    asp = data[offset+12]
    totd = struct.unpack_from('<I', data, offset+13)[0]
    npd = data[offset+17]
    asd = data[offset+18]
    
    print(f'Block length: {block_len}')
    print(f'Pause: {pause}ms')
    print(f'TOTP (pilot/sync pulses): {totp}')
    print(f'NPP (num pilot symbols): {npp}')
    print(f'ASP (alphabet size pilot): {asp}')
    print(f'TOTD (data pulses): {totd}')
    print(f'NPD (num data symbols): {npd}')
    print(f'ASD (alphabet size data): {asd}')
    
    # Leer tabla de símbolos pilot
    print(f'\n=== PILOT SYMBOL TABLE (ASP={asp} symbols) ===')
    sym_offset = offset + 19
    for sym_idx in range(asp):
        sym_flags = data[sym_offset]
        num_pulses = struct.unpack_from('<H', data, sym_offset+1)[0]
        
        # Leer pulsos de este símbolo
        pulses = []
        for p in range(num_pulses):
            pulse_dur = struct.unpack_from('<H', data, sym_offset + 3 + p*2)[0]
            pulses.append(pulse_dur)
        
        # Convertir a microsegundos (T-states a 3.5MHz)
        pulses_us = [p / 3.5 for p in pulses]
        
        print(f'Symbol {sym_idx}: flags=0x{sym_flags:02X}, num_pulses={num_pulses}')
        print(f'  T-states: {pulses}')
        print(f'  Microsec: {[f"{p:.1f}" for p in pulses_us]}')
        print(f'  Total T-states: {sum(pulses)}, Total us: {sum(pulses)/3.5:.1f}')
        
        sym_offset += 3 + num_pulses * 2
    
    # Leer tabla de símbolos data
    print(f'\n=== DATA SYMBOL TABLE (ASD={asd} symbols) ===')
    for sym_idx in range(asd):
        sym_flags = data[sym_offset]
        num_pulses = struct.unpack_from('<H', data, sym_offset+1)[0]
        
        # Leer pulsos de este símbolo
        pulses = []
        for p in range(num_pulses):
            pulse_dur = struct.unpack_from('<H', data, sym_offset + 3 + p*2)[0]
            pulses.append(pulse_dur)
        
        # Convertir a microsegundos (T-states a 3.5MHz)
        pulses_us = [p / 3.5 for p in pulses]
        
        print(f'Symbol {sym_idx}: flags=0x{sym_flags:02X}, num_pulses={num_pulses}')
        print(f'  T-states: {pulses}')
        print(f'  Microsec: {[f"{p:.1f}" for p in pulses_us]}')
        print(f'  Total T-states: {sum(pulses)}, Total us: {sum(pulses)/3.5:.1f}')
        
        sym_offset += 3 + num_pulses * 2
    
    # Leer PRLE (pilot stream)
    print(f'\n=== PRLE PILOT STREAM ===')
    prle_offset = sym_offset
    total_pilot_symbols = 0
    total_pilot_pulses = 0
    
    remaining_totp = totp
    while remaining_totp > 0:
        symbol = data[prle_offset]
        rep_count = struct.unpack_from('<H', data, prle_offset+1)[0]
        total_pilot_symbols += rep_count
        
        # Calcular pulsos basado en el símbolo
        # Necesitamos saber cuántos pulsos tiene cada símbolo
        # Volver a calcular
        temp_offset = offset + 19
        sym_pulses = []
        for s in range(asp):
            sp_flags = data[temp_offset]
            sp_count = struct.unpack_from('<H', data, temp_offset+1)[0]
            sym_pulses.append(sp_count)
            temp_offset += 3 + sp_count * 2
        
        pulses_for_symbol = sym_pulses[symbol] if symbol < len(sym_pulses) else 0
        total_pilot_pulses += rep_count * pulses_for_symbol
        
        print(f'  Symbol {symbol} x {rep_count} (pulses per sym: {pulses_for_symbol}) = {rep_count * pulses_for_symbol} pulses')
        
        remaining_totp -= rep_count
        prle_offset += 3
    
    print(f'\nTotal pilot symbols: {total_pilot_symbols}')
    print(f'Total pilot pulses: {total_pilot_pulses}')
    
    # Ahora ver los datos
    print(f'\n=== DATA STREAM ===')
    print(f'TOTD (total data symbols): {totd}')
    print(f'NPD (bits per symbol): {npd}')
    print(f'ASD (alphabet size): {asd}')
    
    # Calcular pulsos por símbolo de datos
    temp_offset = offset + 19
    for s in range(asp):
        sp_count = struct.unpack_from('<H', data, temp_offset+1)[0]
        temp_offset += 3 + sp_count * 2
    
    data_sym_pulses = []
    for s in range(asd):
        sp_count = struct.unpack_from('<H', data, temp_offset+1)[0]
        data_sym_pulses.append(sp_count)
        temp_offset += 3 + sp_count * 2
    
    print(f'Data symbol pulses: {data_sym_pulses}')
    
    # Calcular total de pulsos de datos
    # Cada símbolo de datos tiene un número fijo de pulsos
    # Asumiendo 2 pulsos por símbolo (típico para bits 0/1)
    total_data_pulses = totd * data_sym_pulses[0]  # Asumiendo todos los símbolos tienen mismos pulsos
    print(f'Total data pulses (approx): {total_data_pulses}')
    
    print(f'\n=== RESUMEN TOTAL ===')
    print(f'Pilot pulses: {total_pilot_pulses}')
    print(f'Data pulses: {total_data_pulses}')
    grand_total = total_pilot_pulses + total_data_pulses
    print(f'GRAND TOTAL: {grand_total} pulses')
    print(f'Paridad: {"PAR (termina igual que empezó)" if grand_total % 2 == 0 else "IMPAR (termina invertido)"}')
    
    # El pulso largo de 16ms que vemos en el WAV...
    # 16000us = 56000 T-states
    print(f'\n=== BUSCANDO PULSO LARGO (16ms = ~56000 T-states) ===')
    
    # Revisar si hay algún símbolo con pulso muy largo
    temp_offset = offset + 19
    for s in range(asp):
        sp_flags = data[temp_offset]
        sp_count = struct.unpack_from('<H', data, temp_offset+1)[0]
        for p in range(sp_count):
            pulse = struct.unpack_from('<H', data, temp_offset + 3 + p*2)[0]
            if pulse > 10000:  # Más de 10000 T-states
                print(f'  Pilot symbol {s}, pulse {p}: {pulse} T-states = {pulse/3.5:.1f}us')
        temp_offset += 3 + sp_count * 2
