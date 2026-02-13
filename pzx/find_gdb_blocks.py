#!/usr/bin/env python3
"""Encontrar todos los bloques GDB (0x19) en Dan Dare 2"""
import struct
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")

with open(tzx_file, 'rb') as f:
    data = f.read()

print(f"Tamaño del archivo: {len(data)} bytes")
print(f"Header: {data[:7]}")
print(f"Versión: {data[8]}.{data[9]}")

pos = 10  # Después del header
block_num = 0

while pos < len(data):
    block_num += 1
    block_id = data[pos]
    
    # Mostrar info básica
    print(f"\nBloque {block_num} @ offset {pos}: ID 0x{block_id:02X}", end="")
    
    if block_id == 0x10:  # Standard Speed Data
        pause = struct.unpack_from('<H', data, pos+1)[0]
        length = struct.unpack_from('<H', data, pos+3)[0]
        print(f" - Standard Data: pause={pause}ms, length={length}")
        pos += 5 + length
        
    elif block_id == 0x11:  # Turbo Speed Data
        length = struct.unpack_from('<I', data, pos+16)[0] & 0xFFFFFF  # 3 bytes
        print(f" - Turbo Data: length={length}")
        pos += 19 + length
        
    elif block_id == 0x12:  # Pure Tone
        print(" - Pure Tone")
        pos += 5
        
    elif block_id == 0x13:  # Pulse Sequence
        num_pulses = data[pos+1]
        print(f" - Pulse Sequence: {num_pulses} pulses")
        pos += 2 + num_pulses * 2
        
    elif block_id == 0x14:  # Pure Data
        length = struct.unpack_from('<I', data, pos+8)[0] & 0xFFFFFF  # 3 bytes
        print(f" - Pure Data: length={length}")
        pos += 11 + length
        
    elif block_id == 0x19:  # GDB
        block_len = struct.unpack_from('<I', data, pos+1)[0]
        pause = struct.unpack_from('<H', data, pos+5)[0]
        totp = struct.unpack_from('<I', data, pos+7)[0]
        npp = data[pos+11]
        asp = data[pos+12]
        totd = struct.unpack_from('<I', data, pos+13)[0]
        npd = data[pos+17]
        asd = data[pos+18]
        
        print(f" - GDB:")
        print(f"    block_len={block_len}, pause={pause}ms")
        print(f"    TOTP={totp}, NPP={npp}, ASP={asp}")
        print(f"    TOTD={totd}, NPD={npd}, ASD={asd}")
        
        # Verificar si los valores son razonables
        if asp > 10 or asd > 10 or npp > 50 or npd > 50:
            print(f"    *** VALORES SOSPECHOSOS ***")
        
        # Analizar tabla de símbolos pilot
        sym_pos = pos + 19
        print(f"    Pilot symbols @ {sym_pos}:")
        pilot_sym_data = []
        for s in range(min(asp, 3)):  # Solo primeros 3
            sf = data[sym_pos]
            np = struct.unpack_from('<H', data, sym_pos+1)[0]
            print(f"      Sym {s}: flags=0x{sf:02X}, pulses={np}")
            if np <= 10:
                pulses = []
                for p in range(np):
                    pulse = struct.unpack_from('<H', data, sym_pos+3+p*2)[0]
                    pulses.append(pulse)
                print(f"        Durations: {pulses}")
                pilot_sym_data.append({'pulses': np, 'durations': pulses})
            else:
                print(f"        *** Demasiados pulsos, parece corrupto ***")
                break
            sym_pos += 3 + np * 2
        
        pos += 5 + block_len  # ID(1) + blockLen(4) + blockLen bytes
        
    elif block_id == 0x20:  # Pause
        pause = struct.unpack_from('<H', data, pos+1)[0]
        print(f" - Pause: {pause}ms")
        pos += 3
        
    elif block_id == 0x21:  # Group Start
        name_len = data[pos+1]
        name = data[pos+2:pos+2+name_len].decode('ascii', errors='replace')
        print(f" - Group Start: '{name}'")
        pos += 2 + name_len
        
    elif block_id == 0x22:  # Group End
        print(" - Group End")
        pos += 1
        
    elif block_id == 0x30:  # Text Description
        text_len = data[pos+1]
        print(f" - Text: {text_len} bytes")
        pos += 2 + text_len
        
    elif block_id == 0x32:  # Archive Info
        block_len = struct.unpack_from('<H', data, pos+1)[0]
        print(f" - Archive Info: {block_len} bytes")
        pos += 3 + block_len
        
    elif block_id == 0x35:  # Custom Info
        block_len = struct.unpack_from('<I', data, pos+17)[0]
        print(f" - Custom Info: {block_len} bytes")
        pos += 21 + block_len
        
    else:
        print(f" - Unknown ID!")
        # Intentar saltar basado en patrones conocidos
        break
        
    if block_num > 20:
        print("\n... (más bloques)")
        break
