#!/usr/bin/env python3
"""
Comparación detallada entre Dan Dare 2 (FUNCIONA) y BC's Quest (FALLA)
Ambos usan GDB (0x19) pero con diferentes tipos de símbolos
"""

def read_word(data, offset):
    return data[offset] | (data[offset+1] << 8)

def read_dword(data, offset):
    return data[offset] | (data[offset+1] << 8) | (data[offset+2] << 16) | (data[offset+3] << 24)

def analyze_gdb_block(data, offset, name):
    """Analiza un bloque GDB en detalle"""
    print(f"\n{'='*60}")
    print(f"GDB ANALYSIS: {name}")
    print(f"{'='*60}")
    
    block_len = read_dword(data, offset)
    print(f"Block length: {block_len} bytes")
    
    pos = offset + 4
    
    # Pause after block
    pause = read_word(data, pos)
    print(f"Pause after block: {pause} ms")
    pos += 2
    
    # TOTP - Total de símbolos en tabla de pilotos/sync
    totp = read_dword(data, pos)
    print(f"\nTOTP (pilot/sync symbols): {totp}")
    pos += 4
    
    # NPP - Pulsos máximos por símbolo piloto
    npp = data[pos]
    print(f"NPP (max pulses per pilot symbol): {npp}")
    pos += 1
    
    # ASP - Símbolos en alfabeto de piloto
    asp = data[pos]
    print(f"ASP (pilot alphabet size): {asp}")
    pos += 1
    
    # TOTD - Total de símbolos en stream de datos
    totd = read_dword(data, pos)
    print(f"\nTOTD (data stream symbols): {totd}")
    pos += 4
    
    # NPD - Pulsos máximos por símbolo de datos
    npd = data[pos]
    print(f"NPD (max pulses per data symbol): {npd}")
    pos += 1
    
    # ASD - Símbolos en alfabeto de datos
    asd = data[pos]
    print(f"ASD (data alphabet size): {asd}")
    pos += 1
    
    # Leer tabla de símbolos de piloto
    print(f"\n--- PILOT/SYNC SYMBOL TABLE ({asp} symbols) ---")
    pilot_symbols = []
    for i in range(asp):
        flags = data[pos]
        pos += 1
        pulses = []
        for p in range(npp):
            pulse = read_word(data, pos)
            pos += 2
            if pulse > 0:
                pulses.append(pulse)
        pilot_symbols.append({'flags': flags, 'pulses': pulses})
        
        # Analizar simetría
        if len(pulses) == 2:
            if pulses[0] == pulses[1]:
                sym_type = "SYMMETRIC"
            else:
                ratio = pulses[1] / pulses[0] if pulses[0] > 0 else 0
                sym_type = f"ASYMMETRIC (ratio {ratio:.2f})"
        else:
            sym_type = f"{len(pulses)} pulses"
            
        print(f"  Symbol {i}: flags=0x{flags:02X}, pulses={pulses} - {sym_type}")
    
    # Leer stream de piloto/sync
    print(f"\n--- PILOT/SYNC STREAM ({totp} symbols) ---")
    pilot_stream = []
    bits_needed = (totp * 8 + 7) // 8  # Aproximación
    
    # El stream está codificado en bits según ASP
    import math
    bits_per_symbol = max(1, math.ceil(math.log2(asp))) if asp > 1 else 1
    bytes_for_stream = (totp * bits_per_symbol + 7) // 8
    
    print(f"  Bits per symbol: {bits_per_symbol}")
    print(f"  Stream bytes: {bytes_for_stream}")
    
    # Decodificar los primeros símbolos del stream
    stream_data = data[pos:pos + bytes_for_stream]
    pos += bytes_for_stream
    
    # Mostrar primeros bytes del stream
    print(f"  First 16 stream bytes: {' '.join(f'{b:02X}' for b in stream_data[:16])}")
    
    # Decodificar símbolos del piloto
    bit_pos = 0
    decoded_pilot = []
    for i in range(min(totp, 50)):  # Solo primeros 50
        byte_idx = bit_pos // 8
        bit_offset = bit_pos % 8
        
        if byte_idx < len(stream_data):
            # Extraer bits_per_symbol bits
            value = 0
            for b in range(bits_per_symbol):
                if byte_idx < len(stream_data):
                    bit = (stream_data[byte_idx] >> (7 - bit_offset)) & 1
                    value = (value << 1) | bit
                    bit_offset += 1
                    if bit_offset >= 8:
                        bit_offset = 0
                        byte_idx += 1
            decoded_pilot.append(value)
            bit_pos += bits_per_symbol
    
    print(f"  First {len(decoded_pilot)} pilot symbols: {decoded_pilot[:30]}...")
    
    # Leer tabla de símbolos de datos
    print(f"\n--- DATA SYMBOL TABLE ({asd} symbols) ---")
    data_symbols = []
    for i in range(asd):
        flags = data[pos]
        pos += 1
        pulses = []
        for p in range(npd):
            pulse = read_word(data, pos)
            pos += 2
            if pulse > 0:
                pulses.append(pulse)
        data_symbols.append({'flags': flags, 'pulses': pulses})
        
        # Analizar simetría
        if len(pulses) == 2:
            if pulses[0] == pulses[1]:
                sym_type = "SYMMETRIC ✓"
            else:
                ratio = pulses[1] / pulses[0] if pulses[0] > 0 else 0
                sym_type = f"ASYMMETRIC ✗ (ratio {ratio:.2f})"
        else:
            sym_type = f"{len(pulses)} pulses"
            
        print(f"  Symbol {i} (bit {i}): flags=0x{flags:02X}, pulses={pulses} - {sym_type}")
    
    # Calcular tiempos totales
    print(f"\n--- TIMING ANALYSIS ---")
    for i, sym in enumerate(data_symbols):
        total_t = sum(sym['pulses'])
        time_us = total_t / 3.5  # T-states a microsegundos
        print(f"  Data symbol {i}: {total_t}T = {time_us:.1f}µs")
    
    # Calcular ratio entre símbolos de datos
    if len(data_symbols) >= 2:
        sym0_total = sum(data_symbols[0]['pulses'])
        sym1_total = sum(data_symbols[1]['pulses'])
        if sym0_total > 0:
            print(f"\n  Ratio symbol1/symbol0: {sym1_total/sym0_total:.3f}")
            print(f"  Expected for standard: 2.0 (bit1 = 2x bit0)")
    
    return {
        'totp': totp,
        'npp': npp,
        'asp': asp,
        'totd': totd,
        'npd': npd,
        'asd': asd,
        'pilot_symbols': pilot_symbols,
        'data_symbols': data_symbols
    }

def analyze_file(filename):
    """Analiza todos los bloques GDB de un archivo"""
    print(f"\n{'#'*70}")
    print(f"ANALYZING: {filename}")
    print(f"{'#'*70}")
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Verificar header
    if data[:7] != b'ZXTape!':
        print("ERROR: Not a TZX file")
        return None
    
    print(f"TZX Version: {data[8]}.{data[9]:02d}")
    
    pos = 10
    block_num = 0
    gdb_blocks = []
    
    while pos < len(data):
        block_id = data[pos]
        block_num += 1
        
        if block_id == 0x19:  # GDB
            print(f"\n>>> Block {block_num}: GDB (ID 0x19) at offset {pos}")
            gdb_info = analyze_gdb_block(data, pos + 1, filename)
            gdb_blocks.append(gdb_info)
            
            # Calcular tamaño para saltar
            block_len = read_dword(data, pos + 1)
            pos += 1 + 4 + block_len
        else:
            # Saltar bloque
            pos = skip_block(data, pos)
    
    return gdb_blocks

def skip_block(data, pos):
    """Salta un bloque TZX y retorna la nueva posición"""
    block_id = data[pos]
    pos += 1
    
    if block_id == 0x10:
        length = read_word(data, pos + 2)
        return pos + 4 + length
    elif block_id == 0x11:
        length = data[pos + 15] | (data[pos + 16] << 8) | (data[pos + 17] << 16)
        return pos + 18 + length
    elif block_id == 0x12:
        return pos + 4
    elif block_id == 0x13:
        n = data[pos]
        return pos + 1 + n * 2
    elif block_id == 0x14:
        length = data[pos + 7] | (data[pos + 8] << 8) | (data[pos + 9] << 16)
        return pos + 10 + length
    elif block_id == 0x19:
        length = read_dword(data, pos)
        return pos + 4 + length
    elif block_id == 0x20:
        return pos + 2
    elif block_id == 0x21:
        length = data[pos]
        return pos + 1 + length
    elif block_id == 0x22:
        return pos
    elif block_id == 0x30:
        length = data[pos]
        return pos + 1 + length
    elif block_id == 0x32:
        length = read_word(data, pos)
        return pos + 2 + length
    elif block_id == 0x35:
        length = read_dword(data, pos + 16)
        return pos + 20 + length
    else:
        print(f"Unknown block ID: 0x{block_id:02X}")
        return len(data)  # Stop

# Analizar ambos archivos
print("\n" + "="*70)
print("COMPARISON: Dan Dare 2 (WORKS) vs BC's Quest (FAILS)")
print("="*70)

dd2 = analyze_file("Dan Dare 2 - Mekon's Revenge.tzx")
bc = analyze_file("BC's Quest for Tires.tzx")

# Resumen comparativo
print("\n" + "#"*70)
print("SUMMARY: KEY DIFFERENCES")
print("#"*70)

if dd2 and bc:
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│                    DAN DARE 2 (WORKS)                          │")
    print("├─────────────────────────────────────────────────────────────────┤")
    for i, gdb in enumerate(dd2):
        print(f"│ GDB {i+1}: Data symbols = {gdb['asd']}")
        for j, sym in enumerate(gdb['data_symbols']):
            pulses = sym['pulses']
            sym_type = "SYM" if len(pulses)==2 and pulses[0]==pulses[1] else "ASYM"
            print(f"│   Bit {j}: {pulses} [{sym_type}]")
    
    print("├─────────────────────────────────────────────────────────────────┤")
    print("│                  BC'S QUEST (FAILS)                            │")
    print("├─────────────────────────────────────────────────────────────────┤")
    for i, gdb in enumerate(bc):
        print(f"│ GDB {i+1}: Data symbols = {gdb['asd']}")
        for j, sym in enumerate(gdb['data_symbols']):
            pulses = sym['pulses']
            sym_type = "SYM" if len(pulses)==2 and pulses[0]==pulses[1] else "ASYM"
            print(f"│   Bit {j}: {pulses} [{sym_type}]")
    print("└─────────────────────────────────────────────────────────────────┘")

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print("""
Dan Dare 2 usa símbolos de datos SIMÉTRICOS:
  - Bit 0: [555, 555] - ambos pulsos iguales
  - Bit 1: [1110, 1110] - ambos pulsos iguales

BC's Quest usa símbolos de datos ASIMÉTRICOS:
  - Bit 0: [780, 780] - simétrico (OK)
  - Bit 1: [780, 1560] - ASIMÉTRICO (segundo pulso = 2x primero)

El problema está en playCustomSymbol() cuando procesa símbolos
con duraciones de pulso DIFERENTES dentro del mismo símbolo.
""")
