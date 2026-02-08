#!/usr/bin/env python3
"""Verificar pause de bloques en Dan Dare 2"""
import os

def read_word(data, offset):
    return data[offset] | (data[offset+1] << 8)

def read_dword(data, offset):
    return data[offset] | (data[offset+1] << 8) | (data[offset+2] << 16) | (data[offset+3] << 24)

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")
with open(tzx_file, 'rb') as f:
    data = f.read()

pos = 10  # Skip header
block_num = 0

while pos < len(data):
    block_num += 1
    block_id = data[pos]
    print(f"\nBlock {block_num}: ID 0x{block_id:02X} @ offset {pos}")
    
    if block_id == 0x10:  # Standard Speed Data
        pos += 1
        pause = read_word(data, pos)
        pos += 2
        length = read_word(data, pos)
        pos += 2
        print(f"  Pause: {pause} ms, Length: {length} bytes")
        pos += length
        
    elif block_id == 0x19:  # GDB
        pos += 1
        block_len = read_dword(data, pos)
        pos += 4
        pause = read_word(data, pos)
        print(f"  Block length: {block_len}, Pause: {pause} ms")
        pos += block_len
        
    elif block_id == 0x32:  # Archive Info
        pos += 1
        block_len = read_word(data, pos)
        pos += 2
        print(f"  Archive info, length: {block_len}")
        pos += block_len
        
    elif block_id == 0x87:  # Custom block
        pos += 1
        block_len = read_dword(data, pos)
        pos += 4
        print(f"  Custom block, length: {block_len}")
        pos += block_len
        
    else:
        print(f"  Unknown block type")
        break

print(f"\nTotal blocks: {block_num}")
