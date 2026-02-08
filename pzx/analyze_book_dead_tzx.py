#!/usr/bin/env python3
"""Analiza bloques GDB (ID 0x19) en archivo TZX Book of the Dead"""

import struct
import os

def analyze_tzx(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Verificar cabecera TZX
    if data[:7] != b'ZXTape!':
        print("ERROR: No es un archivo TZX válido")
        return
    
    print(f"Archivo: {filepath}")
    print(f"Tamaño: {len(data)} bytes")
    print(f"Versión TZX: {data[8]}.{data[9]}")
    print("=" * 100)
    
    pos = 10  # Después de la cabecera
    block_num = 0
    
    while pos < len(data):
        block_id = data[pos]
        block_start = pos
        
        # Calcular tamaño según ID
        if block_id == 0x10:  # Standard speed data
            length = struct.unpack('<H', data[pos+3:pos+5])[0]
            block_size = 5 + length
            block_name = "Standard Speed Data"
        elif block_id == 0x11:  # Turbo speed data
            length = struct.unpack('<I', data[pos+16:pos+19] + b'\x00')[0] & 0xFFFFFF
            block_size = 19 + length
            block_name = "Turbo Speed Data"
        elif block_id == 0x12:  # Pure tone
            block_size = 5
            block_name = "Pure Tone"
        elif block_id == 0x13:  # Pulse sequence
            num_pulses = data[pos+1]
            block_size = 2 + num_pulses * 2
            block_name = "Pulse Sequence"
        elif block_id == 0x14:  # Pure data
            length = struct.unpack('<I', data[pos+8:pos+11] + b'\x00')[0] & 0xFFFFFF
            block_size = 11 + length
            block_name = "Pure Data"
        elif block_id == 0x15:  # Direct recording
            length = struct.unpack('<I', data[pos+6:pos+9] + b'\x00')[0] & 0xFFFFFF
            block_size = 9 + length
            block_name = "Direct Recording"
        elif block_id == 0x19:  # Generalized Data Block (GDB)
            length = struct.unpack('<I', data[pos+1:pos+5])[0]
            block_size = 5 + length
            block_name = "Generalized Data Block (GDB)"
            
            # ¡ANALIZAR GDB EN DETALLE!
            print(f"\n{'='*100}")
            print(f"BLOQUE #{block_num} - ID 0x19 (GDB) @ offset 0x{block_start:06X}")
            print(f"{'='*100}")
            
            gdb_offset = pos + 5  # Después de ID + length
            
            pause = struct.unpack('<H', data[gdb_offset:gdb_offset+2])[0]
            totp = struct.unpack('<I', data[gdb_offset+2:gdb_offset+6])[0]
            npp = data[gdb_offset+6]
            asp = data[gdb_offset+7]
            totd = struct.unpack('<I', data[gdb_offset+8:gdb_offset+12])[0]
            npd = data[gdb_offset+12]
            asd = data[gdb_offset+13]
            
            print(f"  Pause after block: {pause} ms")
            print(f"  TOTP (Total Pilot/Sync pulses): {totp}")
            print(f"  NPP (Max pulses per pilot symbol): {npp}")
            print(f"  ASP (Num pilot/sync symbol defs): {asp}")
            print(f"  TOTD (Total Data pulses): {totd}")
            print(f"  NPD (Max pulses per data symbol): {npd}")
            print(f"  ASD (Num data symbol defs): {asd}")
            
            # Leer definiciones de símbolos pilot/sync
            symdef_offset = gdb_offset + 14
            print(f"\n  --- PILOT/SYNC Symbol Definitions (ASP={asp}) ---")
            
            for s in range(asp):
                flags = data[symdef_offset]
                polarity = flags & 0x03
                
                polarity_str = {
                    0: "opposite to current",
                    1: "same as current", 
                    2: "force LOW",
                    3: "force HIGH"
                }.get(polarity, f"unknown ({polarity})")
                
                print(f"    Symbol {s}: flags=0x{flags:02X}, polarity={polarity} ({polarity_str})")
                
                # Leer pulsos del símbolo
                pulses = []
                for p in range(npp):
                    pulse_len = struct.unpack('<H', data[symdef_offset+1+p*2:symdef_offset+3+p*2])[0]
                    if pulse_len > 0:
                        pulses.append(pulse_len)
                print(f"           Pulses: {pulses}")
                
                symdef_offset += 1 + npp * 2
            
            # Leer definiciones de símbolos de datos
            print(f"\n  --- DATA Symbol Definitions (ASD={asd}) ---")
            
            for s in range(asd):
                flags = data[symdef_offset]
                polarity = flags & 0x03
                
                polarity_str = {
                    0: "opposite to current",
                    1: "same as current", 
                    2: "force LOW",
                    3: "force HIGH"
                }.get(polarity, f"unknown ({polarity})")
                
                print(f"    Symbol {s}: flags=0x{flags:02X}, polarity={polarity} ({polarity_str})")
                
                # Leer pulsos del símbolo
                pulses = []
                for p in range(npd):
                    pulse_len = struct.unpack('<H', data[symdef_offset+1+p*2:symdef_offset+3+p*2])[0]
                    if pulse_len > 0:
                        pulses.append(pulse_len)
                print(f"           Pulses: {pulses}")
                
                symdef_offset += 1 + npd * 2
            
            # Verificar si hay polaridad forzada
            print(f"\n  >>> RESUMEN DE POLARIDAD <<<")
            has_forced = False
            
            # Re-leer para contar
            symdef_offset = gdb_offset + 14
            for s in range(asp):
                flags = data[symdef_offset]
                pol = flags & 0x03
                if pol == 2 or pol == 3:
                    has_forced = True
                    print(f"      ⚠️  PILOT Symbol {s}: POLARIDAD FORZADA ({['','','LOW','HIGH'][pol]})")
                symdef_offset += 1 + npp * 2
                
            for s in range(asd):
                flags = data[symdef_offset]
                pol = flags & 0x03
                if pol == 2 or pol == 3:
                    has_forced = True
                    print(f"      ⚠️  DATA Symbol {s}: POLARIDAD FORZADA ({['','','LOW','HIGH'][pol]})")
                symdef_offset += 1 + npd * 2
            
            if not has_forced:
                print(f"      ✓ No hay polaridad forzada en este bloque GDB")
                
        elif block_id == 0x20:  # Pause
            block_size = 3
            block_name = "Pause"
        elif block_id == 0x21:  # Group start
            name_len = data[pos+1]
            block_size = 2 + name_len
            block_name = "Group Start"
        elif block_id == 0x22:  # Group end
            block_size = 1
            block_name = "Group End"
        elif block_id == 0x30:  # Text description
            text_len = data[pos+1]
            block_size = 2 + text_len
            block_name = "Text Description"
        elif block_id == 0x32:  # Archive info
            length = struct.unpack('<H', data[pos+1:pos+3])[0]
            block_size = 3 + length
            block_name = "Archive Info"
        elif block_id == 0x33:  # Hardware type
            num = data[pos+1]
            block_size = 2 + num * 3
            block_name = "Hardware Type"
        elif block_id == 0x35:  # Custom info
            length = struct.unpack('<I', data[pos+11:pos+15])[0]
            block_size = 15 + length
            block_name = "Custom Info"
        else:
            print(f"Bloque #{block_num}: ID 0x{block_id:02X} desconocido @ 0x{block_start:06X}")
            break
        
        # Solo mostrar bloques que no sean GDB (ya se muestran arriba)
        if block_id != 0x19:
            print(f"Bloque #{block_num}: ID 0x{block_id:02X} ({block_name}) @ 0x{block_start:06X}, size={block_size}")
        
        pos += block_size
        block_num += 1
    
    print(f"\n{'='*100}")
    print(f"Total bloques: {block_num}")

if __name__ == '__main__':
    filepath = r"pzxsamples\gdb\Book Of The Dead - Part 1 (CRL).tzx"
    if os.path.exists(filepath):
        analyze_tzx(filepath)
    else:
        print(f"No se encuentra: {filepath}")
