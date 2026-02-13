#!/usr/bin/env python3
"""
Análisis detallado de las diferencias entre bc_data_ok.txt y bc_data_ko.txt
"""

import re

def parse_hex(path):
    with open(path, 'r') as f:
        content = f.read()
    hex_values = re.findall(r'0x([0-9a-fA-F]{2})', content)
    return bytes(int(h, 16) for h in hex_values)

ok = parse_hex('bc_data_ok.txt')
ko = parse_hex('bc_data_ko.txt')

print(f'OK length: {len(ok)}')
print(f'KO length: {len(ko)}')

# Encontrar primera diferencia
first_diff = None
for i in range(min(len(ok), len(ko))):
    if ok[i] != ko[i]:
        first_diff = i
        print(f'\nFirst diff at byte {i}')
        # Mostrar contexto
        start = max(0, i - 5)
        end = min(len(ok), i + 10)
        print(f'OK bytes [{start}:{end}]: {" ".join(f"{b:02X}" for b in ok[start:end])}')
        print(f'KO bytes [{start}:{end}]: {" ".join(f"{b:02X}" for b in ko[start:end])}')
        
        print(f'\n-- Bit analysis --')
        print(f'OK[{i}] = 0x{ok[i]:02X} = {ok[i]:08b}')
        print(f'KO[{i}] = 0x{ko[i]:02X} = {ko[i]:08b}')
        
        # Ver si hay un bit perdido
        xor = ok[i] ^ ko[i]
        print(f'XOR = 0x{xor:02X} = {xor:08b}')
        print(f'Bits different: {bin(xor).count("1")}')
        
        break

# Mostrar últimos bytes
print(f'\nLast 20 bytes of OK: {" ".join(f"{b:02X}" for b in ok[-20:])}')
print(f'Last 20 bytes of KO: {" ".join(f"{b:02X}" for b in ko[-20:])}')

# Verificar si KO está "shifted" respecto a OK
if first_diff:
    print(f'\n-- Checking bit shift hypothesis --')
    # Si se perdió un bit, KO desde ese punto estaría desplazado 1 bit a la izquierda
    # OK[i] debería ser igual a (KO[i] >> 1) | (KO[i+1] << 7)
    
    # Verificar desplazamiento
    print('\nComparing next bytes to check for bit shift:')
    for j in range(first_diff, min(first_diff + 5, len(ok) - 1)):
        # Si se perdió un bit, todo está shifted 1 bit
        # El byte j de KO debería ser aprox byte j de OK << 1 | bit de byte j+1
        reconstructed = ((ko[j] << 1) | (ko[j+1] >> 7)) & 0xFF
        print(f'  Byte {j}: OK=0x{ok[j]:02X} ({ok[j]:08b}), KO=0x{ko[j]:02X} ({ko[j]:08b}), KO<<1|next>>7=0x{reconstructed:02X} ({reconstructed:08b})')

# Contar diferencias totales y patrón
print(f'\n-- Error pattern analysis --')
total_diff = 0
for i in range(min(len(ok), len(ko))):
    if ok[i] != ko[i]:
        total_diff += 1

print(f'Total different bytes: {total_diff}')
if first_diff:
    print(f'Percentage correct: {(first_diff / len(ok)) * 100:.2f}%')
