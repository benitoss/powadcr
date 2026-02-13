import struct

with open('ATF.tzx', 'rb') as f:
    data = f.read()

print('=== ATF.tzx Full Analysis ===')
print(f'Header: {data[:7]}')
print(f'Version: {data[8]}.{data[9]}')

offset = 10
block_num = 0
while offset < len(data):
    block_id = data[offset]
    block_num += 1
    print(f'\nBlock {block_num}: ID 0x{block_id:02X} at offset {offset} (0x{offset:X})')
    
    if block_id == 0x10:  # Standard
        pause = struct.unpack('<H', data[offset+1:offset+3])[0]
        length = struct.unpack('<H', data[offset+3:offset+5])[0]
        flag = data[offset+5] if length > 0 else 0
        print(f'  Standard Speed Data Block')
        print(f'  Pause: {pause}ms, Length: {length}, Flag: 0x{flag:02X}')
        if flag == 0 and length >= 18:
            name = data[offset+6:offset+16].decode('ascii', errors='replace')
            print(f'  Name: "{name}"')
        offset += 5 + length
    elif block_id == 0x11:  # Turbo
        pilot = struct.unpack('<H', data[offset+1:offset+3])[0]
        sync1 = struct.unpack('<H', data[offset+3:offset+5])[0]
        sync2 = struct.unpack('<H', data[offset+5:offset+7])[0]
        zero = struct.unpack('<H', data[offset+7:offset+9])[0]
        one = struct.unpack('<H', data[offset+9:offset+11])[0]
        pilot_len = struct.unpack('<H', data[offset+11:offset+13])[0]
        used_bits = data[offset+13]
        pause = struct.unpack('<H', data[offset+14:offset+16])[0]
        length = struct.unpack('<I', data[offset+16:offset+19] + b'\x00')[0]
        print(f'  Turbo Speed Data Block')
        print(f'  Pilot: {pilot}T x {pilot_len}')
        print(f'  Sync1: {sync1}T, Sync2: {sync2}T')
        print(f'  Zero: {zero}T, One: {one}T')
        print(f'  Used bits last byte: {used_bits}')
        print(f'  Pause: {pause}ms, Length: {length}')
        offset += 19 + length
    elif block_id == 0x12:  # Pure tone
        pulse = struct.unpack('<H', data[offset+1:offset+3])[0]
        count = struct.unpack('<H', data[offset+3:offset+5])[0]
        print(f'  Pure Tone: {count} pulses of {pulse}T')
        offset += 5
    elif block_id == 0x13:  # Pulse sequence
        count = data[offset+1]
        pulses = []
        for i in range(count):
            p = struct.unpack('<H', data[offset+2+i*2:offset+4+i*2])[0]
            pulses.append(p)
        print(f'  Pulse Sequence: {pulses}')
        offset += 2 + count * 2
    elif block_id == 0x14:  # Pure data
        zero = struct.unpack('<H', data[offset+1:offset+3])[0]
        one = struct.unpack('<H', data[offset+3:offset+5])[0]
        used_bits = data[offset+5]
        pause = struct.unpack('<H', data[offset+6:offset+8])[0]
        length = struct.unpack('<I', data[offset+8:offset+11] + b'\x00')[0]
        print(f'  Pure Data Block')
        print(f'  Zero: {zero}T, One: {one}T')
        print(f'  Used bits: {used_bits}, Pause: {pause}ms, Length: {length}')
        offset += 11 + length
    elif block_id == 0x19:  # GDB
        block_len = struct.unpack('<I', data[offset+1:offset+5])[0]
        print(f'  Generalized Data Block, size: {block_len}')
        offset += 5 + block_len
    elif block_id == 0x20:  # Pause
        pause = struct.unpack('<H', data[offset+1:offset+3])[0]
        print(f'  Pause: {pause}ms')
        offset += 3
    elif block_id == 0x21:  # Group start
        length = data[offset+1]
        name = data[offset+2:offset+2+length].decode('ascii', errors='replace')
        print(f'  Group Start: "{name}"')
        offset += 2 + length
    elif block_id == 0x22:  # Group end
        print(f'  Group End')
        offset += 1
    elif block_id == 0x30:  # Text
        length = data[offset+1]
        text = data[offset+2:offset+2+length].decode('ascii', errors='replace')
        print(f'  Text Description: "{text}"')
        offset += 2 + length
    elif block_id == 0x32:  # Archive info
        length = struct.unpack('<H', data[offset+1:offset+3])[0]
        print(f'  Archive Info, length: {length}')
        offset += 3 + length
    elif block_id == 0x33:  # Hardware type
        count = data[offset+1]
        print(f'  Hardware Type, {count} entries')
        offset += 2 + count * 3
    elif block_id == 0x35:  # Custom info
        label = data[offset+1:offset+17].decode('ascii', errors='replace').strip()
        length = struct.unpack('<I', data[offset+17:offset+21])[0]
        print(f'  Custom Info: "{label}", length: {length}')
        offset += 21 + length
    else:
        print(f'  Unknown block type')
        break
        
print(f'\nTotal blocks: {block_num}')
