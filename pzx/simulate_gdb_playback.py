#!/usr/bin/env python3
"""
Simula la reproducción del bloque GDB de Basil para verificar el audio generado
"""
import struct
import math
import os

filepath = 'pzxsamples/gdb/Basil the Great Mouse Detective.tzx'

with open(filepath, 'rb') as f:
    data = f.read()

# Analizar TODOS los bloques GDB
print(f"Archivo: {filepath}")
print(f"Tamaño: {len(data)} bytes\n")

# Buscar todos los bloques GDB (ID 0x19)
offset = 10  # Skip header
block_num = 0
gdb_blocks = []

while offset < len(data):
    block_id = data[offset]
    
    if block_id == 0x19:  # GDB
        gdb_blocks.append((block_num, offset))
        block_size = struct.unpack('<I', data[offset+1:offset+5])[0]
        offset += 5 + block_size
    elif block_id == 0x10:  # Standard
        length = struct.unpack('<H', data[offset+3:offset+5])[0]
        offset += 5 + length
    elif block_id == 0x11:  # Turbo
        length = struct.unpack('<I', data[offset+16:offset+19] + b'\x00')[0]
        offset += 19 + length
    elif block_id == 0x12:  # Pure Tone
        offset += 5
    elif block_id == 0x13:  # Pulse Sequence
        num = data[offset+1]
        offset += 2 + num * 2
    elif block_id == 0x14:  # Pure Data
        length = struct.unpack('<I', data[offset+8:offset+11] + b'\x00')[0]
        offset += 11 + length
    elif block_id == 0x20:  # Pause
        offset += 3
    elif block_id == 0x21:  # Group Start
        length = data[offset+1]
        offset += 2 + length
    elif block_id == 0x22:  # Group End
        offset += 1
    elif block_id == 0x30:  # Text
        length = data[offset+1]
        offset += 2 + length
    elif block_id == 0x32:  # Archive Info
        length = struct.unpack('<H', data[offset+1:offset+3])[0]
        offset += 3 + length
    elif block_id == 0x33:  # Hardware
        num = data[offset+1]
        offset += 2 + num * 3
    elif block_id == 0x35:  # Custom Info
        length = struct.unpack('<I', data[offset+17:offset+21])[0]
        offset += 21 + length
    else:
        print(f"Unknown block ID 0x{block_id:02X} at offset {offset}")
        break
    
    block_num += 1

print(f"Encontrados {len(gdb_blocks)} bloques GDB:\n")

# Analizar el primer bloque GDB en detalle
for gdb_num, (block_idx, gdb_offset) in enumerate(gdb_blocks[:3]):  # Solo primeros 3
    print(f"{'='*60}")
    print(f"GDB #{gdb_num} (Bloque {block_idx}) @ offset 0x{gdb_offset:06X}")
    print(f"{'='*60}")
    
    # Leer parámetros
    block_size = struct.unpack('<I', data[gdb_offset+1:gdb_offset+5])[0]
    pause = struct.unpack('<H', data[gdb_offset+5:gdb_offset+7])[0]
    TOTP = struct.unpack('<I', data[gdb_offset+7:gdb_offset+11])[0]
    NPP = data[gdb_offset+11]
    ASP = data[gdb_offset+12]
    TOTD = struct.unpack('<I', data[gdb_offset+13:gdb_offset+17])[0]
    NPD = data[gdb_offset+17]
    ASD = data[gdb_offset+18]
    
    print(f"\nParámetros:")
    print(f"  Block size: {block_size}, Pause: {pause}ms")
    print(f"  TOTP={TOTP}, NPP={NPP}, ASP={ASP}")
    print(f"  TOTD={TOTD}, NPD={NPD}, ASD={ASD}")
    
    # Calcular NB (como en el código C++)
    NB = 0
    tmpASD = ASD - 1
    while tmpASD > 0:
        NB += 1
        tmpASD >>= 1
    
    print(f"  NB (bits per data symbol): {NB}")
    
    # Leer definiciones de símbolos pilot
    pos = gdb_offset + 19
    symdef_pilot = []
    for s in range(ASP):
        flag = data[pos]
        pos += 1
        pulses = []
        for p in range(NPP):
            pulse = struct.unpack('<H', data[pos:pos+2])[0]
            pulses.append(pulse)
            pos += 2
        symdef_pilot.append({'flag': flag, 'pulses': pulses})
    
    print(f"\nSYMDEF Pilot (ASP={ASP}):")
    for s, sym in enumerate(symdef_pilot):
        polarity = ['toggle', 'keep', 'force_low', 'force_high'][sym['flag'] & 0x03]
        non_zero = [p for p in sym['pulses'] if p != 0]
        print(f"  Sym[{s}]: {polarity}, pulses={non_zero}")
    
    # Leer PRLE pilot stream
    prle_pilot = []
    for t in range(TOTP):
        sym = data[pos]
        pos += 1
        rep = struct.unpack('<H', data[pos:pos+2])[0]
        pos += 2
        prle_pilot.append({'symbol': sym, 'repeat': rep})
    
    print(f"\nPRLE Pilot Stream (TOTP={TOTP}):")
    for t, entry in enumerate(prle_pilot):
        print(f"  Entry[{t}]: symbol={entry['symbol']}, repeat={entry['repeat']}")
    
    # Leer definiciones de símbolos data
    symdef_data = []
    for s in range(ASD):
        flag = data[pos]
        pos += 1
        pulses = []
        for p in range(NPD):
            pulse = struct.unpack('<H', data[pos:pos+2])[0]
            pulses.append(pulse)
            pos += 2
        symdef_data.append({'flag': flag, 'pulses': pulses})
    
    print(f"\nSYMDEF Data (ASD={ASD}):")
    for s, sym in enumerate(symdef_data):
        polarity = ['toggle', 'keep', 'force_low', 'force_high'][sym['flag'] & 0x03]
        non_zero = [p for p in sym['pulses'] if p != 0]
        print(f"  Sym[{s}]: {polarity}, pulses={non_zero}")
    
    # Data stream
    DS = math.ceil((NB * TOTD) / 8.0) if NB > 0 else 0
    print(f"\nData Stream: {DS} bytes @ offset 0x{pos:06X}")
    
    # Simular lectura de primeros 32 símbolos como en el código C++
    print(f"\nSimulación de lectura de primeros 32 símbolos:")
    datastream = data[pos:pos+DS]
    
    bit_index = 0
    max_bits = NB * TOTD
    symbols_read = 0
    
    # Contar cuántos pulsos se generarían
    total_pulses = 0
    total_tstates = 0
    
    # Primero contar pulsos del pilot
    for entry in prle_pilot:
        sym_id = entry['symbol']
        repeat = entry['repeat']
        sym = symdef_pilot[sym_id]
        for _ in range(repeat):
            for pulse in sym['pulses']:
                if pulse == 0:
                    break
                total_pulses += 1
                total_tstates += pulse
    
    print(f"\nPilot/Sync:")
    print(f"  Total pulses: {total_pulses}")
    print(f"  Total T-states: {total_tstates}")
    print(f"  Duración aprox: {total_tstates / 3500000:.3f}s")
    
    # Ahora simular data stream
    data_pulses = 0
    data_tstates = 0
    
    while symbols_read < min(TOTD, 100000) and bit_index < max_bits:
        symbolID = 0
        for bit in range(NB):
            if bit_index >= max_bits:
                break
            byte_idx = bit_index // 8
            bit_pos = 7 - (bit_index % 8)  # MSB first
            if byte_idx < len(datastream):
                bit_value = (datastream[byte_idx] >> bit_pos) & 1
                symbolID = (symbolID << 1) | bit_value
            bit_index += 1
        
        if symbolID < ASD:
            sym = symdef_data[symbolID]
            for pulse in sym['pulses']:
                if pulse == 0:
                    break
                data_pulses += 1
                data_tstates += pulse
        
        symbols_read += 1
        
        # Log primeros símbolos
        if symbols_read <= 32:
            byte_idx = (bit_index - NB) // 8
            if byte_idx < len(datastream):
                print(f"  Symbol #{symbols_read-1}: ID={symbolID}, byte=0x{datastream[byte_idx]:02X}")
    
    print(f"\nData Stream (primeros {symbols_read} símbolos):")
    print(f"  Total pulses: {data_pulses}")
    print(f"  Total T-states: {data_tstates}")
    print(f"  Duración aprox: {data_tstates / 3500000:.3f}s")
    
    print(f"\n{'='*60}\n")
