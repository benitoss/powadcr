#!/usr/bin/env python3
"""Análisis completo de Dan Dare 2 - todos los bloques"""
import os
import math

def read_word(data, offset):
    return data[offset] | (data[offset+1] << 8)

def read_dword(data, offset):
    return data[offset] | (data[offset+1] << 8) | (data[offset+2] << 16) | (data[offset+3] << 24)

def read_3bytes(data, offset):
    return data[offset] | (data[offset+1] << 8) | (data[offset+2] << 16)

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")
with open(tzx_file, 'rb') as f:
    data = f.read()

pos = 10  # Skip header
block_num = 0
gdb_count = 0

print("=" * 80)
print("DAN DARE 2 - ANÁLISIS COMPLETO DE TODOS LOS BLOQUES")
print("=" * 80)

while pos < len(data):
    block_num += 1
    block_id = data[pos]
    print(f"\nBloque {block_num}: ID 0x{block_id:02X} @ offset {pos}")
    
    try:
        if block_id == 0x10:  # Standard Speed Data
            pos += 1
            pause = read_word(data, pos)
            pos += 2
            length = read_word(data, pos)
            pos += 2
            flag = data[pos] if length > 0 else 0
            print(f"  Standard: Pause={pause}ms, Length={length} bytes, Flag={flag}")
            pos += length
            
        elif block_id == 0x11:  # Turbo Speed Data
            pos += 1
            pilot_len = read_word(data, pos)
            pos += 2
            sync1_len = read_word(data, pos)
            pos += 2
            sync2_len = read_word(data, pos)
            pos += 2
            zero_len = read_word(data, pos)
            pos += 2
            one_len = read_word(data, pos)
            pos += 2
            pilot_tone = read_word(data, pos)
            pos += 2
            last_byte = data[pos]
            pos += 1
            pause = read_word(data, pos)
            pos += 2
            length = read_3bytes(data, pos)
            pos += 3
            print(f"  Turbo: Pause={pause}ms, Length={length} bytes")
            pos += length
            
        elif block_id == 0x12:  # Pure Tone
            pos += 1
            pulse_len = read_word(data, pos)
            pos += 2
            pulses = read_word(data, pos)
            pos += 2
            print(f"  Pure Tone: {pulses} pulses of {pulse_len} T-states")
            
        elif block_id == 0x13:  # Pulse Sequence
            pos += 1
            num_pulses = data[pos]
            pos += 1
            print(f"  Pulse Sequence: {num_pulses} pulses")
            pos += num_pulses * 2
            
        elif block_id == 0x14:  # Pure Data
            pos += 1
            zero_len = read_word(data, pos)
            pos += 2
            one_len = read_word(data, pos)
            pos += 2
            last_byte = data[pos]
            pos += 1
            pause = read_word(data, pos)
            pos += 2
            length = read_3bytes(data, pos)
            pos += 3
            print(f"  Pure Data: Pause={pause}ms, Length={length} bytes")
            pos += length
            
        elif block_id == 0x19:  # GDB
            gdb_count += 1
            pos += 1
            block_len = read_dword(data, pos)
            pos += 4
            pause = read_word(data, pos)
            pos += 2
            
            TOTP = read_dword(data, pos)
            pos += 4
            NPP = data[pos]
            pos += 1
            ASP = data[pos]
            pos += 1
            TOTD = read_dword(data, pos)
            pos += 4
            NPD = data[pos]
            pos += 1
            ASD = data[pos]
            pos += 1
            
            print(f"  **GDB #{gdb_count}**: Pause={pause}ms, TOTP={TOTP}, NPP={NPP}, ASP={ASP}, TOTD={TOTD}, NPD={NPD}, ASD={ASD}")
            
            # Pilot/Sync symbols
            print(f"    PILOT/SYNC symbols ({ASP}), NPP={NPP}:")
            for i in range(ASP):
                flag = data[pos]
                pos += 1
                print(f"      Symbol[{i}]: flag=0x{flag:02X}, NPP={NPP} pulses", end="")
                pulses = []
                for j in range(NPP):
                    pulse = read_word(data, pos)
                    pos += 2
                    pulses.append(pulse)
                print(f" -> {pulses}")
            
            # PRLE
            print(f"    PRLE ({TOTP} entries):")
            for i in range(TOTP):
                symbol = data[pos]
                pos += 1
                repeat = read_word(data, pos)
                pos += 2
                if i < 10:  # Mostrar solo los primeros 10
                    print(f"      [{i}]: symbol={symbol}, repeat={repeat}")
            
            # Data symbols
            print(f"    DATA symbols ({ASD}), NPD={NPD}:")
            for i in range(ASD):
                flag = data[pos]
                pos += 1
                print(f"      Symbol[{i}]: flag=0x{flag:02X}, NPD={NPD} pulses", end="")
                pulses = []
                for j in range(NPD):
                    pulse = read_word(data, pos)
                    pos += 2
                    pulses.append(pulse)
                print(f" -> {pulses}")
            
            # Data stream - según TZX spec v1.20, no hay byte NB, se calcula
            # NB = bits needed per symbol = ceil(log2(ASD))
            # DS = bytes in data stream = ceil(NB * TOTD / 8)
            NB_calculated = math.ceil(math.log(ASD) / math.log(2)) if ASD > 1 else 1
            DS_calculated = math.ceil(NB_calculated * TOTD / 8)
            
            print(f"    Data stream: NB={NB_calculated} bits/symbol, DS={DS_calculated} bytes")
            
            # Leer los bytes del data stream
            data_stream = data[pos:pos+DS_calculated]
            pos += DS_calculated
            
        elif block_id == 0x20:  # Pause
            pos += 1
            pause = read_word(data, pos)
            pos += 2
            print(f"  Pause: {pause}ms")
            
        elif block_id == 0x21:  # Group Start
            pos += 1
            length = data[pos]
            pos += 1
            name = data[pos:pos+length].decode('ascii', errors='ignore')
            pos += length
            print(f"  Group Start: '{name}'")
            
        elif block_id == 0x22:  # Group End
            pos += 1
            print(f"  Group End")
            
        elif block_id == 0x24:  # Loop Start
            pos += 1
            repeats = read_word(data, pos)
            pos += 2
            print(f"  Loop Start: {repeats} repetitions")
            
        elif block_id == 0x25:  # Loop End
            pos += 1
            print(f"  Loop End")
            
        elif block_id == 0x30:  # Text Description
            pos += 1
            length = data[pos]
            pos += 1
            text = data[pos:pos+length].decode('ascii', errors='ignore')
            pos += length
            print(f"  Text: '{text}'")
            
        elif block_id == 0x32:  # Archive Info
            pos += 1
            block_len = read_word(data, pos)
            pos += 2
            print(f"  Archive Info: {block_len} bytes")
            pos += block_len
            
        elif block_id == 0x35:  # Custom Info
            pos += 1
            info_id = data[pos:pos+16]
            pos += 16
            length = read_dword(data, pos)
            pos += 4
            print(f"  Custom Info: {length} bytes")
            pos += length
            
        else:
            print(f"  UNKNOWN BLOCK TYPE - stopping analysis")
            break
            
    except Exception as e:
        print(f"  ERROR parsing block: {e}")
        break

print(f"\n{'=' * 80}")
print(f"TOTAL: {block_num} bloques, {gdb_count} bloques GDB")
print("=" * 80)
