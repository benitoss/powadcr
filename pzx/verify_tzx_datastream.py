#!/usr/bin/env python3
"""
Verifica el contenido del data stream del bloque GDB en el archivo TZX
y lo compara con bc_data_ok.txt
"""

import struct

def read_tzx_gdb_datastream(tzx_path):
    """Lee el data stream del bloque GDB del archivo TZX"""
    with open(tzx_path, 'rb') as f:
        # Leer header TZX
        header = f.read(10)
        print(f"TZX Header: {header[:7]}")
        
        # Buscar bloque 0x19 (GDB)
        while True:
            block_id = f.read(1)
            if not block_id:
                print("No more blocks")
                break
            
            block_id = block_id[0]
            
            if block_id == 0x19:  # GDB
                print(f"\nFound GDB block at offset {f.tell() - 1}")
                
                # Leer longitud del bloque (4 bytes little-endian)
                block_len = struct.unpack('<I', f.read(4))[0]
                print(f"Block length: {block_len} bytes")
                
                # Leer parámetros del GDB
                pause = struct.unpack('<H', f.read(2))[0]
                TOTP = struct.unpack('<I', f.read(4))[0]
                NPP = f.read(1)[0]
                ASP = f.read(1)[0]
                TOTD = struct.unpack('<I', f.read(4))[0]
                NPD = f.read(1)[0]
                ASD = f.read(1)[0]
                
                print(f"Pause: {pause}")
                print(f"TOTP: {TOTP}, NPP: {NPP}, ASP: {ASP}")
                print(f"TOTD: {TOTD}, NPD: {NPD}, ASD: {ASD}")
                
                # Calcular NB y DS
                import math
                NB = max(1, math.ceil(math.log2(ASD))) if ASD > 1 else 1
                DS = math.ceil((NB * TOTD) / 8)
                print(f"Calculated NB: {NB}, DS: {DS}")
                
                # Saltar definiciones de símbolos piloto (si las hay)
                pilot_sym_size = (2 * NPP + 1) * ASP  # NPP pulsos + 1 flag por símbolo, ASP símbolos
                print(f"Pilot symbols size: {pilot_sym_size} bytes")
                f.read(pilot_sym_size)
                
                # Saltar pilot stream (PRLE)
                pilot_stream_size = 3 * TOTP  # 3 bytes por entrada PRLE (symbol + 2 bytes repetitions)
                print(f"Pilot stream size: {pilot_stream_size} bytes")
                f.read(pilot_stream_size)
                
                # Saltar definiciones de símbolos de datos
                data_sym_size = (2 * NPD + 1) * ASD
                print(f"Data symbols size: {data_sym_size} bytes")
                f.read(data_sym_size)
                
                # Ahora estamos en el data stream
                print(f"\nData stream starts at offset {f.tell()}")
                data_stream = f.read(DS)
                print(f"Read {len(data_stream)} bytes from data stream")
                
                return data_stream
            
            else:
                # Saltar bloque
                if block_id == 0x10:  # Standard speed data
                    f.read(2)  # pause
                    length = struct.unpack('<H', f.read(2))[0]
                    f.read(length)
                elif block_id == 0x11:  # Turbo speed data
                    f.read(15)  # params
                    length = struct.unpack('<I', f.read(3) + b'\x00')[0]
                    f.read(length)
                elif block_id == 0x30:  # Text description
                    length = f.read(1)[0]
                    f.read(length)
                elif block_id == 0x32:  # Archive info
                    length = struct.unpack('<H', f.read(2))[0]
                    f.read(length)
                else:
                    print(f"Unknown block 0x{block_id:02X} at offset {f.tell()-1}")
                    break
    
    return None

def parse_hex_file(file_path):
    """Parsea el archivo de bytes hex"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Buscar todos los valores 0xXX
    import re
    hex_values = re.findall(r'0x([0-9a-fA-F]{2})', content)
    return bytes(int(h, 16) for h in hex_values)

def main():
    tzx_path = r"c:\Users\atama\Documents\200.SPECTRUM\500. Proyectos\PowaDCR - General\powadcr_recorder\pzx\BC's Quest for Tires.tzx"
    ok_path = r"c:\Users\atama\Documents\200.SPECTRUM\500. Proyectos\PowaDCR - General\powadcr_recorder\pzx\bc_data_ok.txt"
    
    print("=" * 60)
    print("Reading TZX file...")
    print("=" * 60)
    tzx_data = read_tzx_gdb_datastream(tzx_path)
    
    if tzx_data is None:
        print("ERROR: Could not read data stream from TZX")
        return
    
    print("\n" + "=" * 60)
    print("Reading OK reference file...")
    print("=" * 60)
    ok_data = parse_hex_file(ok_path)
    print(f"Read {len(ok_data)} bytes from OK file")
    
    print("\n" + "=" * 60)
    print("Comparing...")
    print("=" * 60)
    
    min_len = min(len(tzx_data), len(ok_data))
    differences = 0
    first_diff = None
    
    for i in range(min_len):
        if tzx_data[i] != ok_data[i]:
            if first_diff is None:
                first_diff = i
            differences += 1
            if differences <= 10:
                print(f"Diff at byte {i}: TZX=0x{tzx_data[i]:02X}, OK=0x{ok_data[i]:02X}")
    
    if differences == 0:
        print("✓ TZX data stream matches OK file perfectly!")
    else:
        print(f"\n✗ Found {differences} differences")
        print(f"  First difference at byte {first_diff}")
        
    # Verificar longitudes
    if len(tzx_data) != len(ok_data):
        print(f"\nLength mismatch: TZX={len(tzx_data)}, OK={len(ok_data)}")
    
    # Mostrar primeros y últimos bytes para verificación
    print(f"\nFirst 10 bytes TZX: {' '.join(f'{b:02X}' for b in tzx_data[:10])}")
    print(f"First 10 bytes OK:  {' '.join(f'{b:02X}' for b in ok_data[:10])}")
    print(f"\nLast 10 bytes TZX:  {' '.join(f'{b:02X}' for b in tzx_data[-10:])}")
    print(f"Last 10 bytes OK:   {' '.join(f'{b:02X}' for b in ok_data[-10:])}")

if __name__ == "__main__":
    main()
