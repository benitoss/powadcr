"""
Script para crear un archivo TZX de prueba con un GDB simplificado
que tiene el mismo formato que BC's Quest pero con datos más simples.
"""
import struct

def create_test_gdb_tzx(filename):
    """Crea un archivo TZX con un bloque GDB de prueba"""
    
    # TZX Header
    header = b'ZXTape!' + bytes([0x1A, 1, 20])  # Signature + EOF marker + version 1.20
    
    # Creamos un pequeño bloque de datos GDB
    # Similar a BC's Quest pero con solo 1024 símbolos (128 bytes)
    
    pause = 1000  # 1 segundo de pausa
    TOTP = 3      # 3 entradas en pilot/sync PRLE
    NPP = 2       # Max 2 pulsos por símbolo pilot/sync
    ASP = 3       # 3 símbolos en alfabeto pilot/sync
    TOTD = 1024   # 1024 símbolos de datos (128 bytes)
    NPD = 2       # Max 2 pulsos por símbolo de datos
    ASD = 2       # 2 símbolos en alfabeto de datos
    
    # Crear SYMDEF para pilot/sync (igual que BC's Quest)
    pilot_symdef = bytes([
        0x00, 0x78, 0x08, 0x00, 0x00,  # Symbol 0: Flag=0, [2168, 0]
        0x00, 0x9B, 0x02, 0xDF, 0x02,  # Symbol 1: Flag=0, [667, 735]
        0x00, 0x0C, 0x03, 0x92, 0x04   # Symbol 2: Flag=0, [780, 1170]
    ])
    
    # Crear PRLE para pilot/sync
    pilot_prle = bytes([
        0x00,  # Symbol 0
    ]) + struct.pack('<H', 100) + bytes([  # Repeat 100 veces (pilot corto para prueba)
        0x01,  # Symbol 1
    ]) + struct.pack('<H', 1) + bytes([    # Repeat 1 vez
        0x02,  # Symbol 2
    ]) + struct.pack('<H', 4)              # Repeat 4 veces
    
    # Crear SYMDEF para datos (igual que BC's Quest - asimétrico)
    data_symdef = bytes([
        0x00, 0x0C, 0x03, 0x0C, 0x03,  # Symbol 0: Flag=0, [780, 780]
        0x00, 0x0C, 0x03, 0x18, 0x06   # Symbol 1: Flag=0, [780, 1560]
    ])
    
    # Crear datastream - patrón alternante para verificar que ambos símbolos funcionan
    # 0xAA = 10101010 en binario, alternarán 0s y 1s
    datastream = bytes([0xAA] * (TOTD // 8))
    
    # Calcular longitud del bloque
    block_content = struct.pack('<H', pause)
    block_content += struct.pack('<I', TOTP)
    block_content += bytes([NPP, ASP])
    block_content += struct.pack('<I', TOTD)
    block_content += bytes([NPD, ASD])
    block_content += pilot_symdef
    block_content += pilot_prle
    block_content += data_symdef
    block_content += datastream
    
    block_len = len(block_content)
    
    # Bloque GDB completo
    gdb_block = bytes([0x19]) + struct.pack('<I', block_len) + block_content
    
    # Escribir archivo
    with open(filename, 'wb') as f:
        f.write(header)
        f.write(gdb_block)
    
    print(f'Archivo TZX de prueba creado: {filename}')
    print(f'  Pilot: {100} pulsos')
    print(f'  Datos: {TOTD} símbolos ({TOTD//8} bytes)')
    print(f'  Patrón: 0xAA (alternante)')
    print(f'  Símbolos: [780,780] para 0, [780,1560] para 1')

def create_symmetric_test_gdb_tzx(filename):
    """Crea un archivo TZX con GDB usando símbolos simétricos (como Dan Dare 2)"""
    
    header = b'ZXTape!' + bytes([0x1A, 1, 20])
    
    pause = 1000
    TOTP = 3
    NPP = 2
    ASP = 3
    TOTD = 1024
    NPD = 2
    ASD = 2
    
    # SYMDEF pilot/sync
    pilot_symdef = bytes([
        0x00, 0x78, 0x08, 0x00, 0x00,  # Symbol 0: Flag=0, [2168, 0]
        0x00, 0x9B, 0x02, 0xDF, 0x02,  # Symbol 1: Flag=0, [667, 735]
        0x00, 0x0C, 0x03, 0x92, 0x04   # Symbol 2: Flag=0, [780, 1170]
    ])
    
    # PRLE pilot/sync
    pilot_prle = bytes([
        0x00,
    ]) + struct.pack('<H', 100) + bytes([
        0x01,
    ]) + struct.pack('<H', 1) + bytes([
        0x02,
    ]) + struct.pack('<H', 4)
    
    # SYMDEF datos SIMÉTRICOS (como Dan Dare 2)
    data_symdef = bytes([
        0x00, 0x2B, 0x02, 0x2B, 0x02,  # Symbol 0: Flag=0, [555, 555]
        0x00, 0x56, 0x04, 0x56, 0x04   # Symbol 1: Flag=0, [1110, 1110]
    ])
    
    datastream = bytes([0xAA] * (TOTD // 8))
    
    block_content = struct.pack('<H', pause)
    block_content += struct.pack('<I', TOTP)
    block_content += bytes([NPP, ASP])
    block_content += struct.pack('<I', TOTD)
    block_content += bytes([NPD, ASD])
    block_content += pilot_symdef
    block_content += pilot_prle
    block_content += data_symdef
    block_content += datastream
    
    block_len = len(block_content)
    gdb_block = bytes([0x19]) + struct.pack('<I', block_len) + block_content
    
    with open(filename, 'wb') as f:
        f.write(header)
        f.write(gdb_block)
    
    print(f'Archivo TZX de prueba (simétrico) creado: {filename}')
    print(f'  Símbolos: [555,555] para 0, [1110,1110] para 1')

if __name__ == '__main__':
    create_test_gdb_tzx('test_gdb_asymmetric.tzx')
    print()
    create_symmetric_test_gdb_tzx('test_gdb_symmetric.tzx')
