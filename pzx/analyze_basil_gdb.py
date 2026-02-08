import struct
import os
import math

filepath = 'pzxsamples/gdb/Basil the Great Mouse Detective.tzx'
print(f'Analizando: {filepath}')
print(f'Tamaño: {os.path.getsize(filepath)} bytes')
print()

with open(filepath, 'rb') as f:
    # Header TZX
    header = f.read(10)
    print(f'Header: {header[:7]}')
    print(f'Version: {header[8]}.{header[9]}')
    print()
    
    block_num = 0
    while True:
        pos = f.tell()
        block_id_byte = f.read(1)
        if not block_id_byte:
            break
        
        block_id = block_id_byte[0]
        
        if block_id == 0x19:  # GDB
            block_len = struct.unpack('<I', f.read(4))[0]
            pause = struct.unpack('<H', f.read(2))[0]
            totp = struct.unpack('<I', f.read(4))[0]
            npp = f.read(1)[0]
            asp = f.read(1)[0]
            totd = struct.unpack('<I', f.read(4))[0]
            npd = f.read(1)[0]
            asd = f.read(1)[0]
            
            print(f'=== BLOQUE {block_num} - ID 0x19 (GDB) @ offset {pos} ===')
            print(f'  Block length: {block_len}')
            print(f'  Pause after: {pause} ms')
            print(f'  TOTP (pilot/sync symbols): {totp}')
            print(f'  NPP (max pulses per pilot symbol): {npp}')
            print(f'  ASP (pilot alphabet size): {asp}')
            print(f'  TOTD (data symbols): {totd}')
            print(f'  NPD (max pulses per data symbol): {npd}')
            print(f'  ASD (data alphabet size): {asd}')
            
            # Calcular NB (bits por símbolo de datos)
            NB = 0
            tmpASD = asd - 1
            while tmpASD > 0:
                NB += 1
                tmpASD >>= 1
            print(f'  NB (bits per data symbol): {NB}')
            
            # IMPORTANTE: Si ASD es 0 o 1, NB será 0
            if asd <= 1:
                print(f'  *** ATENCIÓN: ASD={asd}, lo que significa NB={NB} (0 bits por símbolo)')
                print(f'  *** Esto implica que solo hay UN símbolo de datos (símbolo 0)')
            
            # Leer definiciones de símbolos pilot
            print(f'  --- Pilot Symbol Definitions (ASP={asp}) ---')
            for s in range(asp):
                flag = f.read(1)[0]
                pulses = []
                for p in range(npp):
                    pulse = struct.unpack('<H', f.read(2))[0]
                    pulses.append(pulse)
                print(f'    Symbol {s}: flag={flag}, pulses={pulses}')
            
            # Leer pilot stream (PRLE)
            print(f'  --- Pilot Stream (TOTP={totp}) ---')
            for t in range(totp):
                sym = f.read(1)[0]
                rep = struct.unpack('<H', f.read(2))[0]
                print(f'    Entry {t}: symbol={sym}, repeat={rep}')
            
            # Leer definiciones de símbolos data
            print(f'  --- Data Symbol Definitions (ASD={asd}) ---')
            for s in range(asd):
                flag = f.read(1)[0]
                pulses = []
                for p in range(npd):
                    pulse = struct.unpack('<H', f.read(2))[0]
                    pulses.append(pulse)
                print(f'    Symbol {s}: flag={flag}, pulses={pulses}')
            
            # Data stream size
            if NB == 0:
                DS = 0
                print(f'  --- Data Stream: NB=0, no hay datastream en bytes ---')
                print(f'  *** El datastream tiene 0 bytes porque cada símbolo usa 0 bits')
                print(f'  *** Se deben reproducir {totd} símbolos, todos son símbolo 0')
            else:
                DS = math.ceil((NB * totd) / 8.0)
                print(f'  --- Data Stream (DS={DS} bytes) ---')
                
                # Leer primeros bytes del datastream
                data_bytes = f.read(min(20, DS))
                print(f'    First bytes: {[hex(b) for b in data_bytes]}')
            
            # Saltar al siguiente bloque
            end_of_block = pos + 5 + block_len
            f.seek(end_of_block)
            print()
            
        elif block_id == 0x10:  # Standard
            pause = struct.unpack('<H', f.read(2))[0]
            length = struct.unpack('<H', f.read(2))[0]
            f.seek(length, 1)
            print(f'Bloque {block_num} - ID 0x10 (Standard) @ {pos}: {length} bytes, pause={pause}ms')
            
        elif block_id == 0x11:  # Turbo
            f.seek(15, 1)
            length = struct.unpack('<I', f.read(3) + b'\x00')[0]
            f.seek(length, 1)
            print(f'Bloque {block_num} - ID 0x11 (Turbo) @ {pos}: {length} bytes')
            
        elif block_id == 0x12:  # Pure Tone
            pulse_len = struct.unpack('<H', f.read(2))[0]
            num_pulses = struct.unpack('<H', f.read(2))[0]
            print(f'Bloque {block_num} - ID 0x12 (Pure Tone) @ {pos}: {num_pulses} pulses of {pulse_len}T')
            
        elif block_id == 0x13:  # Pulse Sequence
            num = f.read(1)[0]
            f.seek(num * 2, 1)
            print(f'Bloque {block_num} - ID 0x13 (Pulse Seq) @ {pos}: {num} pulses')
            
        elif block_id == 0x14:  # Pure Data
            f.seek(7, 1)
            length = struct.unpack('<I', f.read(3) + b'\x00')[0]
            f.seek(length, 1)
            print(f'Bloque {block_num} - ID 0x14 (Pure Data) @ {pos}: {length} bytes')
            
        elif block_id == 0x20:  # Pause
            pause = struct.unpack('<H', f.read(2))[0]
            print(f'Bloque {block_num} - ID 0x20 (Pause) @ {pos}: {pause}ms')
            
        elif block_id == 0x21:  # Group Start
            length = f.read(1)[0]
            name = f.read(length).decode('ascii', errors='replace')
            print(f'Bloque {block_num} - ID 0x21 (Group Start) @ {pos}: "{name}"')
            
        elif block_id == 0x22:  # Group End
            print(f'Bloque {block_num} - ID 0x22 (Group End) @ {pos}')
            
        elif block_id == 0x30:  # Text
            length = f.read(1)[0]
            f.seek(length, 1)
            print(f'Bloque {block_num} - ID 0x30 (Text) @ {pos}')
            
        elif block_id == 0x32:  # Archive Info
            length = struct.unpack('<H', f.read(2))[0]
            f.seek(length, 1)
            print(f'Bloque {block_num} - ID 0x32 (Archive Info) @ {pos}')
            
        elif block_id == 0x33:  # Hardware Type
            num = f.read(1)[0]
            f.seek(num * 3, 1)
            print(f'Bloque {block_num} - ID 0x33 (Hardware) @ {pos}')
            
        elif block_id == 0x35:  # Custom Info
            f.seek(16, 1)
            length = struct.unpack('<I', f.read(4))[0]
            f.seek(length, 1)
            print(f'Bloque {block_num} - ID 0x35 (Custom Info) @ {pos}')
            
        else:
            print(f'Bloque {block_num} - ID 0x{block_id:02X} (Unknown) @ {pos}')
            break
            
        block_num += 1
