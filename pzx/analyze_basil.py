#!/usr/bin/env python3
"""
Analiza todos los bloques TZX de Basil para encontrar diferencias
entre bloques que funcionan (1-5) y que no funcionan (6+)
"""

import struct
import math
import os

def read_word(data, pos):
    return struct.unpack('<H', data[pos:pos+2])[0]

def read_dword(data, pos):
    return struct.unpack('<I', data[pos:pos+4])[0]

def analyze_standard_block(data, offset):
    """Analiza bloque ID 0x10"""
    pause = read_word(data, offset+1)
    length = read_word(data, offset+3)
    return {
        'type': 'Standard (0x10)',
        'pause': pause,
        'length': length,
        'size': length + 5
    }

def analyze_turbo_block(data, offset):
    """Analiza bloque ID 0x11"""
    pilot_len = read_word(data, offset+1)
    sync1 = read_word(data, offset+3)
    sync2 = read_word(data, offset+5)
    zero_len = read_word(data, offset+7)
    one_len = read_word(data, offset+9)
    pilot_pulses = read_word(data, offset+11)
    last_byte_bits = data[offset+13]
    pause = read_word(data, offset+14)
    length = (data[offset+16]) | (data[offset+17] << 8) | (data[offset+18] << 16)
    
    return {
        'type': 'Turbo (0x11)',
        'pilot_len': pilot_len,
        'sync1': sync1,
        'sync2': sync2,
        'zero_len': zero_len,
        'one_len': one_len,
        'pilot_pulses': pilot_pulses,
        'pause': pause,
        'length': length,
        'size': length + 19
    }

def analyze_gdb_block(data, offset):
    """Analiza bloque ID 0x19 (GDB)"""
    block_size = read_dword(data, offset+1)
    pause = read_word(data, offset+5)
    TOTP = read_dword(data, offset+7)
    NPP = data[offset+11]
    ASP = data[offset+12]
    TOTD = read_dword(data, offset+13)
    NPD = data[offset+17]
    ASD = data[offset+18]
    
    # Calcular posición de símbolos
    pos = offset + 19
    
    # Símbolos pilot/sync
    pilot_symbols = []
    for s in range(ASP):
        flag = data[pos]
        pos += 1
        pulses = []
        for p in range(NPP):
            pulse = read_word(data, pos)
            pulses.append(pulse)
            pos += 2
        pilot_symbols.append({'flag': flag, 'pulses': pulses})
    
    # Símbolos data
    data_symbols = []
    for s in range(ASD):
        flag = data[pos]
        pos += 1
        pulses = []
        for p in range(NPD):
            pulse = read_word(data, pos)
            pulses.append(pulse)
            pos += 2
        data_symbols.append({'flag': flag, 'pulses': pulses})
    
    return {
        'type': 'GDB (0x19)',
        'block_size': block_size,
        'pause': pause,
        'TOTP': TOTP,
        'NPP': NPP,
        'ASP': ASP,
        'TOTD': TOTD,
        'NPD': NPD,
        'ASD': ASD,
        'pilot_symbols': pilot_symbols,
        'data_symbols': data_symbols,
        'size': block_size + 5
    }

def analyze_tzx(filepath):
    """Analiza todos los bloques de un TZX"""
    print(f"\n{'='*80}")
    print(f"Analizando: {os.path.basename(filepath)}")
    print(f"{'='*80}\n")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Verificar header
    if data[0:7] != b'ZXTape!':
        print("ERROR: No es un archivo TZX válido")
        return
    
    offset = 10  # Después del header
    block_num = 0
    
    while offset < len(data):
        block_id = data[offset]
        block_num += 1
        
        try:
            if block_id == 0x10:  # Standard block
                info = analyze_standard_block(data, offset)
                print(f"Bloque #{block_num:3d} @ 0x{offset:06X} - {info['type']}")
                print(f"              Pausa={info['pause']}ms, Length={info['length']} bytes")
                offset += info['size']
                
            elif block_id == 0x11:  # Turbo block
                info = analyze_turbo_block(data, offset)
                print(f"Bloque #{block_num:3d} @ 0x{offset:06X} - {info['type']}")
                print(f"              Pilot={info['pilot_len']}T x{info['pilot_pulses']}, " +
                      f"Sync={info['sync1']}/{info['sync2']}T, " +
                      f"0={info['zero_len']}T, 1={info['one_len']}T")
                print(f"              Pausa={info['pause']}ms, Length={info['length']} bytes")
                offset += info['size']
                
            elif block_id == 0x19:  # GDB block
                info = analyze_gdb_block(data, offset)
                print(f"\nBloque #{block_num:3d} @ 0x{offset:06X} - {info['type']} *** GDB ***")
                print(f"              PILOT: TOTP={info['TOTP']}, NPP={info['NPP']}, ASP={info['ASP']}")
                print(f"              DATA:  TOTD={info['TOTD']}, NPD={info['NPD']}, ASD={info['ASD']}")
                print(f"              Pausa={info['pause']}ms")
                print(f"              Pilot symbols:")
                for i, sym in enumerate(info['pilot_symbols']):
                    polarity = ['toggle', 'keep', 'low', 'high'][sym['flag'] & 0x03]
                    print(f"                Sym[{i}]: flag=0x{sym['flag']:02X} ({polarity}), pulses={sym['pulses']}")
                print(f"              Data symbols:")
                for i, sym in enumerate(info['data_symbols']):
                    polarity = ['toggle', 'keep', 'low', 'high'][sym['flag'] & 0x03]
                    print(f"                Sym[{i}]: flag=0x{sym['flag']:02X} ({polarity}), pulses={sym['pulses']}")
                offset += info['size']
                
            elif block_id == 0x20:  # Pause
                pause = read_word(data, offset+1)
                print(f"Bloque #{block_num:3d} @ 0x{offset:06X} - Pause (0x20): {pause}ms")
                offset += 3
                
            elif block_id == 0x21:  # Group start
                length = data[offset+1]
                name = data[offset+2:offset+2+length].decode('ascii', errors='ignore')
                print(f"Bloque #{block_num:3d} @ 0x{offset:06X} - Group Start (0x21): '{name}'")
                offset += 2 + length
                
            elif block_id == 0x22:  # Group end
                print(f"Bloque #{block_num:3d} @ 0x{offset:06X} - Group End (0x22)")
                offset += 1
                
            elif block_id == 0x30:  # Text description
                length = data[offset+1]
                print(f"Bloque #{block_num:3d} @ 0x{offset:06X} - Text (0x30)")
                offset += 2 + length
                
            elif block_id == 0x32:  # Archive info
                length = read_word(data, offset+1)
                print(f"Bloque #{block_num:3d} @ 0x{offset:06X} - Archive Info (0x32)")
                offset += 3 + length
                
            else:
                print(f"Bloque #{block_num:3d} @ 0x{offset:06X} - ID 0x{block_id:02X} (desconocido)")
                break
                
        except Exception as e:
            print(f"ERROR en bloque #{block_num}: {e}")
            import traceback
            traceback.print_exc()
            break

if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)
    basil_path = os.path.join(script_dir, 'pzxsamples', 'gdb', 'Basil the Great Mouse Detective.tzx')
    
    if os.path.exists(basil_path):
        analyze_tzx(basil_path)
    else:
        print(f"Archivo no encontrado: {basil_path}")
