#!/usr/bin/env python3
"""
Lista TODOS los bloques del TZX de BC's Quest para ver qué viene después del GDB
"""

import struct

def read_byte(f):
    return struct.unpack('<B', f.read(1))[0]

def read_word(f):
    return struct.unpack('<H', f.read(2))[0]

def read_dword(f):
    return struct.unpack('<I', f.read(4))[0]

def list_all_blocks():
    filename = r"c:\Users\atama\Documents\200.SPECTRUM\500. Proyectos\PowaDCR - General\powadcr_recorder\pzx\BC's Quest for Tires.tzx"
    
    print(f"Listado completo de bloques TZX: {filename}")
    print("=" * 80)
    
    with open(filename, 'rb') as f:
        # Verificar header TZX
        header = f.read(8)
        if header[:7] != b'ZXTape!':
            print("ERROR: No es un archivo TZX válido")
            return
        
        major = header[7]
        minor = read_byte(f)
        print(f"TZX Version: {major}.{minor}\n")
        
        block_num = 0
        
        while True:
            # Leer ID del bloque
            pos = f.tell()
            id_byte = f.read(1)
            if not id_byte:
                print("\n--- Fin del archivo ---")
                break
            
            block_id = struct.unpack('<B', id_byte)[0]
            block_num += 1
            
            print(f"#{block_num:02d} @ 0x{pos:05X}: ID=0x{block_id:02X} ", end='')
            
            try:
                if block_id == 0x10:  # Standard Speed Data
                    pause = read_word(f)
                    length = read_word(f)
                    print(f"Standard Speed Data - pause={pause}ms, len={length}bytes")
                    f.seek(length, 1)
                    
                elif block_id == 0x11:  # Turbo Speed Data
                    pilot_len = read_word(f)
                    sync1 = read_word(f)
                    sync2 = read_word(f)
                    bit0 = read_word(f)
                    bit1 = read_word(f)
                    pilot_pulses = read_word(f)
                    bitcfg = read_byte(f)
                    pause = read_word(f)
                    length = read_word(f) | (read_byte(f) << 16)
                    print(f"Turbo Speed Data - pause={pause}ms, len={length}bytes")
                    f.seek(length, 1)
                    
                elif block_id == 0x14:  # Pure Data Block
                    bit0 = read_word(f)
                    bit1 = read_word(f)
                    bitcfg = read_byte(f)
                    pause = read_word(f)
                    length = read_word(f) | (read_byte(f) << 16)
                    print(f"Pure Data Block - pause={pause}ms, len={length}bytes")
                    f.seek(length, 1)
                    
                elif block_id == 0x19:  # Generalized Data Block (GDB)
                    block_size = read_dword(f)
                    pause = read_word(f)
                    print(f"Generalized Data Block - pause={pause}ms, size={block_size}bytes")
                    # Saltar el resto del bloque
                    f.seek(block_size - 2, 1)  # -2 porque ya leímos pause
                    
                elif block_id == 0x20:  # Pause
                    pause = read_word(f)
                    print(f"Pause/Stop - {pause}ms")
                    
                elif block_id == 0x21:  # Group start
                    length = read_byte(f)
                    name = f.read(length).decode('latin1', errors='replace')
                    print(f"Group Start - '{name}'")
                    
                elif block_id == 0x22:  # Group end
                    print("Group End")
                    
                elif block_id == 0x30:  # Text description
                    length = read_byte(f)
                    text = f.read(length).decode('latin1', errors='replace')
                    print(f"Text Description - '{text[:50]}'")
                    
                elif block_id == 0x32:  # Archive info
                    length = read_word(f)
                    print(f"Archive Info - {length}bytes")
                    f.seek(length, 1)
                    
                elif block_id == 0x33:  # Hardware type
                    num = read_byte(f)
                    print(f"Hardware Type - {num} entries")
                    f.seek(num * 3, 1)
                    
                elif block_id == 0x35:  # Custom info
                    info_id = f.read(16).hex()
                    length = read_dword(f)
                    print(f"Custom Info - ID={info_id[:16]}..., {length}bytes")
                    f.seek(length, 1)
                    
                else:
                    print(f"Unknown/Not implemented - STOPPING")
                    break
                    
            except Exception as e:
                print(f"ERROR: {e}")
                break

if __name__ == "__main__":
    list_all_blocks()
