#!/usr/bin/env python3
"""
Buscar patrones de repetición en bc_data_ko.txt que sugieran problemas de buffer
"""

import re
from collections import Counter

def parse_hex(path):
    with open(path, 'r') as f:
        content = f.read()
    hex_values = re.findall(r'0x([0-9a-fA-F]{2})', content)
    return bytes(int(h, 16) for h in hex_values)

ko = parse_hex('bc_data_ko.txt')

# Analizar solo la zona corrupta
start = 48506
corrupted = ko[start:]

print(f"Analyzing corrupted zone: bytes {start} to {len(ko)-1}")
print(f"Zone size: {len(corrupted)} bytes")
print()

# Buscar bytes más frecuentes
counter = Counter(corrupted)
print("Top 10 most frequent bytes in corrupted zone:")
for byte_val, count in counter.most_common(10):
    print(f"  0x{byte_val:02X}: {count} times ({count/len(corrupted)*100:.1f}%)")

print()

# Buscar patrones repetidos
print("Looking for repeated patterns...")
# Buscar secuencias de 2-8 bytes que se repitan
for pattern_len in [2, 3, 4]:
    pattern_counter = Counter()
    for i in range(len(corrupted) - pattern_len):
        pattern = corrupted[i:i+pattern_len]
        pattern_counter[pattern] += 1
    
    print(f"\nTop 5 repeated {pattern_len}-byte patterns:")
    for pattern, count in pattern_counter.most_common(5):
        if count > 2:
            print(f"  {' '.join(f'{b:02X}' for b in pattern)}: {count} times")

# Ver si hay una secuencia que se repite exactamente
print("\n\nLooking for exact repeating blocks...")
for block_size in [64, 128, 256, 512]:
    if len(corrupted) >= block_size * 2:
        block1 = corrupted[:block_size]
        # Buscar este bloque más adelante
        for offset in range(block_size, len(corrupted) - block_size + 1, block_size // 2):
            block2 = corrupted[offset:offset + block_size]
            matching = sum(1 for a, b in zip(block1, block2) if a == b)
            if matching > block_size * 0.8:  # >80% match
                print(f"  Block of {block_size} bytes at offset 0 matches block at offset {offset} ({matching}/{block_size} = {matching/block_size*100:.1f}%)")

# Verificar si los datos corruptos son parte del datastream correcto de otra posición
ok = parse_hex('bc_data_ok.txt')
print("\n\nChecking if corrupted data appears elsewhere in OK data...")
# Tomar los primeros 50 bytes de la zona corrupta y buscarlos en OK
search_chunk = corrupted[:20]
for i in range(len(ok) - 20):
    if ok[i:i+5] == search_chunk[:5]:  # Buscar coincidencia de 5 bytes
        match_len = 0
        for j in range(min(50, len(ok) - i, len(search_chunk))):
            if ok[i+j] == search_chunk[j]:
                match_len += 1
            else:
                break
        if match_len >= 5:
            print(f"  First bytes of corrupted zone (0x{search_chunk[0]:02X}...) found at OK position {i} with {match_len} consecutive matches")
