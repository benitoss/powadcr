#!/usr/bin/env python3
"""Análisis completo de Book of the Dead TZX - seguimiento de polaridad"""

import struct

filepath = r"pzxsamples\gdb\Book Of The Dead - Part 1 (CRL).tzx"

with open(filepath, 'rb') as f:
    data = f.read()

print(f"Archivo: {filepath}")
print(f"Tamaño: {len(data)} bytes")
print("=" * 120)

pos = 10  # Después de la cabecera
block_num = 0
level = 'LOW'  # Nivel inicial típico antes del primer bloque

def simulate_standard_block(data, pos, level):
    """Simula un bloque estándar ID 0x10 y devuelve el nivel final"""
    pause = struct.unpack('<H', data[pos+1:pos+3])[0]
    length = struct.unpack('<H', data[pos+3:pos+5])[0]
    
    # Leer flag byte
    flag_byte = data[pos+5]
    
    # Determinar número de pulsos de pilot
    if flag_byte < 128:
        pilot_pulses = 8063  # Header
    else:
        pilot_pulses = 3223  # Data
    
    # Simular pilot
    for _ in range(pilot_pulses):
        level = 'HIGH' if level == 'LOW' else 'LOW'
    
    # Simular SYNC1 y SYNC2 (2 pulsos)
    level = 'HIGH' if level == 'LOW' else 'LOW'  # SYNC1
    level = 'HIGH' if level == 'LOW' else 'LOW'  # SYNC2
    
    # Simular datos (cada byte = 8 bits, cada bit = 2 pulsos)
    data_pulses = length * 8 * 2
    for _ in range(data_pulses):
        level = 'HIGH' if level == 'LOW' else 'LOW'
    
    total_pulses = pilot_pulses + 2 + data_pulses
    
    return level, pause, length, flag_byte, pilot_pulses, total_pulses

def simulate_gdb_block(data, pos, level):
    """Simula un bloque GDB ID 0x19 y devuelve el nivel final"""
    length = struct.unpack('<I', data[pos+1:pos+5])[0]
    gdb_offset = pos + 5
    
    pause = struct.unpack('<H', data[gdb_offset:gdb_offset+2])[0]
    totp = struct.unpack('<I', data[gdb_offset+2:gdb_offset+6])[0]
    npp = data[gdb_offset+6]
    asp = data[gdb_offset+7]
    totd = struct.unpack('<I', data[gdb_offset+8:gdb_offset+12])[0]
    npd = data[gdb_offset+12]
    asd = data[gdb_offset+13]
    
    # Leer definiciones de símbolos pilot
    symdef_offset = gdb_offset + 14
    pilot_symbols = []
    for s in range(asp):
        flags = data[symdef_offset]
        pulses = []
        for p in range(npp):
            pulse_len = struct.unpack('<H', data[symdef_offset+1+p*2:symdef_offset+3+p*2])[0]
            if pulse_len > 0:
                pulses.append(pulse_len)
        pilot_symbols.append({'flags': flags, 'pulses': pulses})
        symdef_offset += 1 + npp * 2
    
    # Leer pilot stream
    pilot_stream = []
    for i in range(totp):
        symbol = data[symdef_offset]
        repeat = struct.unpack('<H', data[symdef_offset+1:symdef_offset+3])[0]
        pilot_stream.append({'symbol': symbol, 'repeat': repeat})
        symdef_offset += 3
    
    # Simular pilot/sync
    total_pilot_pulses = 0
    for entry in pilot_stream:
        sym_def = pilot_symbols[entry['symbol']]
        pulses_per_sym = len(sym_def['pulses'])
        for _ in range(entry['repeat']):
            for _ in range(pulses_per_sym):
                level = 'HIGH' if level == 'LOW' else 'LOW'
                total_pilot_pulses += 1
    
    # Simular data (si ASD > 0)
    # Por simplicidad, asumimos que cada símbolo de datos alterna
    # En realidad depende de la definición
    
    return level, pause, totp, totd, total_pilot_pulses

print(f"\n{'#':>2} | {'ID':^6} | {'Offset':^10} | {'Pause':>6} | {'Nivel Ini':^10} | {'Nivel Fin':^10} | {'Detalles'}")
print("-" * 120)

while pos < len(data):
    block_id = data[pos]
    block_start = pos
    nivel_inicial = level
    
    if block_id == 0x10:  # Standard speed data
        level_fin, pause, length, flag_byte, pilot_pulses, total_pulses = simulate_standard_block(data, pos, level)
        block_type = "Header" if flag_byte < 128 else "Data"
        detalles = f"len={length}, flag=0x{flag_byte:02X} ({block_type}), pilot={pilot_pulses}, total_pulses={total_pulses}"
        
        block_size = 5 + length
        level = level_fin
        
        print(f"{block_num:>2} | 0x{block_id:02X}   | 0x{block_start:06X}   | {pause:>6} | {nivel_inicial:^10} | {level:^10} | {detalles}")
        
        # Si pause > 0, después del silencio el nivel debería ser LOW
        # Pero esto depende de cómo lo implemente el reproductor
        if pause > 0:
            print(f"   |        |            |        | {'':^10} | {'→ LOW?':^10} | (pausa de {pause}ms - nivel podría resetearse)")
        
    elif block_id == 0x19:  # GDB
        level_fin, pause, totp, totd, total_pilot_pulses = simulate_gdb_block(data, pos, level)
        length = struct.unpack('<I', data[pos+1:pos+5])[0]
        block_size = 5 + length
        
        detalles = f"TOTP={totp}, TOTD={totd}, pilot_pulses={total_pilot_pulses}"
        
        # Nota: No simulamos completamente los datos del GDB
        level = level_fin  # Esto es solo después del pilot/sync
        
        print(f"{block_num:>2} | 0x{block_id:02X}   | 0x{block_start:06X}   | {pause:>6} | {nivel_inicial:^10} | {level:^10} | {detalles} (solo pilot/sync)")
        
        if pause > 0:
            print(f"   |        |            |        | {'':^10} | {'→ LOW?':^10} | (pausa de {pause}ms)")
        
    elif block_id == 0x32:  # Archive info
        length = struct.unpack('<H', data[pos+1:pos+3])[0]
        block_size = 3 + length
        print(f"{block_num:>2} | 0x{block_id:02X}   | 0x{block_start:06X}   | {'N/A':>6} | {nivel_inicial:^10} | {level:^10} | Archive Info")
        
    else:
        print(f"{block_num:>2} | 0x{block_id:02X}   | 0x{block_start:06X}   | {'???':>6} | {nivel_inicial:^10} | {'???':^10} | Bloque desconocido")
        break
    
    pos += block_size
    block_num += 1

print("\n" + "=" * 120)
print("ANÁLISIS DE CONTINUIDAD DE NIVEL")
print("=" * 120)
