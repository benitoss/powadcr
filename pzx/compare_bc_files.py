import struct

def analyze_tzx(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f'=== {filepath} ===')
    print(f'File size: {len(data)} bytes')
    
    # Verificar header TZX
    header = data[0:7]
    print(f'Header: {header}')
    
    # Buscar bloque 0x19
    pos = 10
    block_num = 0
    while pos < len(data):
        block_id = data[pos]
        block_num += 1
        
        if block_id == 0x19:
            block_len = struct.unpack('<I', data[pos+1:pos+5])[0]
            pause = struct.unpack('<H', data[pos+5:pos+7])[0]
            TOTP = struct.unpack('<I', data[pos+7:pos+11])[0]
            NPP = data[pos+11]
            ASP = data[pos+12]
            TOTD = struct.unpack('<I', data[pos+13:pos+17])[0]
            NPD = data[pos+17]
            ASD = data[pos+18]
            
            NB = 0
            tmp = ASD - 1
            while tmp > 0:
                NB += 1
                tmp >>= 1
            DS = (NB * TOTD + 7) // 8
            
            print(f'Block #{block_num}: ID 0x19 at offset {pos}')
            print(f'  Block length: {block_len}')
            print(f'  TOTP={TOTP}, NPP={NPP}, ASP={ASP}')
            print(f'  TOTD={TOTD}, NPD={NPD}, ASD={ASD}')
            print(f'  NB={NB}, DS={DS}')
            
            # Calcular offset del datastream
            pilot_def_size = ASP * (1 + NPP * 2)
            pilot_stream_size = TOTP * 3
            data_def_size = ASD * (1 + NPD * 2)
            ds_offset = pos + 19 + pilot_def_size + pilot_stream_size + data_def_size
            print(f'  DataStream offset: {ds_offset}')
            print(f'  DataStream ends at: {ds_offset + DS}')
            
            # Mostrar primeros y ultimos bytes del DS
            ds_data = data[ds_offset:ds_offset+DS]
            print(f'  First 10 bytes: {ds_data[:10].hex()}')
            print(f'  Last 10 bytes: {ds_data[-10:].hex()}')
            
            return ds_data, ds_offset
            
        # Avanzar al siguiente bloque
        if block_id == 0x10:
            bl = struct.unpack('<H', data[pos+3:pos+5])[0]
            pos += 5 + bl
        elif block_id == 0x11:
            bl = struct.unpack('<I', data[pos+1:pos+4] + b'\x00')[0] & 0xFFFFFF
            pos += 19 + bl
        elif block_id == 0x19:
            bl = struct.unpack('<I', data[pos+1:pos+5])[0]
            pos += 5 + bl
        elif block_id == 0x30:
            bl = data[pos+1]
            pos += 2 + bl
        elif block_id == 0x32:
            bl = struct.unpack('<H', data[pos+1:pos+3])[0]
            pos += 3 + bl
        else:
            print(f'Block #{block_num}: ID 0x{block_id:02X} at offset {pos}')
            pos += 1
    
    return None, 0

print()
ds1, off1 = analyze_tzx('BC_malo.tzx')
print()
ds2, off2 = analyze_tzx("BC's Quest for Tires.tzx")

# Comparar los datastreams
if ds1 and ds2:
    print()
    print('=== COMPARACION ===')
    print(f'DS malo:  {len(ds1)} bytes')
    print(f'DS bueno: {len(ds2)} bytes')
    
    min_len = min(len(ds1), len(ds2))
    diff_count = 0
    first_diff = -1
    
    for i in range(min_len):
        if ds1[i] != ds2[i]:
            if first_diff == -1:
                first_diff = i
            diff_count += 1
            if diff_count <= 30:
                print(f'Diff at byte {i}: malo=0x{ds1[i]:02X}, bueno=0x{ds2[i]:02X}')
    
    if first_diff >= 0:
        print()
        print(f'Primera diferencia en byte: {first_diff}')
        print(f'Total diferencias: {diff_count}')
        print(f'Porcentaje donde empieza la corrupcion: {first_diff * 100 / min_len:.2f}%')
    else:
        print('Los datastreams son IDENTICOS en los primeros', min_len, 'bytes')
