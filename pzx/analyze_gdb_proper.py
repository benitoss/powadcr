#!/usr/bin/env python3
"""Proper GDB analysis with correct offsets"""
import struct
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")

with open(tzx_file, 'rb') as f:
    data = f.read()

# Find all GDB blocks
pos = 10  # After header
block_num = 0

while pos < len(data):
    block_id = data[pos]
    
    if block_id == 0x19:  # GDB
        block_num += 1
        print(f"\n{'='*60}")
        print(f"GDB Block {block_num} @ offset {pos}")
        print(f"{'='*60}")
        
        # Header (all relative to block start)
        block_len = struct.unpack_from('<I', data, pos+1)[0]
        pause = struct.unpack_from('<H', data, pos+5)[0]
        totp = struct.unpack_from('<I', data, pos+7)[0]
        npp = data[pos+11]
        asp = data[pos+12]
        totd = struct.unpack_from('<I', data, pos+13)[0]
        npd = data[pos+17]
        asd = data[pos+18]
        
        print(f"Block length: {block_len}")
        print(f"Pause after: {pause}ms")
        print(f"TOTP (pilot PRLE entries): {totp}")
        print(f"NPP (max pulses per pilot symbol): {npp}")
        print(f"ASP (number of pilot symbols): {asp}")
        print(f"TOTD (data PRLE entries): {totd}")
        print(f"NPD (max pulses per data symbol): {npd}")
        print(f"ASD (number of data symbols): {asd}")
        
        # Symbol definitions start at pos+19
        pilot_sym_start = pos + 19
        pilot_sym_size = 1 + npp * 2
        
        print(f"\nPILOT SYMBOL TABLE (size per sym: {pilot_sym_size} bytes):")
        for i in range(asp):
            sym_offset = pilot_sym_start + i * pilot_sym_size
            flags = data[sym_offset]
            durations = []
            for j in range(npp):
                dur = struct.unpack_from('<H', data, sym_offset + 1 + j*2)[0]
                durations.append(dur)
            
            non_zero = [d for d in durations if d > 0]
            dur_str = ', '.join([f"{d} ({d/3.5:.1f}us)" for d in non_zero])
            print(f"  Sym {i}: flags=0x{flags:02x}, durations=[{dur_str}] ({len(non_zero)} pulses)")
        
        # Data symbols
        data_sym_start = pilot_sym_start + asp * pilot_sym_size
        data_sym_size = 1 + npd * 2
        
        print(f"\nDATA SYMBOL TABLE (size per sym: {data_sym_size} bytes):")
        for i in range(asd):
            sym_offset = data_sym_start + i * data_sym_size
            flags = data[sym_offset]
            durations = []
            for j in range(npd):
                dur = struct.unpack_from('<H', data, sym_offset + 1 + j*2)[0]
                durations.append(dur)
            
            non_zero = [d for d in durations if d > 0]
            dur_str = ', '.join([f"{d} ({d/3.5:.1f}us)" for d in non_zero])
            print(f"  Sym {i}: flags=0x{flags:02x}, durations=[{dur_str}] ({len(non_zero)} pulses)")
        
        # PRLE starts after data symbols
        pilot_prle_start = data_sym_start + asd * data_sym_size
        
        print(f"\nPILOT PRLE @ offset {pilot_prle_start} ({totp} entries):")
        prle_pos = pilot_prle_start
        total_pilot_pulses = 0
        for i in range(min(totp, 20)):
            symbol = data[prle_pos]
            reps = struct.unpack_from('<H', data, prle_pos+1)[0]
            
            # Count pulses in this symbol
            sym_offset = pilot_sym_start + symbol * pilot_sym_size + 1
            pulses_count = sum(1 for j in range(npp) if struct.unpack_from('<H', data, sym_offset+j*2)[0] > 0)
            
            total_this = reps * pulses_count
            total_pilot_pulses += total_this
            
            print(f"  [{i}] Symbol {symbol} x {reps} = {total_this} pulses")
            prle_pos += 3
        
        # Data PRLE
        data_prle_start = pilot_prle_start + totp * 3
        
        print(f"\nDATA PRLE @ offset {data_prle_start} ({totd} entries):")
        prle_pos = data_prle_start
        total_data_pulses = 0
        for i in range(min(totd, 10)):
            symbol = data[prle_pos]
            reps = struct.unpack_from('<H', data, prle_pos+1)[0]
            
            # Count pulses in this symbol
            sym_offset = data_sym_start + symbol * data_sym_size + 1
            pulses_count = sum(1 for j in range(npd) if struct.unpack_from('<H', data, sym_offset+j*2)[0] > 0)
            
            total_this = reps * pulses_count
            total_data_pulses += total_this
            
            print(f"  [{i}] Symbol {symbol} x {reps} = {total_this} pulses")
            prle_pos += 3
        
        # Contar todas las entradas
        prle_pos = data_prle_start
        full_data_pulses = 0
        for i in range(totd):
            symbol = data[prle_pos]
            reps = struct.unpack_from('<H', data, prle_pos+1)[0]
            sym_offset = data_sym_start + symbol * data_sym_size + 1
            pulses_count = sum(1 for j in range(npd) if struct.unpack_from('<H', data, sym_offset+j*2)[0] > 0)
            full_data_pulses += reps * pulses_count
            prle_pos += 3
        
        print(f"\n=== TOTALS ===")
        print(f"Pilot pulses: {total_pilot_pulses}")
        print(f"Data pulses: {full_data_pulses}")
        print(f"GRAND TOTAL: {total_pilot_pulses + full_data_pulses}")
        parity = "IMPAR (ODD)" if (total_pilot_pulses + full_data_pulses) % 2 == 1 else "PAR (EVEN)"
        print(f"Parity: {parity}")
        
        pos += 1 + block_len
        
        if block_num >= 1:  # Solo primer GDB
            break
    
    elif block_id == 0x10:
        length = struct.unpack_from('<H', data, pos+3)[0]
        pos += 5 + length
    elif block_id == 0x11:
        length = struct.unpack_from('<I', data, pos+16)[0] & 0xFFFFFF
        pos += 19 + length
    elif block_id == 0x21:
        length = data[pos+1]
        pos += 2 + length
    elif block_id == 0x20:
        pos += 3
    else:
        print(f"Unknown block 0x{block_id:02x} @ {pos}")
        break
