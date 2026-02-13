#!/usr/bin/env python3
"""Analiza bloques PZX del archivo Book of the Dead"""

import struct
import os

def read_pzx_file(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    return data

def parse_puls_block(data, offset, size):
    """Parsea un bloque PULS y devuelve info de los pulsos"""
    pulses = []
    pos = 0
    block_data = data[offset:offset+size]
    
    while pos < size:
        if pos + 2 > size:
            break
            
        val = struct.unpack('<H', block_data[pos:pos+2])[0]
        pos += 2
        
        count = 1
        duration = 0
        
        if val > 0x8000:
            # Bit 15 = 1: Es un repeat count
            count = val & 0x7FFF
            if pos + 2 > size:
                break
            duration = struct.unpack('<H', block_data[pos:pos+2])[0]
            pos += 2
        elif val == 0x8000:
            # Caso especial: indica duración extendida sin count
            if pos + 2 > size:
                break
            duration = struct.unpack('<H', block_data[pos:pos+2])[0]
            pos += 2
        else:
            duration = val
            
        # Verificar si duración es de 31 bits
        if duration >= 0x8000:
            high_bits = duration & 0x7FFF
            if pos + 2 > size:
                break
            low_bits = struct.unpack('<H', block_data[pos:pos+2])[0]
            pos += 2
            duration = (high_bits << 16) | low_bits
            
        pulses.append({'count': count, 'duration': duration})
    
    return pulses

def parse_data_block(data, offset, size):
    """Parsea un bloque DATA y devuelve sus parámetros"""
    if size < 8:
        return None
    
    block_data = data[offset:offset+size]
    count_field = struct.unpack('<I', block_data[0:4])[0]
    
    num_bits = count_field & 0x7FFFFFFF
    initial_level = (count_field >> 31) & 1
    
    tail = struct.unpack('<H', block_data[4:6])[0]
    p0 = block_data[6]
    p1 = block_data[7]
    
    # Leer secuencias s0 y s1
    s0 = []
    s1 = []
    pos = 8
    for i in range(p0):
        if pos + 2 <= size:
            s0.append(struct.unpack('<H', block_data[pos:pos+2])[0])
            pos += 2
    for i in range(p1):
        if pos + 2 <= size:
            s1.append(struct.unpack('<H', block_data[pos:pos+2])[0])
            pos += 2
    
    return {
        'num_bits': num_bits,
        'initial_level': 'HIGH' if initial_level else 'LOW',
        'tail': tail,
        'p0': p0, 'p1': p1,
        's0': s0, 's1': s1,
        'data_bytes': (num_bits + 7) // 8
    }

def parse_paus_block(data, offset, size):
    """Parsea un bloque PAUS"""
    if size < 4:
        return None
    block_data = data[offset:offset+size]
    duration_field = struct.unpack('<I', block_data[0:4])[0]
    
    duration = duration_field & 0x7FFFFFFF
    initial_level = (duration_field >> 31) & 1
    
    return {
        'duration': duration,
        'initial_level': 'HIGH' if initial_level else 'LOW'
    }

def analyze_pzx(filepath):
    data = read_pzx_file(filepath)
    pos = 0
    blocks = []
    block_num = 0
    
    while pos < len(data) - 8:
        tag = data[pos:pos+4].decode('ascii', errors='replace')
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        block_offset = pos
        data_offset = pos + 8
        
        block_info = {
            'num': block_num,
            'tag': tag,
            'offset': block_offset,
            'data_offset': data_offset,
            'size': size,
            'params': None
        }
        
        if tag == 'PULS':
            pulses = parse_puls_block(data, data_offset, size)
            block_info['params'] = pulses
            
            # Analizar si hay pulso de duración 0
            has_zero_pulse = any(p['duration'] == 0 for p in pulses)
            first_pulse_zero = pulses[0]['duration'] == 0 if pulses else False
            block_info['has_zero_pulse'] = has_zero_pulse
            block_info['first_zero'] = first_pulse_zero
            block_info['effective_start'] = 'HIGH' if first_pulse_zero else 'LOW'
            block_info['num_pulses'] = len(pulses)
            block_info['total_pulses'] = sum(p['count'] for p in pulses)
            
        elif tag == 'DATA':
            block_info['params'] = parse_data_block(data, data_offset, size)
            
        elif tag == 'PAUS':
            block_info['params'] = parse_paus_block(data, data_offset, size)
            
        elif tag == 'PZXT':
            # Header block
            if size >= 2:
                major = data[data_offset]
                minor = data[data_offset + 1]
                # Leer strings
                strings = []
                str_pos = data_offset + 2
                current_str = b''
                while str_pos < data_offset + size:
                    b = data[str_pos]
                    if b == 0:
                        if current_str:
                            strings.append(current_str.decode('utf-8', errors='replace'))
                        current_str = b''
                    else:
                        current_str += bytes([b])
                    str_pos += 1
                if current_str:
                    strings.append(current_str.decode('utf-8', errors='replace'))
                    
                block_info['params'] = {
                    'version': f'{major}.{minor}',
                    'title': strings[0] if strings else '',
                    'info': strings[1:] if len(strings) > 1 else []
                }
        
        elif tag == 'STOP':
            if size >= 2:
                flags = struct.unpack('<H', data[data_offset:data_offset+2])[0]
                block_info['params'] = {'flags': flags, 'condition': '48k only' if flags == 1 else 'always'}
        
        elif tag == 'BRWS':
            text = data[data_offset:data_offset+size].decode('utf-8', errors='replace').rstrip('\x00')
            block_info['params'] = {'text': text}
        
        blocks.append(block_info)
        pos += 8 + size
        block_num += 1
    
    return blocks

def main():
    filepath = r"pzxsamples\gdb\Book Of The Dead - Part 1 (CRL).pzx"
    
    if not os.path.exists(filepath):
        print(f"Error: No se encuentra {filepath}")
        return
    
    blocks = analyze_pzx(filepath)
    
    print("=" * 120)
    print(f"ANÁLISIS PZX: {filepath}")
    print("=" * 120)
    
    # Tabla principal
    print(f"\n{'#':>3} | {'TAG':^6} | {'Offset':>8} | {'Size':>8} | {'Nivel Inicial':^14} | {'Detalles'}")
    print("-" * 120)
    
    for b in blocks:
        tag = b['tag']
        offset = f"0x{b['offset']:06X}"
        size = b['size']
        
        if tag == 'PZXT':
            params = b['params']
            nivel = '-'
            detalles = f"v{params['version']} - {params['title']}"
            
        elif tag == 'PULS':
            nivel = b['effective_start']
            first_zero = "Sí" if b['first_zero'] else "No"
            detalles = f"Entradas: {b['num_pulses']}, Total pulsos: {b['total_pulses']}, Primer pulso=0: {first_zero}"
            
        elif tag == 'DATA':
            params = b['params']
            if params:
                nivel = params['initial_level']
                detalles = f"Bits: {params['num_bits']}, Bytes: {params['data_bytes']}, Tail: {params['tail']}, p0={params['p0']}, p1={params['p1']}"
            else:
                nivel = '?'
                detalles = 'Error parsing'
                
        elif tag == 'PAUS':
            params = b['params']
            if params:
                nivel = params['initial_level']
                duration_ms = params['duration'] / 3500  # T-states a ms
                detalles = f"Duración: {params['duration']} T ({duration_ms:.1f} ms)"
            else:
                nivel = '?'
                detalles = 'Error parsing'
                
        elif tag == 'BRWS':
            nivel = '-'
            detalles = f'"{b["params"]["text"]}"' if b['params'] else ''
            
        elif tag == 'STOP':
            nivel = '-'
            detalles = f"Condición: {b['params']['condition']}" if b['params'] else ''
            
        else:
            nivel = '-'
            detalles = ''
        
        print(f"{b['num']:>3} | {tag:^6} | {offset:>8} | {size:>8} | {nivel:^14} | {detalles}")
    
    # Detalle de bloques PULS
    print("\n" + "=" * 120)
    print("DETALLE DE BLOQUES PULS")
    print("=" * 120)
    
    for b in blocks:
        if b['tag'] == 'PULS':
            print(f"\nBloque #{b['num']} @ 0x{b['offset']:06X}")
            print(f"  Nivel inicial efectivo: {b['effective_start']}")
            print(f"  Primer pulso duración=0: {'SÍ (invierte nivel)' if b['first_zero'] else 'NO'}")
            print(f"  Pulsos:")
            
            pulses = b['params']
            level = 'LOW'  # Siempre empieza en LOW
            
            print(f"    {'#':>3} | {'Count':>6} | {'Duración':>10} | {'Nivel al emitir':^16} | {'Nivel después':^14}")
            print("    " + "-" * 70)
            
            for i, p in enumerate(pulses[:20]):  # Solo primeros 20 para no saturar
                nivel_emision = level
                # Calcular nivel después de este pulso (cambia por cada repetición)
                for _ in range(p['count']):
                    level = 'HIGH' if level == 'LOW' else 'LOW'
                nivel_despues = level
                
                dur_str = f"{p['duration']}" if p['duration'] > 0 else "0 (toggle)"
                print(f"    {i:>3} | {p['count']:>6} | {dur_str:>10} | {nivel_emision:^16} | {nivel_despues:^14}")
            
            if len(pulses) > 20:
                print(f"    ... y {len(pulses) - 20} entradas más")

if __name__ == '__main__':
    main()
