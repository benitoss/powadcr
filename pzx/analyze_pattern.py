#!/usr/bin/env python3
"""
Análisis profundo del patrón de error
"""

import re

def parse_hex(path):
    with open(path, 'r') as f:
        content = f.read()
    hex_values = re.findall(r'0x([0-9a-fA-F]{2})', content)
    return bytes(int(h, 16) for h in hex_values)

ok = parse_hex('bc_data_ok.txt')
ko = parse_hex('bc_data_ko.txt')

print("=" * 70)
print("Byte-by-byte comparison from first error")
print("=" * 70)

first_diff = 48506
end_range = min(first_diff + 50, len(ok))

print(f"{'Idx':>6} | {'OK':>4} | {'KO':>4} | {'Match':^5} | OK binary   | KO binary")
print("-" * 70)

consecutive_matches = 0
match_positions = []
diff_positions = []

for i in range(first_diff, end_range):
    ok_byte = ok[i]
    ko_byte = ko[i]
    match = "YES" if ok_byte == ko_byte else "NO"
    
    if ok_byte == ko_byte:
        consecutive_matches += 1
        match_positions.append(i - first_diff)
    else:
        consecutive_matches = 0
        diff_positions.append(i - first_diff)
    
    print(f"{i:>6} | 0x{ok_byte:02X} | 0x{ko_byte:02X} | {match:^5} | {ok_byte:08b} | {ko_byte:08b}")

print("\n" + "=" * 70)
print("Pattern analysis")
print("=" * 70)

# Contar cuántos bytes coinciden vs no coinciden en la zona de error
total_in_error_zone = len(ok) - first_diff
matches_in_error_zone = sum(1 for i in range(first_diff, len(ok)) if ok[i] == ko[i])
print(f"Bytes in error zone: {total_in_error_zone}")
print(f"Matching bytes in error zone: {matches_in_error_zone}")
print(f"Percentage matching in error zone: {matches_in_error_zone/total_in_error_zone*100:.2f}%")

# Buscar patrones de repetición
print(f"\n-- Matching positions (relative to first error) --")
print(f"Match positions (first 20): {match_positions[:20]}")

# Ver si hay bytes que aparecen bien pero fuera de lugar (shifted)
print(f"\n-- Looking for shifted data --")
# Buscar los bytes OK en KO con offset
for offset in range(-5, 6):
    if offset == 0:
        continue
    matches_with_offset = 0
    for i in range(first_diff, min(first_diff + 100, len(ok))):
        ko_idx = i + offset
        if 0 <= ko_idx < len(ko):
            if ok[i] == ko[ko_idx]:
                matches_with_offset += 1
    print(f"  Offset {offset:+d}: {matches_with_offset} matches out of 100")

# Verificar si los bytes incorrectos tienen algún patrón
print(f"\n-- XOR pattern for first 20 errors --")
error_count = 0
for i in range(first_diff, len(ok)):
    if ok[i] != ko[i] and error_count < 20:
        xor = ok[i] ^ ko[i]
        print(f"  Byte {i}: OK=0x{ok[i]:02X} XOR KO=0x{ko[i]:02X} = 0x{xor:02X} ({xor:08b})")
        error_count += 1
