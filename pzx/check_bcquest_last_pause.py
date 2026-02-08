#!/usr/bin/env python3
"""
Analiza el TZX de BC's Quest para ver el valor de pausa del último bloque GDB
"""

import struct

def read_byte(f):
    return struct.unpack('<B', f.read(1))[0]

def read_word(f):
    return struct.unpack('<H', f.read(2))[0]

def read_dword(f):
    return struct.unpack('<I', f.read(4))[0]

def analyze_bcquest_tzx():
    filename = r"c:\Users\atama\Documents\200.SPECTRUM\500. Proyectos\PowaDCR - General\powadcr_recorder\pzx\BC's Quest for Tires.tzx"
    
    print(f"Analizando: {filename}")
    print("=" * 80)
    
    with open(filename, 'rb') as f:
        # Verificar header TZX
        header = f.read(8)
        if header[:7] != b'ZXTape!':
            print("ERROR: No es un archivo TZX válido")
            return
        
        major = header[7]
        minor = read_byte(f)
        print(f"TZX Version: {major}.{minor}")
        print()
        
        block_num = 0
        last_gdb_block = None
        gdb_blocks = []
        
        while True:
            # Leer ID del bloque
            pos = f.tell()
            id_byte = f.read(1)
            if not id_byte:
                break
            
            block_id = struct.unpack('<B', id_byte)[0]
            block_num += 1
            
            print(f"Block #{block_num} @ 0x{pos:X}: ID=0x{block_id:02X}", end='')
            
            if block_id == 0x10:  # Standard Speed Data
                print(" - Standard Speed Data")
                pause = read_word(f)
                length = read_word(f)
                f.seek(length, 1)
                
            elif block_id == 0x11:  # Turbo Speed Data
                print(" - Turbo Speed Data")
                f.seek(0x0F, 1)  # Skip timings
                pause = read_word(f)
                length = read_word(f) | (read_byte(f) << 16)
                f.seek(length, 1)
                
            elif block_id == 0x19:  # Generalized Data Block (GDB)
                block_size = read_dword(f)
                pause = read_word(f)
                
                print(f" - Generalized Data Block")
                print(f"    Block size: {block_size} bytes")
                print(f"    Pause after: {pause} ms")
                
                # Leer parámetros pilot/sync
                TOTP = read_dword(f)
                NPP = read_byte(f)
                ASP = read_byte(f)
                
                # Leer parámetros data
                TOTD = read_dword(f)
                NPD = read_byte(f)
                ASD = read_byte(f)
                
                print(f"    Pilot: TOTP={TOTP}, NPP={NPP}, ASP={ASP}")
                print(f"    Data: TOTD={TOTD}, NPD={NPD}, ASD={ASD}")
                
                # Guardar info de este GDB
                gdb_info = {
                    'block_num': block_num,
                    'offset': pos,
                    'pause': pause,
                    'TOTP': TOTP,
                    'ASP': ASP,
                    'TOTD': TOTD,
                    'ASD': ASD
                }
                gdb_blocks.append(gdb_info)
                last_gdb_block = gdb_info
                
                # Saltar el resto del bloque
                remaining = block_size - 10  # Ya leímos 10 bytes (pause + params)
                f.seek(remaining, 1)
                
            elif block_id == 0x20:  # Pause
                print(" - Pause")
                pause = read_word(f)
                print(f"    Duration: {pause} ms")
                
            elif block_id == 0x21:  # Group start
                print(" - Group start")
                length = read_byte(f)
                f.seek(length, 1)
                
            elif block_id == 0x22:  # Group end
                print(" - Group end")
                
            elif block_id == 0x30:  # Text description
                print(" - Text description")
                length = read_byte(f)
                f.seek(length, 1)
                
            elif block_id == 0x32:  # Archive info
                print(" - Archive info")
                length = read_word(f)
                f.seek(length, 1)
                
            else:
                print(f" - Unknown/Not implemented")
                # Intentar saltar conservadoramente
                break
        
        print()
        print("=" * 80)
        print(f"Total bloques GDB encontrados: {len(gdb_blocks)}")
        print()
        
        if last_gdb_block:
            print("ÚLTIMO BLOQUE GDB:")
            print(f"  Bloque #{last_gdb_block['block_num']} @ 0x{last_gdb_block['offset']:X}")
            print(f"  Pause after: {last_gdb_block['pause']} ms")
            print(f"  TOTP={last_gdb_block['TOTP']}, ASP={last_gdb_block['ASP']}")
            print(f"  TOTD={last_gdb_block['TOTD']}, ASD={last_gdb_block['ASD']}")
            print()
            print(f"  ⚠️ PAUSA DEL ÚLTIMO BLOQUE: {last_gdb_block['pause']} ms")
            
            if last_gdb_block['pause'] == 0:
                print("  ⚠️ PROBLEMA DETECTADO: Pausa = 0ms")
                print("  El Spectrum necesita tiempo para procesar el último bloque!")
                print("  Recomendación: Añadir pausa mínima de 1000-3000ms")

if __name__ == "__main__":
    analyze_bcquest_tzx()
