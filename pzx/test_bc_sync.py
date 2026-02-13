#!/usr/bin/env python3
"""
Crea un TZX de prueba que simula la estructura exacta de BC's Quest:
- Piloto con Symbol 0 [2168, 0] 
- Sync 1 con Symbol 1 [667, 735] - ASIMÉTRICO
- Sync 2 con Symbol 2 [780, 1170] x 4 - ASIMÉTRICO repetido
- Data con symbols simétricos para simplificar

Este test verifica si el problema está en los sync asimétricos.
"""
import struct

def create_bc_style_test():
    """Crea TZX con estructura de sync idéntica a BC's Quest"""
    
    # Header TZX
    tzx = bytearray(b'ZXTape!\x1a\x01\x14')
    
    # Datos: header estándar "TEST" (19 bytes)
    header_data = bytes([
        0x00,  # Flag: header
        0x03,  # Type: CODE
        ord('T'), ord('E'), ord('S'), ord('T'),  # Name
        ord(' '), ord(' '), ord(' '), ord(' '),
        ord(' '), ord(' '),
        0x00, 0x40,  # Length: 16384
        0x00, 0x40,  # Start: 16384
        0x00, 0x80,  # Unused
    ])
    # Calcular checksum
    checksum = 0
    for b in header_data:
        checksum ^= b
    header_data = header_data + bytes([checksum])
    
    # Crear GDB (ID 0x19) con estructura BC's Quest
    # TOTP=3 (pilot, sync1, sync2)
    # NPP=2 (2 pulsos por símbolo pilot)
    # ASP=3 (3 símbolos pilot)
    # TOTD = 19*8 = 152 (bits para el header)
    # NPD=2 (2 pulsos por símbolo data)
    # ASD=2 (2 símbolos data: 0 y 1)
    
    TOTP = 3
    NPP = 2
    ASP = 3
    TOTD = len(header_data) * 8  # 152 bits
    NPD = 2
    ASD = 2
    
    # Construir el bloque GDB
    gdb = bytearray()
    
    # Pause after block (2 bytes)
    gdb.extend(struct.pack('<H', 1000))  # 1000ms pause
    
    # TOTP (4 bytes)
    gdb.extend(struct.pack('<I', TOTP))
    
    # NPP (1 byte)
    gdb.append(NPP)
    
    # ASP (1 byte)
    gdb.append(ASP)
    
    # TOTD (4 bytes)
    gdb.extend(struct.pack('<I', TOTD))
    
    # NPD (1 byte)
    gdb.append(NPD)
    
    # ASD (1 byte)
    gdb.append(ASD)
    
    # PILOT SYMDEF (ASP símbolos, cada uno: 1 byte flag + NPP*2 bytes pulsos)
    # Symbol 0: [2168, 0] - pilot tone (igual que BC's Quest)
    gdb.append(0)  # flag = 0 (change edge)
    gdb.extend(struct.pack('<H', 2168))  # pulse 1
    gdb.extend(struct.pack('<H', 0))     # pulse 2 = 0 (termina símbolo)
    
    # Symbol 1: [667, 735] - sync1 ASIMÉTRICO (igual que BC's Quest)
    gdb.append(0)  # flag = 0
    gdb.extend(struct.pack('<H', 667))
    gdb.extend(struct.pack('<H', 735))
    
    # Symbol 2: [780, 1170] - sync2 ASIMÉTRICO (igual que BC's Quest)
    gdb.append(0)  # flag = 0
    gdb.extend(struct.pack('<H', 780))
    gdb.extend(struct.pack('<H', 1170))
    
    # PILOT PRLE (TOTP entradas, cada una: 1 byte symbol + 2 bytes repeat)
    # PRLE[0]: Symbol 0 x 3223 (pilot)
    gdb.append(0)
    gdb.extend(struct.pack('<H', 3223))
    
    # PRLE[1]: Symbol 1 x 1 (sync1)
    gdb.append(1)
    gdb.extend(struct.pack('<H', 1))
    
    # PRLE[2]: Symbol 2 x 4 (sync2) - BC's Quest repite 4 veces!
    gdb.append(2)
    gdb.extend(struct.pack('<H', 4))
    
    # DATA SYMDEF (ASD símbolos)
    # Symbol 0: [855, 855] - bit 0 (simétrico estándar para simplificar)
    gdb.append(0)
    gdb.extend(struct.pack('<H', 855))
    gdb.extend(struct.pack('<H', 855))
    
    # Symbol 1: [1710, 1710] - bit 1 (simétrico estándar para simplificar)
    gdb.append(0)
    gdb.extend(struct.pack('<H', 1710))
    gdb.extend(struct.pack('<H', 1710))
    
    # DATA STREAM (los bytes de datos)
    gdb.extend(header_data)
    
    # Ahora agregar el bloque al TZX
    block_length = len(gdb)
    tzx.append(0x19)  # Block ID
    tzx.extend(struct.pack('<I', block_length))
    tzx.extend(gdb)
    
    return bytes(tzx)


def create_standard_sync_test():
    """Crea TZX con sync SIMÉTRICO para comparar"""
    
    # Header TZX
    tzx = bytearray(b'ZXTape!\x1a\x01\x14')
    
    # Datos: header estándar "TEST" (19 bytes)
    header_data = bytes([
        0x00,  # Flag: header
        0x03,  # Type: CODE
        ord('T'), ord('E'), ord('S'), ord('T'),
        ord(' '), ord(' '), ord(' '), ord(' '),
        ord(' '), ord(' '),
        0x00, 0x40,
        0x00, 0x40,
        0x00, 0x80,
    ])
    checksum = 0
    for b in header_data:
        checksum ^= b
    header_data = header_data + bytes([checksum])
    
    TOTP = 2  # Solo pilot y sync (como estándar)
    NPP = 2
    ASP = 2
    TOTD = len(header_data) * 8
    NPD = 2
    ASD = 2
    
    gdb = bytearray()
    
    # Pause
    gdb.extend(struct.pack('<H', 1000))
    
    # TOTP, NPP, ASP
    gdb.extend(struct.pack('<I', TOTP))
    gdb.append(NPP)
    gdb.append(ASP)
    
    # TOTD, NPD, ASD
    gdb.extend(struct.pack('<I', TOTD))
    gdb.append(NPD)
    gdb.append(ASD)
    
    # PILOT SYMDEF
    # Symbol 0: [2168, 2168] - pilot simétrico
    gdb.append(0)
    gdb.extend(struct.pack('<H', 2168))
    gdb.extend(struct.pack('<H', 2168))
    
    # Symbol 1: [667, 735] - sync SIMÉTRICO (usando valores promedio)
    gdb.append(0)
    gdb.extend(struct.pack('<H', 667))
    gdb.extend(struct.pack('<H', 735))
    
    # PRLE
    # Pilot x 3223 (pero con 2 pulsos, así que serían menos repeticiones)
    # Para 3223 pulsos individuales con símbolo de 2 pulsos: 3223/2 = 1611 repeticiones
    gdb.append(0)
    gdb.extend(struct.pack('<H', 1611))
    
    # Sync x 1
    gdb.append(1)
    gdb.extend(struct.pack('<H', 1))
    
    # DATA SYMDEF
    gdb.append(0)
    gdb.extend(struct.pack('<H', 855))
    gdb.extend(struct.pack('<H', 855))
    
    gdb.append(0)
    gdb.extend(struct.pack('<H', 1710))
    gdb.extend(struct.pack('<H', 1710))
    
    # DATA STREAM
    gdb.extend(header_data)
    
    block_length = len(gdb)
    tzx.append(0x19)
    tzx.extend(struct.pack('<I', block_length))
    tzx.extend(gdb)
    
    return bytes(tzx)


if __name__ == '__main__':
    # Test 1: Sync asimétrico estilo BC's Quest
    bc_style = create_bc_style_test()
    with open('test_bc_sync_asym.tzx', 'wb') as f:
        f.write(bc_style)
    print(f'Created test_bc_sync_asym.tzx ({len(bc_style)} bytes)')
    print('  - Pilot: [2168, 0] x 3223')
    print('  - Sync1: [667, 735] x 1 (ASIMÉTRICO)')
    print('  - Sync2: [780, 1170] x 4 (ASIMÉTRICO)')
    print('  - Data: símbolos estándar simétricos')
    print()
    
    # Test 2: Sync con piloto simétrico
    std_sync = create_standard_sync_test()
    with open('test_bc_sync_sym.tzx', 'wb') as f:
        f.write(std_sync)
    print(f'Created test_bc_sync_sym.tzx ({len(std_sync)} bytes)')
    print('  - Pilot: [2168, 2168] x 1611')
    print('  - Sync: [667, 735] x 1')
    print('  - Data: símbolos estándar simétricos')
