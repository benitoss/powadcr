#!/usr/bin/env python3
"""
Verifica cómo está codificado realmente el PRLE en bloques GDB
"""
import struct
import math

def analyze_gdb_prle(tzx_file, gdb_offset):
    with open(tzx_file, 'rb') as f:
        data = f.read()
    
    print(f"=== Analyzing GDB at offset {gdb_offset} ===\n")
    
    pos = gdb_offset + 1  # Skip block ID
    
    # Block length
    block_len = struct.unpack('<I', data[pos:pos+4])[0]
    pos += 4
    print(f"Block length: {block_len} bytes")
    
    # Pause
    pause = struct.unpack('<H', data[pos:pos+2])[0]
    pos += 2
    print(f"Pause: {pause} ms")
    
    # TOTP, NPP, ASP
    totp = struct.unpack('<I', data[pos:pos+4])[0]
    pos += 4
    npp = data[pos]
    pos += 1
    asp = data[pos] if data[pos] != 0 else 256
    pos += 1
    
    print(f"TOTP: {totp}, NPP: {npp}, ASP: {asp}")
    
    # TOTD, NPD, ASD
    totd = struct.unpack('<I', data[pos:pos+4])[0]
    pos += 4
    npd = data[pos]
    pos += 1
    asd = data[pos] if data[pos] != 0 else 256
    pos += 1
    
    print(f"TOTD: {totd}, NPD: {npd}, ASD: {asd}\n")
    
    # Skip SYMDEF pilot table
    symdef_pilot_size = asp * (1 + npp * 2)
    print(f"SYMDEF pilot table: {symdef_pilot_size} bytes")
    pos += symdef_pilot_size
    
    # PRLE encoding
    print(f"\n=== PRLE Stream (offset {pos}) ===")
    print("Según TZX spec:")
    bits_per_symbol = max(1, math.ceil(math.log2(asp))) if asp > 1 else 1
    print(f"  Bits per symbol (ceil(log2({asp}))): {bits_per_symbol}")
    total_bits = totp * bits_per_symbol
    prle_bytes_spec = math.ceil(total_bits / 8)
    print(f"  Total bits needed: {total_bits}")
    print(f"  PRLE stream bytes (spec): {prle_bytes_spec}")
    
    print("\nPero el código actual lee:")
    prle_bytes_actual = totp * 3  # 1 byte symbol + 2 bytes repeat
    print(f"  PRLE stream bytes (actual): {prle_bytes_actual} (1 byte + 2 bytes) x {totp}")
    
    print(f"\n¿Son iguales? {prle_bytes_spec == prle_bytes_actual}")
    
    # Leer según código actual (1 byte symbol + 2 bytes repeat)
    print("\n=== Reading PRLE as current code does ===")
    for i in range(min(totp, 10)):  # First 10 entries
        symbol = data[pos]
        repeat = struct.unpack('<H', data[pos+1:pos+3])[0]
        print(f"  [{i}] Symbol: {symbol}, Repeat: {repeat}")
        pos += 3
    
    if totp > 10:
        print(f"  ... ({totp - 10} more entries)")
    
    return prle_bytes_spec == prle_bytes_actual

# Test con Dan Dare 2 (funciona)
print("=" * 70)
print("DAN DARE 2 - Bloque GDB #8")
print("=" * 70)
result1 = analyze_gdb_prle("Dan Dare 2 - Mekon's Revenge.tzx", 5444)

print("\n" + "=" * 70)
print("BC'S QUEST - Bloque GDB")
print("=" * 70)
result2 = analyze_gdb_prle("BC's Quest for Tires.tzx", 590)

print("\n" + "=" * 70)
print("CONCLUSIÓN")
print("=" * 70)
if result1 and result2:
    print("✓ El código actual de PRLE coincide con la spec para ambos juegos")
else:
    print("✗ HAY UN PROBLEMA: El código no lee PRLE correctamente")
    print("  La spec dice que PRLE es un bitstream compacto, no bytes individuales")
