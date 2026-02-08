import struct
import sys

filename = "BC's Quest for Tires.tzx"

with open(filename, 'rb') as f:
    header = f.read(10)
    print(f'Header: {header[:7]}')
    print(f'Version: {header[8]}.{header[9]}')
    print()
    
    block_num = 0
    while True:
        id_byte = f.read(1)
        if not id_byte:
            break
        block_id = id_byte[0]
        block_num += 1
        pos = f.tell() - 1
        
        if block_id == 0x10:  # Standard speed data
            pause = struct.unpack('<H', f.read(2))[0]
            length = struct.unpack('<H', f.read(2))[0]
            data = f.read(length)
            flag = data[0] if length > 0 else 0
            block_type = 'Header' if flag == 0 else 'Data' if flag == 255 else f'Custom({flag})'
            print(f'Block {block_num}: ID 0x10 @ {pos} - {block_type}, len={length}, pause={pause}ms')
            if flag == 0 and length >= 18:
                name = data[2:12].decode('ascii', errors='replace').strip()
                print(f'         Name: "{name}"')
        elif block_id == 0x11:  # Turbo speed data
            pilot_pulse = struct.unpack('<H', f.read(2))[0]
            sync1 = struct.unpack('<H', f.read(2))[0]
            sync2 = struct.unpack('<H', f.read(2))[0]
            zero = struct.unpack('<H', f.read(2))[0]
            one = struct.unpack('<H', f.read(2))[0]
            pilot_len = struct.unpack('<H', f.read(2))[0]
            used_bits = f.read(1)[0]
            pause = struct.unpack('<H', f.read(2))[0]
            length = struct.unpack('<I', f.read(3) + b'\x00')[0]
            data = f.read(length)
            flag = data[0] if length > 0 else 0
            print(f'Block {block_num}: ID 0x11 @ {pos} - Turbo, len={length}, pause={pause}ms, pilot={pilot_pulse}T x{pilot_len}, bits_last={used_bits}')
            print(f'         zero={zero}T, one={one}T, sync1={sync1}T, sync2={sync2}T, flag=0x{flag:02X}')
        elif block_id == 0x12:  # Pure tone
            pulse_len = struct.unpack('<H', f.read(2))[0]
            pulses = struct.unpack('<H', f.read(2))[0]
            print(f'Block {block_num}: ID 0x12 @ {pos} - Pure Tone, {pulses} pulses x {pulse_len}T')
        elif block_id == 0x13:  # Pulse sequence
            count = f.read(1)[0]
            pulses = [struct.unpack('<H', f.read(2))[0] for _ in range(count)]
            print(f'Block {block_num}: ID 0x13 @ {pos} - Pulse Sequence, {count} pulses: {pulses}')
        elif block_id == 0x14:  # Pure data
            zero = struct.unpack('<H', f.read(2))[0]
            one = struct.unpack('<H', f.read(2))[0]
            used_bits = f.read(1)[0]
            pause = struct.unpack('<H', f.read(2))[0]
            length = struct.unpack('<I', f.read(3) + b'\x00')[0]
            f.read(length)
            print(f'Block {block_num}: ID 0x14 @ {pos} - Pure Data, len={length}, pause={pause}ms, zero={zero}T, one={one}T, bits_last={used_bits}')
        elif block_id == 0x15:  # Direct recording
            tpersample = struct.unpack('<H', f.read(2))[0]
            pause = struct.unpack('<H', f.read(2))[0]
            used_bits = f.read(1)[0]
            length = struct.unpack('<I', f.read(3) + b'\x00')[0]
            f.read(length)
            print(f'Block {block_num}: ID 0x15 @ {pos} - Direct Recording, len={length}, pause={pause}ms, T/sample={tpersample}')
        elif block_id == 0x19:  # Generalized Data Block
            block_len = struct.unpack('<I', f.read(4))[0]
            start_pos = f.tell()
            pause = struct.unpack('<H', f.read(2))[0]
            TOTP = struct.unpack('<I', f.read(4))[0]
            NPP = f.read(1)[0]
            ASP = f.read(1)[0]
            TOTD = struct.unpack('<I', f.read(4))[0]
            NPD = f.read(1)[0]
            ASD = f.read(1)[0]
            print(f'Block {block_num}: ID 0x19 @ {pos} - GDB, block_len={block_len}, pause={pause}ms')
            print(f'         TOTP={TOTP}, NPP={NPP}, ASP={ASP}')
            print(f'         TOTD={TOTD}, NPD={NPD}, ASD={ASD}')
            
            # Read pilot/sync symbol definitions
            if ASP > 0:
                print(f'         --- PILOT/SYNC SYMDEF ({ASP} symbols) ---')
                for s in range(ASP):
                    flag = f.read(1)[0]
                    pulses = [struct.unpack('<H', f.read(2))[0] for _ in range(NPP)]
                    print(f'         SYMDEF[{s}]: Flag={flag}, Pulses={pulses}')
            
            # Read pilot/sync stream (PRLE)
            if TOTP > 0:
                print(f'         --- PILOT/SYNC PRLE ({TOTP} entries) ---')
                for p in range(min(TOTP, 10)):  # Show first 10
                    symbol = f.read(1)[0]
                    repeat = struct.unpack('<H', f.read(2))[0]
                    print(f'         PRLE[{p}]: Symbol={symbol}, Repeat={repeat}')
                if TOTP > 10:
                    # Skip remaining
                    f.read((TOTP - 10) * 3)
                    print(f'         ... ({TOTP - 10} more entries)')
            
            # Read data symbol definitions
            if ASD > 0:
                print(f'         --- DATA SYMDEF ({ASD} symbols) ---')
                for s in range(ASD):
                    flag = f.read(1)[0]
                    pulses = [struct.unpack('<H', f.read(2))[0] for _ in range(NPD)]
                    print(f'         SYMDEF[{s}]: Flag={flag}, Pulses={pulses}')
            
            # Calculate data stream size
            import math
            if ASD > 0:
                NB = math.ceil(math.log(ASD) / math.log(2)) if ASD > 1 else 1
                DS = math.ceil(NB * TOTD / 8)
                print(f'         Data stream: NB={NB} bits/symbol, DS={DS} bytes')
            
            # Skip to end of block
            f.seek(start_pos + block_len - 4)  # -4 because block_len doesn't include the length field itself
            
        elif block_id == 0x20:  # Pause
            pause = struct.unpack('<H', f.read(2))[0]
            print(f'Block {block_num}: ID 0x20 @ {pos} - Pause {pause}ms')
        elif block_id == 0x21:  # Group start
            length = f.read(1)[0]
            name = f.read(length).decode('ascii', errors='replace')
            print(f'Block {block_num}: ID 0x21 @ {pos} - Group Start: "{name}"')
        elif block_id == 0x22:  # Group end
            print(f'Block {block_num}: ID 0x22 @ {pos} - Group End')
        elif block_id == 0x30:  # Text description
            length = f.read(1)[0]
            text = f.read(length).decode('ascii', errors='replace')
            print(f'Block {block_num}: ID 0x30 @ {pos} - Text: "{text}"')
        elif block_id == 0x32:  # Archive info
            length = struct.unpack('<H', f.read(2))[0]
            f.read(length)
            print(f'Block {block_num}: ID 0x32 @ {pos} - Archive Info')
        elif block_id == 0x33:  # Hardware type
            count = f.read(1)[0]
            f.read(count * 3)
            print(f'Block {block_num}: ID 0x33 @ {pos} - Hardware Type')
        elif block_id == 0x35:  # Custom info
            id_str = f.read(16).decode('ascii', errors='replace').strip()
            length = struct.unpack('<I', f.read(4))[0]
            f.read(length)
            print(f'Block {block_num}: ID 0x35 @ {pos} - Custom Info: "{id_str}"')
        else:
            print(f'Block {block_num}: ID 0x{block_id:02X} @ {pos} - Unknown/Other')
            # Try to skip unknown blocks by reading their length
            # Many TZX blocks have a 4-byte length after the ID
            try:
                # Read next 4 bytes as potential length
                length_bytes = f.read(4)
                if len(length_bytes) == 4:
                    potential_len = struct.unpack('<I', length_bytes)[0]
                    if potential_len < 1000000:  # Sanity check
                        print(f'         Potential length: {potential_len}')
                        # Show first few bytes
                        peek = f.read(min(20, potential_len))
                        print(f'         First bytes: {peek.hex()}')
                        f.seek(f.tell() - len(peek) + potential_len - 4)
                    else:
                        f.seek(f.tell() - 4)
            except:
                pass
    
    print(f'\nTotal blocks: {block_num}')
