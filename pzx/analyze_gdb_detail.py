#!/usr/bin/env python3
"""
Análisis detallado de los pulsos del bloque 6 (GDB) y 7 (Standard)
para encontrar dónde se pierde el pulso
"""

import struct

def read_tzx(filename):
    """Lee el archivo TZX y extrae información de los bloques"""
    with open(filename, 'rb') as f:
        # Header
        header = f.read(10)
        if header[:7] != b'ZXTape!':
            print("Not a valid TZX file")
            return
        
        major = header[8]
        minor = header[9]
        print(f"TZX Version: {major}.{minor}")
        
        block_num = 0
        while True:
            block_id_byte = f.read(1)
            if not block_id_byte:
                break
            
            block_id = block_id_byte[0]
            block_num += 1
            
            if block_id == 0x10:  # Standard Speed Data Block
                pause, length = struct.unpack('<HH', f.read(4))
                data = f.read(length)
                flag_byte = data[0] if length > 0 else 0
                
                # Calcular número de pulsos pilot
                if flag_byte < 128:
                    pilot_pulses = 8063  # Header
                else:
                    pilot_pulses = 3223  # Data
                
                print(f"\nBlock {block_num}: ID 0x10 (Standard)")
                print(f"  Pause: {pause}ms")
                print(f"  Length: {length} bytes")
                print(f"  Flag byte: 0x{flag_byte:02X}")
                print(f"  Pilot pulses: {pilot_pulses}")
                print(f"  Total semi-pulsos: pilot({pilot_pulses}) + SYNC1(1) + SYNC2(1) + data({length*8*2}) = {pilot_pulses + 2 + length*8*2}")
                
            elif block_id == 0x19:  # Generalized Data Block
                block_len = struct.unpack('<I', f.read(4))[0]
                pause = struct.unpack('<H', f.read(2))[0]
                
                TOTP = struct.unpack('<I', f.read(4))[0]
                NPP = f.read(1)[0]
                ASP = f.read(1)[0]
                
                TOTD = struct.unpack('<I', f.read(4))[0]
                NPD = f.read(1)[0]
                ASD = f.read(1)[0]
                
                print(f"\nBlock {block_num}: ID 0x19 (GDB)")
                print(f"  Block length: {block_len}")
                print(f"  Pause: {pause}ms")
                print(f"  TOTP (pilot symbols): {TOTP}")
                print(f"  NPP (pulses per pilot symbol): {NPP}")
                print(f"  ASP (alphabet size pilot): {ASP}")
                print(f"  TOTD (data symbols): {TOTD}")
                print(f"  NPD (pulses per data symbol): {NPD}")
                print(f"  ASD (alphabet size data): {ASD}")
                
                # Leer definiciones de símbolos pilot
                print(f"\n  Pilot Symbol Definitions:")
                for i in range(ASP):
                    flags = f.read(1)[0]
                    pulses = []
                    for j in range(NPP):
                        pulse_len = struct.unpack('<H', f.read(2))[0]
                        if pulse_len > 0:
                            pulses.append(pulse_len)
                    polarity = flags & 0x03
                    pol_names = {0: "opposite", 1: "same", 2: "force LOW", 3: "force HIGH"}
                    print(f"    Symbol {i}: polarity={polarity} ({pol_names.get(polarity, '?')}), pulses={pulses}")
                
                # Leer pilot stream
                print(f"\n  Pilot Stream (TOTP={TOTP} symbols):")
                total_pilot_pulses = 0
                for i in range(TOTP):
                    symbol_id = f.read(1)[0]
                    repeat = struct.unpack('<H', f.read(2))[0]
                    total_pilot_pulses += repeat
                    if i < 5 or i >= TOTP - 5:
                        print(f"    [{i}] Symbol {symbol_id} x {repeat}")
                    elif i == 5:
                        print(f"    ... ({TOTP - 10} entries omitted) ...")
                
                print(f"  Total pilot pulses: {total_pilot_pulses}")
                
                # Leer definiciones de símbolos data
                print(f"\n  Data Symbol Definitions:")
                for i in range(ASD):
                    flags = f.read(1)[0]
                    pulses = []
                    for j in range(NPD):
                        pulse_len = struct.unpack('<H', f.read(2))[0]
                        if pulse_len > 0:
                            pulses.append(pulse_len)
                    polarity = flags & 0x03
                    pol_names = {0: "opposite", 1: "same", 2: "force LOW", 3: "force HIGH"}
                    print(f"    Symbol {i}: polarity={polarity} ({pol_names.get(polarity, '?')}), pulses={pulses}")
                
                # Calcular bytes restantes (data stream)
                header_size = 2 + 4 + 1 + 1 + 4 + 1 + 1  # pause + TOTP + NPP + ASP + TOTD + NPD + ASD
                pilot_def_size = ASP * (1 + NPP * 2)
                pilot_stream_size = TOTP * 3
                data_def_size = ASD * (1 + NPD * 2)
                data_stream_size = block_len - header_size - pilot_def_size - pilot_stream_size - data_def_size
                
                print(f"\n  Data stream size: {data_stream_size} bytes")
                print(f"  TOTD symbols: {TOTD}")
                
                # Calcular bits por símbolo (NB)
                NB = 0
                tmpASD = ASD - 1
                while tmpASD > 0:
                    NB += 1
                    tmpASD >>= 1
                print(f"  NB (bits per symbol): {NB}")
                
                # Total de semi-pulsos de datos
                # Cada símbolo tiene NPD pulsos (pero algunos pueden ser 0)
                total_data_pulses = TOTD * 2  # Asumiendo 2 pulsos por símbolo (como bit 0/1)
                print(f"  Total data semi-pulses (estimate): {total_data_pulses}")
                
                # Saltar data stream
                f.read(data_stream_size)
                
                # Total de semi-pulsos en el bloque
                print(f"\n  RESUMEN GDB:")
                print(f"    Pilot semi-pulsos: {total_pilot_pulses}")
                print(f"    Data semi-pulsos: ~{total_data_pulses}")
                print(f"    Total: ~{total_pilot_pulses + total_data_pulses}")
                print(f"    Paridad total: {'IMPAR' if (total_pilot_pulses + total_data_pulses) % 2 == 1 else 'PAR'}")
                
            elif block_id == 0x20:  # Pause
                pause = struct.unpack('<H', f.read(2))[0]
                print(f"\nBlock {block_num}: ID 0x20 (Pause)")
                print(f"  Duration: {pause}ms")
                
            elif block_id == 0x21:  # Group Start
                name_len = f.read(1)[0]
                name = f.read(name_len).decode('ascii', errors='ignore')
                print(f"\nBlock {block_num}: ID 0x21 (Group Start): {name}")
                
            elif block_id == 0x22:  # Group End
                print(f"\nBlock {block_num}: ID 0x22 (Group End)")
                
            elif block_id == 0x30:  # Text Description
                text_len = f.read(1)[0]
                text = f.read(text_len).decode('ascii', errors='ignore')
                print(f"\nBlock {block_num}: ID 0x30 (Text): {text}")
                
            elif block_id == 0x32:  # Archive Info
                length = struct.unpack('<H', f.read(2))[0]
                f.read(length)
                print(f"\nBlock {block_num}: ID 0x32 (Archive Info)")
                
            else:
                print(f"\nBlock {block_num}: ID 0x{block_id:02X} (Unknown/Not parsed)")
                # Try to skip
                # This is tricky without knowing the block structure
                break

print("="*70)
print("Análisis de pzxsamples\gdb\Book Of The Dead - Part 1 (CRL).tzx")
print("="*70)

read_tzx(r"c:\Users\atama\Documents\200.SPECTRUM\500. Proyectos\PowaDCR - General\powadcr_recorder\pzx\pzxsamples\gdb\Book Of The Dead - Part 1 (CRL).tzx")
