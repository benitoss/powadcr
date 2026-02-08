with open("BC's Quest for Tires.tzx", 'rb') as f:
    data = f.read()
    print('Total length:', len(data))
    pos = data.find(b'\x19')
    if pos != -1:
        print(f'Found 0x19 at position {pos}')
    else:
        print('No 0x19 found')
    print('Block IDs:')
    offset = 9
    while offset < len(data):
        if offset + 1 < len(data):
            block_id = data[offset]
            print(f'Offset {offset}: ID {hex(block_id)}')
            if block_id == 0x14:
                # skip
                offset += 1 + 2 + 2 + 1 + 2 + 3 + (data[offset+7] | (data[offset+8] << 8) | (data[offset+9] << 16))
            else:
                break
        else:
            break