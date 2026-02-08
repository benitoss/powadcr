import struct
import math

def analyze_tzx(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'=== {filename} ===')
    print(f'File size: {len(data)} bytes')
    
    offset = 10
    block_num = 0
    while offset < len(data):
        block_id = data[offset]
        block_num += 1
        
        if block_id == 0x19:  # GDB
            block_len = struct.unpack('<I', data[offset+1:offset+5])[0]
            pause = struct.unpack('<H', data[offset+5:offset+7])[0]
            TOTP = struct.unpack('<I', data[offset+7:offset+11])[0]
            NPP = data[offset+11]
            ASP = data[offset+12]
            TOTD = struct.unpack('<I', data[offset+13:offset+17])[0]
            NPD = data[offset+17]
            ASD = data[offset+18]
            
            print(f'\nBlock {block_num}: ID 0x19 (GDB) at offset {offset:#x}')
            print(f'  Block size: {block_len}')
            print(f'  Pause: {pause} ms')
            print(f'  TOTP={TOTP}, NPP={NPP}, ASP={ASP}')
            print(f'  TOTD={TOTD}, NPD={NPD}, ASD={ASD}')
            
            # Parse pilot/sync symbols
            pos = offset + 19
            print(f'\n  PILOT/SYNC SYMDEF ({ASP} symbols):')
            pilot_syms = []
            for s in range(ASP):
                flag = data[pos]
                pos += 1
                pulses = []
                for p in range(NPP):
                    pulse = struct.unpack('<H', data[pos:pos+2])[0]
                    pulses.append(pulse)
                    pos += 2
                pilot_syms.append((flag, pulses))
                print(f'    [{s}] Flag={flag}, Pulses={pulses}')
            
            # Parse PRLE
            print(f'\n  PRLE ({TOTP} entries):')
            for p in range(TOTP):
                symbol = data[pos]
                repeat = struct.unpack('<H', data[pos+1:pos+3])[0]
                pos += 3
                print(f'    [{p}] Symbol={symbol}, Repeat={repeat}')
            
            # Parse data symbols
            print(f'\n  DATA SYMDEF ({ASD} symbols):')
            data_syms = []
            for s in range(ASD):
                flag = data[pos]
                pos += 1
                pulses = []
                for p in range(NPD):
                    pulse = struct.unpack('<H', data[pos:pos+2])[0]
                    pulses.append(pulse)
                    pos += 2
                data_syms.append((flag, pulses))
                print(f'    [{s}] Flag={flag}, Pulses={pulses}')
            
            # Check symmetry
            if ASD == 2:
                sym0 = data_syms[0][1]
                sym1 = data_syms[1][1]
                is_sym0_symmetric = len(set(p for p in sym0 if p > 0)) <= 1
                is_sym1_symmetric = len(set(p for p in sym1 if p > 0)) <= 1
                print(f'\n  ANALYSIS:')
                print(f'    Symbol 0 symmetric: {is_sym0_symmetric} {sym0}')
                print(f'    Symbol 1 symmetric: {is_sym1_symmetric} {sym1}')
                if sym0[0] == sym1[0]:
                    print(f'    >>> ASYMMETRIC ENCODING (same first pulse)')
                else:
                    print(f'    >>> SYMMETRIC ENCODING (different first pulses)')
            
            offset += 5 + block_len
        elif block_id == 0x10:
            bl = struct.unpack('<H', data[offset+3:offset+5])[0]
            flag = data[offset+5] if bl > 0 else 0
            btype = 'Header' if flag == 0 else 'Data'
            print(f'Block {block_num}: ID 0x10 (Standard {btype}) len={bl}')
            offset += 5 + bl
        elif block_id == 0x11:
            bl = struct.unpack('<I', data[offset+16:offset+19] + b'\x00')[0]
            print(f'Block {block_num}: ID 0x11 (Turbo) len={bl}')
            offset += 19 + bl
        elif block_id == 0x30:
            tl = data[offset+1]
            offset += 2 + tl
        elif block_id == 0x32:
            bl = struct.unpack('<H', data[offset+1:offset+3])[0]
            offset += 3 + bl
        elif block_id == 0x35:
            bl = struct.unpack('<I', data[offset+17:offset+21])[0]
            offset += 21 + bl
        else:
            print(f'Block {block_num}: ID 0x{block_id:02X}')
            break
    print()

if __name__ == '__main__':
    analyze_tzx('ATF.tzx')
    print('='*60)
    analyze_tzx("BC's Quest for Tires.tzx")
