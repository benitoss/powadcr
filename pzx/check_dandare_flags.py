#!/usr/bin/env python3
"""Ver todos los flags de Dan Dare 2"""
import os

def read_word(data, offset):
    return data[offset] | (data[offset+1] << 8)

def read_dword(data, offset):
    return data[offset] | (data[offset+1] << 8) | (data[offset+2] << 16) | (data[offset+3] << 24)

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")
with open(tzx_file, 'rb') as f:
    data = f.read()

pos = 10
block_num = 0

print("="*80)
print("DAN DARE 2 - TODOS LOS FLAGS DE SÍMBOLOS GDB")
print("="*80)

while pos < len(data):
    block_id = data[pos]
    block_num += 1
    
    if block_id == 0x19:  # GDB
        print(f"\n>>> Bloque {block_num}: GDB en offset {pos}")
        
        pos += 1
        block_len = read_dword(data, pos)
        pos += 4
        pause = read_word(data, pos)
        pos += 2
        totp = read_dword(data, pos)
        pos += 4
        npp = data[pos]
        pos += 1
        asp = data[pos]
        pos += 1
        totd = read_dword(data, pos)
        pos += 4
        npd = data[pos]
        pos += 1
        asd = data[pos]
        pos += 1
        
        print(f"  TOTD={totd}, NPD={npd}, ASD={asd}")
        
        # Saltar pilot symbols
        for i in range(asp):
            pos += 1  # flags
            pos += npp * 2  # pulses
        
        # Saltar pilot stream
        import math
        bits_per_symbol = max(1, math.ceil(math.log2(asp))) if asp > 1 else 1
        pilot_stream_bytes = (totp * bits_per_symbol + 7) // 8
        pos += pilot_stream_bytes
        
        # Leer DATA symbols
        print(f"  Símbolos de datos:")
        for i in range(asd):
            flags = data[pos]
            print(f"    Symbol {i}: flags=0x{flags:02X} (binario={flags:08b})", end="")
            
            # Analizar bits
            bit0 = flags & 0x01
            bit1 = (flags >> 1) & 0x01
            polarity = flags & 0x03
            upper_bits = flags >> 2
            
            print(f" -> polarity={polarity}, upper_bits=0x{upper_bits:02X}")
            
            if flags & 0x03 != flags:
                print(f"      ⚠️  TIENE BITS SUPERIORES ACTIVOS")
            
            pos += 1
            # Leer pulses
            for p in range(npd):
                pulse = read_word(data, pos)
                pos += 2
        
        # Saltar data stream
        import math
        bits_per_data = max(1, math.ceil(math.log2(asd))) if asd > 1 else 1
        data_stream_bytes = (totd * bits_per_data + 7) // 8
        pos += data_stream_bytes
    else:
        # Saltar otros bloques
        if block_id == 0x10:
            length = read_word(data, pos + 3)
            pos += 5 + length
        elif block_id == 0x20:
            pos += 3
        elif block_id == 0x30:
            length = data[pos + 1]
            pos += 2 + length
        else:
            break

print("\n" + "="*80)
