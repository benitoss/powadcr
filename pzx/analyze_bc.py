import struct
import math

with open("BC's Quest for Tires.tzx", 'rb') as f:
    data = f.read()

# Buscar bloque 0x19 (GDB)
offset = 10
while offset < len(data):
    block_id = data[offset]
    if block_id == 0x19:
        # GDB encontrado
        block_len = struct.unpack('<I', data[offset+1:offset+5])[0]
        pause = struct.unpack('<H', data[offset+5:offset+7])[0]
        
        # Pilot/Sync definitions
        TOTP = struct.unpack('<I', data[offset+7:offset+11])[0]
        NPP = data[offset+11]
        ASP = data[offset+12]
        
        # Data definitions  
        TOTD = struct.unpack('<I', data[offset+13:offset+17])[0]
        NPD = data[offset+17]
        ASD = data[offset+18]
        
        print('=== BC Quest GDB Details ===')
        print(f'Pause: {pause} ms')
        print(f'Pilot/Sync: TOTP={TOTP}, NPP={NPP}, ASP={ASP}')
        print(f'Data: TOTD={TOTD}, NPD={NPD}, ASD={ASD}')
        
        # Parse SYMDEF for Pilot/Sync
        pos = offset + 19
        print('\n--- Pilot/Sync SYMDEF ---')
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
            flag_meaning = ['Change edge', 'Keep edge', 'Force LOW', 'Force HIGH'][flag & 3]
            print(f'  Symbol {s}: Flag={flag} ({flag_meaning}), Pulses={pulses}')
        
        # Parse PRLE for Pilot/Sync
        print('\n--- Pilot/Sync PRLE ---')
        pilot_prle = []
        for p in range(TOTP):
            symbol = data[pos]
            repeat = struct.unpack('<H', data[pos+1:pos+3])[0]
            pos += 3
            pilot_prle.append((symbol, repeat))
            print(f'  Entry {p}: Symbol={symbol}, Repeat={repeat}')
        
        # Parse SYMDEF for Data
        print('\n--- Data SYMDEF ---')
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
            flag_meaning = ['Change edge', 'Keep edge', 'Force LOW', 'Force HIGH'][flag & 3]
            print(f'  Symbol {s}: Flag={flag} ({flag_meaning}), Pulses={pulses}')
        
        # Calcular NB y DS
        NB = math.ceil(math.log(ASD) / math.log(2))
        DS = math.ceil(NB * TOTD / 8)
        print(f'\nNB (bits per symbol) = {NB}')
        print(f'DS (bytes in datastream) = {DS}')
        
        # First bytes
        print(f'\nFirst 16 bytes of datastream (hex):')
        print('  ', end='')
        for i in range(16):
            print(f'{data[pos+i]:02X} ', end='')
        print()
        
        # Analysis of timing
        print('\n=== Timing Analysis ===')
        
        # Total pilot/sync time
        pilot_time = 0
        for sym_id, repeat in pilot_prle:
            flag, pulses = pilot_syms[sym_id]
            for pulse in pulses:
                if pulse > 0:
                    pilot_time += pulse * repeat
        print(f'Pilot/Sync total T-states: {pilot_time}')
        print(f'Pilot/Sync duration: {pilot_time / 3500000 * 1000:.2f} ms')
        
        # Data time (approximate based on distribution)
        # Assume 50% zeros, 50% ones
        sym0_time = sum(p for p in data_syms[0][1] if p > 0)
        sym1_time = sum(p for p in data_syms[1][1] if p > 0)
        avg_time = (sym0_time + sym1_time) / 2
        data_time = avg_time * TOTD
        print(f'\nData Symbol 0 total time: {sym0_time} T-states')
        print(f'Data Symbol 1 total time: {sym1_time} T-states')
        print(f'Average symbol time: {avg_time} T-states')
        print(f'Estimated data duration: {data_time / 3500000:.2f} seconds')
        
        # Key insight
        print('\n=== Key Observation ===')
        print(f'Symbol 0: {data_syms[0][1]} - First pulse: {data_syms[0][1][0]}')
        print(f'Symbol 1: {data_syms[1][1]} - First pulse: {data_syms[1][1][0]}')
        
        if data_syms[0][1][0] == data_syms[1][1][0]:
            print('>>> ASYMMETRIC ENCODING: First pulses are IDENTICAL!')
            print('>>> Loader distinguishes bits by measuring SECOND pulse length')
            print(f'    Bit 0: second pulse = {data_syms[0][1][1]} T-states')
            print(f'    Bit 1: second pulse = {data_syms[1][1][1]} T-states')
            print(f'    Ratio: {data_syms[1][1][1] / data_syms[0][1][1]:.2f}x')
        else:
            print('>>> SYMMETRIC ENCODING: First pulses differ')
        
        break
    else:
        if block_id == 0x10:
            offset += 5 + struct.unpack('<H', data[offset+3:offset+5])[0]
        elif block_id == 0x11:
            bl = struct.unpack('<I', data[offset+1:offset+4] + b'\x00')[0]
            offset += 19 + bl
        elif block_id == 0x12:
            offset += 5
        elif block_id == 0x13:
            offset += 2 + data[offset+1] * 2
        elif block_id == 0x14:
            bl = struct.unpack('<I', data[offset+8:offset+11] + b'\x00')[0]
            offset += 11 + bl
        elif block_id == 0x15:
            bl = struct.unpack('<I', data[offset+6:offset+9] + b'\x00')[0]
            offset += 9 + bl
        elif block_id == 0x19:
            offset += 5 + struct.unpack('<I', data[offset+1:offset+5])[0]
        elif block_id == 0x20:
            offset += 3
        elif block_id == 0x21:
            offset += 2 + data[offset+1]
        elif block_id == 0x22:
            offset += 1
        elif block_id == 0x30:
            offset += 2 + data[offset+1]
        elif block_id == 0x32:
            offset += 3 + struct.unpack('<H', data[offset+1:offset+3])[0]
        elif block_id == 0x33:
            offset += 2 + data[offset+1] * 3
        elif block_id == 0x35:
            offset += 21 + struct.unpack('<I', data[offset+17:offset+21])[0]
        elif block_id == 0x5A:
            offset += 10
        else:
            print(f'Unknown block 0x{block_id:02X} at offset {offset}')
            break
