#!/usr/bin/env python3
"""
Compare two hex byte streams to find where they diverge.
"""

def parse_hex_file(filename):
    """Parse a file containing comma-separated hex bytes."""
    with open(filename, 'r') as f:
        content = f.read()
    
    # Split by comma and parse each hex value
    bytes_list = []
    for item in content.split(','):
        item = item.strip()
        if item.startswith('0x'):
            try:
                bytes_list.append(int(item, 16))
            except ValueError:
                pass
    return bytes_list

def compare_streams(file_ok, file_ko):
    """Compare two byte streams and find divergence point."""
    bytes_ok = parse_hex_file(file_ok)
    bytes_ko = parse_hex_file(file_ko)
    
    print(f"File OK: {len(bytes_ok)} bytes")
    print(f"File KO: {len(bytes_ko)} bytes")
    print()
    
    # Find first divergence
    min_len = min(len(bytes_ok), len(bytes_ko))
    first_diff = -1
    
    for i in range(min_len):
        if bytes_ok[i] != bytes_ko[i]:
            first_diff = i
            break
    
    if first_diff == -1 and len(bytes_ok) == len(bytes_ko):
        print("Files are identical!")
        return
    elif first_diff == -1:
        first_diff = min_len
        print(f"Files match for first {min_len} bytes, but have different lengths")
    else:
        print(f"First difference at byte index {first_diff} (0x{first_diff:04X})")
        print()
        
        # Show context around the difference
        start = max(0, first_diff - 10)
        end = min(min_len, first_diff + 20)
        
        print(f"Context (bytes {start} to {end-1}):")
        print("-" * 80)
        print(f"{'Index':<8} {'OK':>6} {'KO':>6} {'Diff':>6}")
        print("-" * 80)
        
        for i in range(start, end):
            ok_val = bytes_ok[i] if i < len(bytes_ok) else None
            ko_val = bytes_ko[i] if i < len(bytes_ko) else None
            
            ok_str = f"0x{ok_val:02X}" if ok_val is not None else "N/A"
            ko_str = f"0x{ko_val:02X}" if ko_val is not None else "N/A"
            
            marker = " ***" if ok_val != ko_val else ""
            print(f"{i:<8} {ok_str:>6} {ko_str:>6}{marker}")
    
    # Count total differences
    diff_count = 0
    for i in range(min_len):
        if bytes_ok[i] != bytes_ko[i]:
            diff_count += 1
    
    print()
    print(f"Total differences in overlapping range: {diff_count}")
    
    # Show first 10 differences
    if diff_count > 0:
        print()
        print("First 10 differences:")
        print("-" * 80)
        count = 0
        for i in range(min_len):
            if bytes_ok[i] != bytes_ko[i]:
                print(f"  Byte {i} (0x{i:04X}): OK=0x{bytes_ok[i]:02X}, KO=0x{bytes_ko[i]:02X}")
                count += 1
                if count >= 10:
                    break
    
    # Analyze pattern of differences
    if diff_count > 0 and first_diff >= 0:
        print()
        print("Analyzing difference pattern...")
        
        # Check if it's a bit shift or inversion
        bit_errors = []
        for i in range(first_diff, min(first_diff + 50, min_len)):
            if bytes_ok[i] != bytes_ko[i]:
                xor = bytes_ok[i] ^ bytes_ko[i]
                bit_errors.append((i, bytes_ok[i], bytes_ko[i], xor))
        
        if bit_errors:
            print("\nXOR analysis (first differences):")
            for idx, ok, ko, xor in bit_errors[:10]:
                print(f"  Byte {idx}: OK={ok:08b} KO={ko:08b} XOR={xor:08b}")
            
            # Check for bit shift pattern
            print("\nChecking for bit shift pattern:")
            shifts_match = 0
            for i in range(first_diff, min(first_diff + 20, min_len)):
                if i + 1 < len(bytes_ko):
                    # Check if KO[i] matches OK[i] shifted
                    ok_val = bytes_ok[i]
                    ko_val = bytes_ko[i]
                    # Left shift by 1
                    if ((ok_val << 1) & 0xFF) == ko_val or ((ok_val >> 1) & 0xFF) == ko_val:
                        shifts_match += 1
            print(f"  Bytes matching 1-bit shift: {shifts_match}/20")

if __name__ == '__main__':
    import sys
    import os
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_ok = os.path.join(script_dir, 'bc_data_ok.txt')
    file_ko = os.path.join(script_dir, 'bc_data_ko.txt')
    
    compare_streams(file_ok, file_ko)
