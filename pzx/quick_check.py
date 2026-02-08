import struct
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Find BC's Quest file
tzx_file = None
for f in os.listdir('.'):
    if 'BC' in f and f.endswith('.tzx'):
        tzx_file = f
        break

if not tzx_file:
    print("BC's Quest file not found!")
    exit(1)

print(f"Opening: {tzx_file}")

with open(tzx_file, 'rb') as f:
    data = f.read()

print(f"File size: {len(data)} bytes")
print()

# First list all blocks
print("=== BLOCKS IN FILE ===")
offset = 10
block_list = []
while offset < len(data):
    block_id = data[offset]
    block_list.append((block_id, offset))
    print(f"Block 0x{block_id:02X} at offset {offset}")
    
    if block_id == 0x10:
        length = struct.unpack('<H', data[offset+3:offset+5])[0]
        offset += 5 + length
    elif block_id == 0x11:
        length = struct.unpack('<I', data[offset+16:offset+19] + b'\x00')[0]
        offset += 19 + length
    elif block_id == 0x19:
        length = struct.unpack('<I', data[offset+1:offset+5])[0]
        offset += 5 + length
    elif block_id == 0x30:
        length = data[offset+1]
        offset += 2 + length
    elif block_id == 0x32:
        length = struct.unpack('<H', data[offset+1:offset+3])[0]
        offset += 3 + length
    else:
        print(f"  Unknown block, stopping")
        break

print()

# Now analyze GDB blocks in detail
for block_id, block_offset in block_list:
    if block_id == 0x19:
        offset = block_offset
        print(f"=== GDB BLOCK at {offset} ===")
        
        TOTP = struct.unpack('<I', data[offset+7:offset+11])[0]
        NPP = data[offset+11]
        ASP = data[offset+12]
        TOTD = struct.unpack('<I', data[offset+13:offset+17])[0]
        NPD = data[offset+17]
        ASD = data[offset+18]
        
        print(f'Pilot/Sync: TOTP={TOTP}, NPP={NPP}, ASP={ASP}')
        print(f'Data:       TOTD={TOTD}, NPD={NPD}, ASD={ASD}')
        print()
        
        pos = offset + 19
        print('=== PILOT SYMDEF ===')
        for s in range(ASP):
            flag = data[pos]
            pulses = []
            for p in range(NPP):
                pulse = struct.unpack('<H', data[pos+1+p*2:pos+3+p*2])[0]
                pulses.append(pulse)
            print(f'  Symbol {s}: flag={flag}, pulses={pulses}')
            pos += 1 + NPP*2
        
        print()
        print('=== PILOT PRLE (first 10) ===')
        for p in range(min(TOTP, 10)):
            sym = data[pos]
            rep = struct.unpack('<H', data[pos+1:pos+3])[0]
            print(f'  PRLE[{p}]: symbol={sym}, rep={rep}')
            pos += 3
        if TOTP > 10:
            print(f'  ... ({TOTP-10} more entries)')
            pos += (TOTP - 10) * 3
            
        print()
        print('=== DATA SYMDEF ===')
        for s in range(ASD):
            flag = data[pos]
            pulses = []
            for p in range(NPD):
                pulse = struct.unpack('<H', data[pos+1+p*2:pos+3+p*2])[0]
                pulses.append(pulse)
            print(f'  Symbol {s}: flag={flag}, pulses={pulses}')
            pos += 1 + NPD*2
        print()
        break

# Also show Dan Dare 2 for comparison
dan_dare = None
for f in os.listdir('.'):
    if 'Dan Dare' in f and f.endswith('.tzx'):
        dan_dare = f
        break

if dan_dare:
    print()
    print("=" * 50)
    print(f"=== COMPARISON: {dan_dare} ===")
    print("=" * 50)
    with open(dan_dare, 'rb') as f:
        data = f.read()
    
    offset = 10
    while offset < len(data):
        block_id = data[offset]
        if block_id == 0x19:
            print(f"GDB Block at offset {offset}")
            TOTP = struct.unpack('<I', data[offset+7:offset+11])[0]
            NPP = data[offset+11]
            ASP = data[offset+12]
            TOTD = struct.unpack('<I', data[offset+13:offset+17])[0]
            NPD = data[offset+17]
            ASD = data[offset+18]
            
            print(f'  Pilot/Sync: TOTP={TOTP}, NPP={NPP}, ASP={ASP}')
            print(f'  Data:       TOTD={TOTD}, NPD={NPD}, ASD={ASD}')
            
            pos = offset + 19
            print('  Pilot SYMDEF:')
            for s in range(ASP):
                flag = data[pos]
                pulses = []
                for p in range(NPP):
                    pulse = struct.unpack('<H', data[pos+1+p*2:pos+3+p*2])[0]
                    pulses.append(pulse)
                print(f'    Symbol {s}: flag={flag}, pulses={pulses}')
                pos += 1 + NPP*2
            
            print('  Data SYMDEF:')
            pos += TOTP * 3  # Skip PRLE
            for s in range(ASD):
                flag = data[pos]
                pulses = []
                for p in range(NPD):
                    pulse = struct.unpack('<H', data[pos+1+p*2:pos+3+p*2])[0]
                    pulses.append(pulse)
                print(f'    Symbol {s}: flag={flag}, pulses={pulses}')
                pos += 1 + NPD*2
            break
            
        elif block_id == 0x10:
            length = struct.unpack('<H', data[offset+3:offset+5])[0]
            offset += 5 + length
        elif block_id == 0x11:
            length = struct.unpack('<I', data[offset+16:offset+19] + b'\x00')[0]
            offset += 19 + length
        elif block_id == 0x19:
            length = struct.unpack('<I', data[offset+1:offset+5])[0]
            offset += 5 + length
        elif block_id == 0x30:
            length = data[offset+1]
            offset += 2 + length
        elif block_id == 0x32:
            length = struct.unpack('<H', data[offset+1:offset+3])[0]
            offset += 3 + length
        else:
            break
