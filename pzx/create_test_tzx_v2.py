"""
Script para crear archivos TZX de prueba con GDB que realmente exciten
la carga del Spectrum. Usa piloto ROM estándar con suficientes pulsos.
"""
import struct

def create_working_gdb_tzx(filename, symmetric=False):
    """
    Crea un TZX con:
    1. Bloque 0x10 estándar con cabecera BASIC (para excitar LOAD)
    2. Bloque GDB para los datos (asimétrico o simétrico)
    """
    
    header = b'ZXTape!' + bytes([0x1A, 1, 20])
    
    # --- BLOQUE 0x10: Cabecera estándar ---
    # Esto excitará "Program: test" en el Spectrum
    
    # Crear cabecera de 17 bytes + flag + checksum = 19 bytes
    flag = 0x00  # Cabecera
    block_type = 0x00  # Program
    filename_bytes = b'test      '  # 10 caracteres
    data_length = 128  # Longitud del bloque BASIC
    param1 = 10  # LINE de autorun
    param2 = 128  # Longitud del programa
    
    header_data = bytes([flag, block_type]) + filename_bytes + struct.pack('<HHH', data_length, param1, param2)
    checksum = 0
    for b in header_data:
        checksum ^= b
    header_block_data = header_data + bytes([checksum])
    
    # Bloque 0x10: pause(2 bytes) + length(2 bytes) + data
    block_10 = bytes([0x10])
    block_10 += struct.pack('<H', 1000)  # Pause 1000ms
    block_10 += struct.pack('<H', len(header_block_data))
    block_10 += header_block_data
    
    # --- BLOQUE GDB: Datos con símbolos personalizados ---
    
    pause = 0  # Sin pausa al final del GDB
    
    # Piloto/sync: usaremos formato ROM estándar
    # El piloto ROM tiene pulsos de 2168 T-states (medio ciclo)
    # Necesitamos ~8063 medios pulsos para cabecera, ~3223 para datos
    
    TOTP = 2      # 2 entradas en PRLE (piloto + sync)
    NPP = 2       # Max 2 pulsos por símbolo
    ASP = 2       # 2 símbolos: piloto y sync
    
    # Datos: 128 bytes = 1024 bits
    TOTD = 1024
    NPD = 2
    ASD = 2
    
    # SYMDEF pilot/sync
    # Symbol 0: Pulso piloto (2168 T-states, repetido como medio ciclo)
    # Symbol 1: Sync (667 + 735 T-states)
    pilot_symdef = bytes([
        0x00,  # Flag
    ]) + struct.pack('<H', 2168) + struct.pack('<H', 2168) + bytes([  # [2168, 2168] - ciclo completo piloto
        0x00,  # Flag  
    ]) + struct.pack('<H', 667) + struct.pack('<H', 735)   # [667, 735] - sync
    
    # PRLE: 3223 pulsos de piloto + 1 sync
    pilot_prle = bytes([0x00]) + struct.pack('<H', 3223)  # Piloto x3223
    pilot_prle += bytes([0x01]) + struct.pack('<H', 1)    # Sync x1
    
    # SYMDEF datos
    if symmetric:
        # Simétrico como Dan Dare 2: [855,855] y [1710,1710]
        data_symdef = bytes([
            0x00,
        ]) + struct.pack('<H', 855) + struct.pack('<H', 855) + bytes([
            0x00,
        ]) + struct.pack('<H', 1710) + struct.pack('<H', 1710)
        style = "SIMÉTRICO"
    else:
        # Asimétrico como BC's Quest: [855,855] y [855,1710]
        data_symdef = bytes([
            0x00,
        ]) + struct.pack('<H', 855) + struct.pack('<H', 855) + bytes([
            0x00,
        ]) + struct.pack('<H', 855) + struct.pack('<H', 1710)
        style = "ASIMÉTRICO"
    
    # Datastream: crear un bloque de datos válido
    # Flag byte (0xFF = datos) + datos + checksum
    data_flag = 0xFF
    # Datos BASIC dummy: 10 REM seguido de espacios
    basic_data = bytes([0x00, 0x0A,  # Line 10
                        0x7D, 0x00,  # Longitud línea = 125
                        0xEA])       # REM
    basic_data += bytes([0x20] * 120)  # Espacios
    basic_data += bytes([0x0D])        # Fin de línea
    
    # Calcular checksum
    full_data = bytes([data_flag]) + basic_data
    checksum = 0
    for b in full_data:
        checksum ^= b
    full_data += bytes([checksum])
    
    # Convertir a bits MSB first
    datastream = full_data
    
    # Ajustar TOTD al número real de bits
    TOTD = len(datastream) * 8
    
    # Construir bloque GDB
    block_content = struct.pack('<H', pause)
    block_content += struct.pack('<I', TOTP)
    block_content += bytes([NPP, ASP])
    block_content += struct.pack('<I', TOTD)
    block_content += bytes([NPD, ASD])
    block_content += pilot_symdef
    block_content += pilot_prle
    block_content += data_symdef
    block_content += datastream
    
    gdb_block = bytes([0x19]) + struct.pack('<I', len(block_content)) + block_content
    
    # Escribir archivo
    with open(filename, 'wb') as f:
        f.write(header)
        f.write(block_10)   # Cabecera estándar
        f.write(gdb_block)  # Datos con GDB
    
    print(f'Archivo TZX creado: {filename}')
    print(f'  Estilo: {style}')
    print(f'  Bloque 0x10: Cabecera "test" (estándar)')
    print(f'  Bloque GDB: {TOTD} bits de datos')
    print(f'  Piloto: 3223 ciclos de [2168, 2168]')
    if symmetric:
        print(f'  Símbolos datos: [855,855] para 0, [1710,1710] para 1')
    else:
        print(f'  Símbolos datos: [855,855] para 0, [855,1710] para 1')


def create_pure_standard_test(filename):
    """
    Crea un TZX con SOLO bloques estándar 0x10 para verificar
    que el PowaDCR funciona con carga normal.
    """
    header = b'ZXTape!' + bytes([0x1A, 1, 20])
    
    # Cabecera
    flag = 0x00
    block_type = 0x00  # Program
    name = b'standard  '
    data_len = 2
    param1 = 0
    param2 = 2
    
    hdr_data = bytes([flag, block_type]) + name + struct.pack('<HHH', data_len, param1, param2)
    chk = 0
    for b in hdr_data:
        chk ^= b
    hdr_block = hdr_data + bytes([chk])
    
    block_hdr = bytes([0x10]) + struct.pack('<HH', 1000, len(hdr_block)) + hdr_block
    
    # Datos
    data_content = bytes([0xFF, 0x00, 0x00])  # Flag + 2 bytes
    chk = 0
    for b in data_content:
        chk ^= b
    data_block = data_content + bytes([chk])
    
    block_data = bytes([0x10]) + struct.pack('<HH', 1000, len(data_block)) + data_block
    
    with open(filename, 'wb') as f:
        f.write(header)
        f.write(block_hdr)
        f.write(block_data)
    
    print(f'Archivo TZX estándar creado: {filename}')
    print(f'  Solo bloques 0x10 (sin GDB)')


if __name__ == '__main__':
    print("=== Creando archivos de prueba v2 ===\n")
    
    create_pure_standard_test('test_standard.tzx')
    print()
    
    create_working_gdb_tzx('test_gdb_asym_v2.tzx', symmetric=False)
    print()
    
    create_working_gdb_tzx('test_gdb_sym_v2.tzx', symmetric=True)
    print()
    
    print("=== Instrucciones de prueba ===")
    print("1. Primero prueba test_standard.tzx - debe cargar correctamente")
    print("2. Luego test_gdb_sym_v2.tzx - cabecera estándar + datos GDB simétricos")
    print("3. Finalmente test_gdb_asym_v2.tzx - cabecera estándar + datos GDB asimétricos")
