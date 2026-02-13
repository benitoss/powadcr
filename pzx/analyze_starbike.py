import struct

with open('pzxsamples/csw/StarBike1.pzx', 'rb') as f:
    data = f.read()

print(f'=== ANALISIS STARBIKE1.PZX ===')
print(f'Tamano total: {len(data)} bytes')
print()

# Header PZX
if data[0:4] != b'PZXT':
    print('ERROR: No es un archivo PZX valido')
else:
    print('Header: PZXT (OK)')
    header_size = struct.unpack('<I', data[4:8])[0]
    print(f'Header size: {header_size}')
    if header_size >= 2:
        major = data[8]
        minor = data[9]
        print(f'Version: {major}.{minor}')
    print()

offset = 8 + header_size
block_num = 0

while offset < len(data) - 4:
    tag = data[offset:offset+4]
    if offset + 8 > len(data):
        break
    size = struct.unpack('<I', data[offset+4:offset+8])[0]
    
    print(f'--- Bloque {block_num} @ offset {offset} ---')
    tag_str = tag.decode("ascii", errors="replace")
    print(f'Tag: {tag_str}')
    print(f'Size: {size}')
    
    if offset + 8 + size > len(data):
        print(f'ERROR: Bloque truncado!')
        break
    
    block_data = data[offset+8:offset+8+size]
    
    if tag == b'PULS':
        print('Tipo: PULS')
        # Analizar pulsos
        i = 0
        pulse_count = 0
        while i < len(block_data):
            if i + 2 > len(block_data):
                break
            count = struct.unpack('<H', block_data[i:i+2])[0]
            i += 2
            
            if count == 0:
                if i + 2 > len(block_data):
                    break
                count = struct.unpack('<H', block_data[i:i+2])[0]
                i += 2
                if count == 0:
                    if i + 4 > len(block_data):
                        break
                    count = struct.unpack('<I', block_data[i:i+4])[0]
                    i += 4
            
            if count > 0x8000:
                duration = count & 0x7FFF
                print(f'  Pulso unico: {duration} T-states')
                pulse_count += 1
            else:
                if i + 2 > len(block_data):
                    break
                duration = struct.unpack('<H', block_data[i:i+2])[0]
                i += 2
                print(f'  Pulso: {duration} T-states x{count}')
                pulse_count += count
        print(f'  Total pulsos: {pulse_count}')
        
    elif tag == b'DATA':
        print('Tipo: DATA')
        if len(block_data) >= 4:
            count_raw = struct.unpack('<I', block_data[0:4])[0]
            initial_high = (count_raw & 0x80000000) != 0
            bit_count = count_raw & 0x7FFFFFFF
            pol = 'HIGH' if initial_high else 'LOW'
            print(f'  Bit count: {bit_count}, Initial level: {pol}')
            
    elif tag == b'PAUS':
        print('Tipo: PAUS')
        if len(block_data) >= 4:
            dur_raw = struct.unpack('<I', block_data[0:4])[0]
            duration = dur_raw & 0x7FFFFFFF
            print(f'  Duration: {duration} T-states ({duration/3500000*1000:.2f} ms)')
            
    elif tag == b'BRWS':
        print('Tipo: BRWS (browse point)')
        text = block_data.decode('utf-8', errors='replace').rstrip('\x00')
        print(f'  Text: {text}')
        
    elif tag == b'STOP':
        print('Tipo: STOP')
        
    else:
        print(f'Tipo: {tag_str}')
        if len(block_data) > 0:
            print(f'  Primeros bytes: {block_data[:min(32,len(block_data))].hex()}')
    
    print()
    offset += 8 + size
    block_num += 1

print(f'=== FIN ===')
print(f'Bloques: {block_num}')
