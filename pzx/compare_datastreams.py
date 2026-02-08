import struct
import math

def analyze_gdb_datastream(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Buscar bloque 0x19 (GDB)
    offset = 10
    while offset < len(data):
        block_id = data[offset]
        if block_id == 0x19:
            # GDB encontrado
            block_len = struct.unpack('<I', data[offset+1:offset+5])[0]
            
            # Pilot/Sync definitions
            TOTP = struct.unpack('<I', data[offset+7:offset+11])[0]
            NPP = data[offset+11]
            ASP = data[offset+12]
            
            # Data definitions  
            TOTD = struct.unpack('<I', data[offset+13:offset+17])[0]
            NPD = data[offset+17]
            ASD = data[offset+18]
            
            # Skip to datastream
            pos = offset + 19
            
            # Skip SYMDEF pilot/sync
            for s in range(ASP):
                pos += 1  # flag
                pos += NPP * 2  # pulses
            
            # Skip PRLE
            pos += TOTP * 3
            
            # Skip SYMDEF data
            for s in range(ASD):
                pos += 1  # flag
                pos += NPD * 2  # pulses
            
            # Now at datastream
            NB = math.ceil(math.log(ASD) / math.log(2))
            DS = math.ceil(NB * TOTD / 8)
            
            return {
                'filename': filename,
                'TOTD': TOTD,
                'DS': DS,
                'datastream': data[pos:pos+DS],
                'first_256': data[pos:pos+256],
                'last_256': data[pos+DS-256:pos+DS] if DS >= 256 else data[pos:pos+DS]
            }
        else:
            if block_id == 0x10:
                offset += 5 + struct.unpack('<H', data[offset+3:offset+5])[0]
            elif block_id == 0x11:
                bl = struct.unpack('<I', data[offset+1:offset+4] + b'\x00')[0]
                offset += 19 + bl
            elif block_id == 0x12:
                offset += 5
            elif block_id == 0x13:
                offset += 2 + data[offset+1] * 2
            elif block_id == 0x14:
                bl = struct.unpack('<I', data[offset+8:offset+11] + b'\x00')[0]
                offset += 11 + bl
            elif block_id == 0x15:
                bl = struct.unpack('<I', data[offset+6:offset+9] + b'\x00')[0]
                offset += 9 + bl
            elif block_id == 0x19:
                offset += 5 + struct.unpack('<I', data[offset+1:offset+5])[0]
            elif block_id == 0x20:
                offset += 3
            elif block_id == 0x21:
                offset += 2 + data[offset+1]
            elif block_id == 0x22:
                offset += 1
            elif block_id == 0x30:
                offset += 2 + data[offset+1]
            elif block_id == 0x32:
                offset += 3 + struct.unpack('<H', data[offset+1:offset+3])[0]
            elif block_id == 0x33:
                offset += 2 + data[offset+1] * 3
            elif block_id == 0x35:
                offset += 21 + struct.unpack('<I', data[offset+17:offset+21])[0]
            elif block_id == 0x5A:
                offset += 10
            elif block_id == 0x87:
                # Custom block - try to skip
                offset += 1
            else:
                print(f"Unknown block 0x{block_id:02X} at offset {offset}")
                break
    return None

# Analyze both files
bc = analyze_gdb_datastream("BC's Quest for Tires.tzx")
kr = analyze_gdb_datastream("Knight Rider (1986)(Ocean).tzx")

print("=" * 70)
print("DATASTREAM COMPARISON")
print("=" * 70)

print(f"\nBC's Quest:")
print(f"  TOTD: {bc['TOTD']}")
print(f"  DS (bytes): {bc['DS']}")

print(f"\nKnight Rider:")
print(f"  TOTD: {kr['TOTD']}")
print(f"  DS (bytes): {kr['DS']}")

print("\n" + "=" * 70)
print("FIRST 64 BYTES OF DATASTREAM")
print("=" * 70)

print("\nBC's Quest (first 64 bytes):")
for i in range(0, 64, 16):
    hex_str = ' '.join(f'{b:02X}' for b in bc['first_256'][i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in bc['first_256'][i:i+16])
    print(f"  {i:04X}: {hex_str}  {ascii_str}")

print("\nKnight Rider (first 64 bytes):")
for i in range(0, 64, 16):
    hex_str = ' '.join(f'{b:02X}' for b in kr['first_256'][i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in kr['first_256'][i:i+16])
    print(f"  {i:04X}: {hex_str}  {ascii_str}")

# Check if they're the same
if bc['datastream'] == kr['datastream']:
    print("\n*** DATASTREAMS ARE IDENTICAL! ***")
else:
    # Find first difference
    for i, (b1, b2) in enumerate(zip(bc['datastream'], kr['datastream'])):
        if b1 != b2:
            print(f"\n*** FIRST DIFFERENCE at byte {i}: BC={b1:02X}, KR={b2:02X} ***")
            break
    
    # Count differences
    diff_count = sum(1 for b1, b2 in zip(bc['datastream'], kr['datastream']) if b1 != b2)
    print(f"*** Total different bytes: {diff_count} out of {len(bc['datastream'])} ***")

# Analyze bit distribution
print("\n" + "=" * 70)
print("BIT DISTRIBUTION (first 1000 bytes)")
print("=" * 70)

def count_bits(data, max_bytes=1000):
    zeros = 0
    ones = 0
    for byte in data[:max_bytes]:
        for bit in range(8):
            if (byte >> bit) & 1:
                ones += 1
            else:
                zeros += 1
    return zeros, ones

bc_zeros, bc_ones = count_bits(bc['datastream'])
kr_zeros, kr_ones = count_bits(kr['datastream'])

print(f"\nBC's Quest: {bc_zeros} zeros, {bc_ones} ones ({bc_ones/(bc_zeros+bc_ones)*100:.1f}% ones)")
print(f"Knight Rider: {kr_zeros} zeros, {kr_ones} ones ({kr_ones/(kr_zeros+kr_ones)*100:.1f}% ones)")
