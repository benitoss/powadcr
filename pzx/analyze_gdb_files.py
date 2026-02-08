#!/usr/bin/env python3
"""
Analiza los bloques GDB de múltiples archivos TZX para identificar diferencias
que puedan causar problemas de carga.
"""

import os
import struct

def read_byte(f):
    """Lee 1 byte"""
    return struct.unpack('<B', f.read(1))[0]

def read_word(f):
    """Lee 2 bytes (little-endian)"""
    return struct.unpack('<H', f.read(2))[0]

def read_dword(f):
    """Lee 4 bytes (little-endian)"""
    return struct.unpack('<I', f.read(4))[0]

def read_3bytes(f):
    """Lee 3 bytes (little-endian)"""
    data = f.read(3)
    return data[0] | (data[1] << 8) | (data[2] << 16)

def analyze_gdb_block(f, block_num):
    """Analiza un bloque GDB (ID 0x19) y retorna su estructura"""
    block_info = {
        'block_num': block_num,
        'offset': f.tell() - 1,  # -1 porque ya leímos el ID
    }
    
    # Tamaño del bloque (4 bytes)
    block_size = read_dword(f)
    block_info['size'] = block_size
    
    # TOTP - Número total de símbolos en el pilot/sync (2 bytes)
    totp = read_word(f)
    block_info['TOTP'] = totp
    
    # NPP - Número de pulsos por símbolo pilot (1 byte)
    npp = read_byte(f)
    block_info['NPP'] = npp
    
    # ASP - Alphabet size pilot (1 byte)
    asp = read_byte(f)
    block_info['ASP'] = asp
    
    # TOTP - Número total de símbolos en data stream (4 bytes)
    totd = read_dword(f)
    block_info['TOTD'] = totd
    
    # NPD - Número de pulsos por símbolo data (1 byte)
    npd = read_byte(f)
    block_info['NPD'] = npd
    
    # ASD - Alphabet size data (1 byte)
    asd = read_byte(f)
    block_info['ASD'] = asd
    
    # Símbolos pilot/sync (ASP símbolos)
    pilot_symbols = []
    for i in range(asp):
        symbol_flag = read_byte(f)
        num_pulses = read_word(f)
        pulses = []
        for j in range(num_pulses):
            pulse_len = read_word(f)
            pulses.append(pulse_len)
        pilot_symbols.append({
            'flag': symbol_flag,
            'num_pulses': num_pulses,
            'pulses': pulses
        })
    block_info['pilot_symbols'] = pilot_symbols
    
    # Símbolos data (ASD símbolos)
    data_symbols = []
    for i in range(asd):
        symbol_flag = read_byte(f)
        num_pulses = read_word(f)
        pulses = []
        for j in range(num_pulses):
            pulse_len = read_word(f)
            pulses.append(pulse_len)
        data_symbols.append({
            'flag': symbol_flag,
            'num_pulses': num_pulses,
            'pulses': pulses
        })
    block_info['data_symbols'] = data_symbols
    
    # PRLE pilot stream (calculamos cuántos bytes)
    pilot_stream_bits = totp
    import math
    nb_pilot = math.ceil(math.log2(asp)) if asp > 1 else 1
    pilot_stream_bytes = math.ceil((pilot_stream_bits * nb_pilot) / 8)
    block_info['pilot_stream_bytes'] = pilot_stream_bytes
    f.read(pilot_stream_bytes)  # Saltamos el pilot stream
    
    # Data stream (calculamos cuántos bytes)
    data_stream_bits = totd
    nb_data = math.ceil(math.log2(asd)) if asd > 1 else 1
    data_stream_bytes = math.ceil((data_stream_bits * nb_data) / 8)
    block_info['data_stream_bytes'] = data_stream_bytes
    f.read(data_stream_bytes)  # Saltamos el data stream
    
    # Pause (2 bytes)
    pause = read_word(f)
    block_info['pause'] = pause
    
    return block_info

def analyze_tzx_file(filepath):
    """Analiza un archivo TZX y extrae información de bloques GDB"""
    print(f"\n{'='*80}")
    print(f"Analizando: {os.path.basename(filepath)}")
    print(f"{'='*80}")
    
    with open(filepath, 'rb') as f:
        # Verificar header TZX
        header = f.read(7)
        if header != b'ZXTape!':
            print("ERROR: No es un archivo TZX válido")
            return []
        
        # Saltar byte 0x1A y versión
        f.read(3)
        
        gdb_blocks = []
        block_num = 0
        
        while True:
            pos = f.tell()
            id_byte = f.read(1)
            if not id_byte:
                break
            
            block_id = id_byte[0]
            block_num += 1
            
            if block_id == 0x19:  # GDB block
                try:
                    block_info = analyze_gdb_block(f, block_num)
                    gdb_blocks.append(block_info)
                    
                    print(f"\nBloque #{block_num} (GDB) @ offset 0x{block_info['offset']:04X}")
                    print(f"  Tamaño: {block_info['size']} bytes")
                    print(f"  PILOT: TOTP={block_info['TOTP']}, NPP={block_info['NPP']}, ASP={block_info['ASP']}")
                    print(f"  DATA:  TOTD={block_info['TOTD']}, NPD={block_info['NPD']}, ASD={block_info['ASD']}")
                    print(f"  Pausa: {block_info['pause']}ms")
                    
                    # Mostrar símbolos pilot
                    print(f"  Símbolos PILOT/SYNC:")
                    for i, sym in enumerate(block_info['pilot_symbols']):
                        polarity = ['toggle', 'keep', 'low', 'high'][sym['flag'] & 0x03]
                        pulses_str = ','.join([str(p) for p in sym['pulses']])
                        print(f"    Sym[{i}]: flag=0x{sym['flag']:02X} ({polarity}), pulses=[{pulses_str}]")
                    
                    # Mostrar símbolos data
                    print(f"  Símbolos DATA:")
                    for i, sym in enumerate(block_info['data_symbols']):
                        polarity = ['toggle', 'keep', 'low', 'high'][sym['flag'] & 0x03]
                        pulses_str = ','.join([str(p) for p in sym['pulses']])
                        print(f"    Sym[{i}]: flag=0x{sym['flag']:02X} ({polarity}), pulses=[{pulses_str}]")
                    
                except Exception as e:
                    print(f"ERROR analizando bloque GDB #{block_num}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # Saltar otros bloques
                if block_id == 0x10:  # Standard speed
                    length = read_word(f)
                    f.read(length + 3)
                elif block_id == 0x11:  # Turbo speed
                    length = read_3bytes(f)
                    f.read(length + 15)
                elif block_id == 0x12:  # Pure tone
                    f.read(4)
                elif block_id == 0x13:  # Pulse sequence
                    n = read_byte(f)
                    f.read(n * 2)
                elif block_id == 0x14:  # Pure data
                    length = read_3bytes(f)
                    f.read(length + 7)
                elif block_id == 0x15:  # Direct recording
                    length = read_3bytes(f)
                    f.read(length + 5)
                elif block_id == 0x18:  # CSW recording
                    length = read_dword(f)
                    f.read(length)
                elif block_id == 0x20:  # Pause
                    f.read(2)
                elif block_id == 0x21:  # Group start
                    length = read_byte(f)
                    f.read(length)
                elif block_id == 0x22:  # Group end
                    pass
                elif block_id == 0x24:  # Loop start
                    f.read(2)
                elif block_id == 0x25:  # Loop end
                    pass
                elif block_id == 0x30:  # Text description
                    length = read_byte(f)
                    f.read(length)
                elif block_id == 0x31:  # Message block
                    time = read_byte(f)
                    length = read_byte(f)
                    f.read(length)
                elif block_id == 0x32:  # Archive info
                    length = read_word(f)
                    f.read(length)
                elif block_id == 0x33:  # Hardware type
                    n = read_byte(f)
                    f.read(n * 3)
                elif block_id == 0x35:  # Custom info
                    f.read(16)
                    length = read_dword(f)
                    f.read(length)
                elif block_id == 0x5A:  # Glue block
                    f.read(9)
                else:
                    print(f"Bloque #{block_num}: ID 0x{block_id:02X} (no GDB, saltado)")
        
        return gdb_blocks

if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)
    gdb_dir = os.path.join(script_dir, 'pzxsamples', 'gdb')
    
    # Archivos a analizar
    files = [
        "BC's Quest for Tires.tzx",
        "Basil the Great Mouse Detective.tzx",
        "Book Of The Dead - Part 1 (CRL).tzx",
        "Dan Dare 2 - Mekon's Revenge.tzx"
    ]
    
    all_results = {}
    
    for filename in files:
        filepath = os.path.join(gdb_dir, filename)
        if os.path.exists(filepath):
            gdb_blocks = analyze_tzx_file(filepath)
            all_results[filename] = gdb_blocks
        else:
            print(f"\nArchivo no encontrado: {filename}")
    
    # Resumen comparativo
    print(f"\n\n{'='*80}")
    print("RESUMEN COMPARATIVO")
    print(f"{'='*80}")
    
    for filename, blocks in all_results.items():
        status = "✓ FUNCIONA" if "Book Of The Dead" in filename or "Dan Dare" in filename else "✗ FALLA"
        print(f"\n{filename} - {status}")
        print(f"  Total bloques GDB: {len(blocks)}")
        if blocks:
            for block in blocks:
                print(f"    Bloque #{block['block_num']}: ASP={block['ASP']}, ASD={block['ASD']}, pause={block['pause']}ms")
