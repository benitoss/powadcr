#!/usr/bin/env python3
"""Analizar wizball.pzx para ver información de polaridad"""
import struct

with open('wizball.pzx', 'rb') as f:
    data = f.read()

print(f'Tamano total: {len(data)} bytes')
print(f'PZX Version: {data[4]}.{data[5]}')
print()

offset = 8
block_num = 0

while offset + 8 <= len(data):
    tag = data[offset:offset+4]
    size = struct.unpack('<I', data[offset+4:offset+8])[0]
    
    tag_str = tag.decode('ascii', errors='replace')
    print(f'Bloque {block_num}: {tag_str} @ offset {offset}, size {size}')
    
    if offset + 8 + size > len(data):
        print('  ERROR: Bloque truncado')
        break
        
    block_data = data[offset+8:offset+8+size]
    
    if tag == b'DATA':
        count_raw = struct.unpack('<I', block_data[0:4])[0]
        initial_high = (count_raw & 0x80000000) != 0
        bit_count = count_raw & 0x7FFFFFFF
        
        tail = struct.unpack('<H', block_data[4:6])[0]
        p0 = struct.unpack('<H', block_data[6:8])[0]
        p1 = struct.unpack('<H', block_data[8:10])[0]
        
        pol = "HIGH" if initial_high else "LOW"
        print(f'  *** POLARIDAD INICIAL: {pol} ***')
        print(f'  Bit count: {bit_count}, Tail: {tail}T, p0: {p0}T, p1: {p1}T')
    
    print()
    offset += 8 + size
    block_num += 1

print(f'Total bloques PZX: {block_num}')
