#!/usr/bin/env python3
"""
Verifica si BC's Quest tiene bloque ID 0x2B (Set Signal Level)
"""

import struct

def check_signal_level():
    filename = r"c:\Users\atama\Documents\200.SPECTRUM\500. Proyectos\PowaDCR - General\powadcr_recorder\pzx\BC's Quest for Tires.tzx"
    
    with open(filename, 'rb') as f:
        # Skip header
        f.seek(10)
        
        block_num = 0
        found_2b = False
        
        while True:
            pos = f.tell()
            id_byte = f.read(1)
            if not id_byte:
                break
            
            block_id = struct.unpack('<B', id_byte)[0]
            block_num += 1
            
            if block_id == 0x2B:  # Set Signal Level
                print(f"✓ ENCONTRADO: Bloque #{block_num} @ 0x{pos:X} - ID 0x2B (Set Signal Level)")
                # Leer los 4 bytes siguientes y el signal level
                data = f.read(5)
                if len(data) == 5:
                    signal_level = data[4]
                    print(f"  Signal Level: {signal_level} ({'HIGH' if signal_level == 1 else 'LOW'})")
                    found_2b = True
                break
            
            # Skip block based on ID
            try:
                if block_id == 0x10:
                    f.seek(2, 1)
                    length = struct.unpack('<H', f.read(2))[0]
                    f.seek(length, 1)
                elif block_id == 0x19:  # GDB
                    block_size = struct.unpack('<I', f.read(4))[0]
                    f.seek(block_size, 1)
                elif block_id == 0x20:
                    f.seek(2, 1)
                elif block_id == 0x21:
                    length = f.read(1)[0]
                    f.seek(length, 1)
                elif block_id == 0x30:
                    length = f.read(1)[0]
                    f.seek(length, 1)
                elif block_id == 0x32:
                    length = struct.unpack('<H', f.read(2))[0]
                    f.seek(length, 1)
                else:
                    print(f"Block #{block_num}: ID 0x{block_id:02X} - stopping")
                    break
            except:
                break
        
        if not found_2b:
            print("\n✗ NO SE ENCONTRÓ bloque ID 0x2B (Set Signal Level)")
            print("\nCONCLUSIÓN:")
            print("  BC's Quest NO especifica polaridad en el TZX")
            print("  → Usa la polaridad por DEFECTO del reproductor")
            print("  → Si TAPIR usa polaridad INVERSA (HIGH inicial),")
            print("    powaDCR debe hacer lo mismo para compatibilidad")

if __name__ == "__main__":
    check_signal_level()
