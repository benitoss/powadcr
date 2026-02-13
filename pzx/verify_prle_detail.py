"""
Verificar detalles del PRLE y comparar con WAV
"""
import struct
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
tzx_file = os.path.join(script_dir, "Dan Dare 2 - Mekon's Revenge.tzx")

with open(tzx_file, 'rb') as f:
    f.seek(919)
    block_id = f.read(1)[0]
    print(f'Block ID: 0x{block_id:02X}')
    
    block_len = struct.unpack('<I', f.read(4))[0]
    pause = struct.unpack('<H', f.read(2))[0]
    TOTP = struct.unpack('<I', f.read(4))[0]
    NPP = f.read(1)[0]
    ASP = f.read(1)[0]
    TOTD = struct.unpack('<I', f.read(4))[0]
    NPD = f.read(1)[0]
    ASD = f.read(1)[0]
    
    print(f'TOTP={TOTP}, NPP={NPP}, ASP={ASP}')
    print(f'TOTD={TOTD}, NPD={NPD}, ASD={ASD}')
    
    # Read pilot SYMDEF (ASP symbols, each with NPP+1 words)
    print('\nPilot SYMDEF:')
    pilot_syms = []
    for i in range(ASP):
        flags = f.read(1)[0]
        pulses = []
        for j in range(NPP):
            dur = struct.unpack('<H', f.read(2))[0]
            pulses.append(dur)
        npulses = sum(1 for p in pulses if p > 0)
        pilot_syms.append((flags, pulses, npulses))
        dur_us = [p * 1000000 / 3500000 for p in pulses if p > 0]
        print(f'  Sym {i}: flags={flags}, T-states={pulses}, ~{dur_us}us, num={npulses}')
    
    # Read data SYMDEF (ASD symbols, each with NPD+1 words)
    print('\nData SYMDEF:')
    data_syms = []
    for i in range(ASD):
        flags = f.read(1)[0]
        pulses = []
        for j in range(NPD):
            dur = struct.unpack('<H', f.read(2))[0]
            pulses.append(dur)
        npulses = sum(1 for p in pulses if p > 0)
        data_syms.append((flags, pulses, npulses))
        dur_us = [p * 1000000 / 3500000 for p in pulses if p > 0]
        print(f'  Sym {i}: flags={flags}, T-states={pulses}, ~{dur_us}us, num={npulses}')
    
    # Read PRLE
    print('\nPRLE entries:')
    total_pilot_pulses = 0
    for i in range(TOTP):
        sym = f.read(1)[0]
        rep = struct.unpack('<H', f.read(2))[0]
        
        if sym < ASP and rep > 0:
            _, _, npulses = pilot_syms[sym]
            pulses_this = npulses * rep
            total_pilot_pulses += pulses_this
            status = f'{pulses_this} pulses'
        elif rep == 0:
            status = 'SKIPPED (rep=0)'
            pulses_this = 0
        else:
            status = f'INVALID (sym {sym} >= ASP {ASP})'
            pulses_this = 0
        
        print(f'  Entry {i}: sym={sym}, rep={rep} - {status}')
    
    print(f'\nTotal pilot pulses: {total_pilot_pulses}')
    
    # Data pulses - each data symbol has 2 pulses
    total_data_pulses = TOTD * 2  # Assuming all data symbols have 2 pulses
    print(f'Total data pulses: {total_data_pulses} (TOTD * 2)')
    print(f'TOTAL EXPECTED: {total_pilot_pulses + total_data_pulses}')
    
    # WAV block 4 has 152,638 pulses
    wav_pulses = 152638
    print(f'\nWAV Block 4: {wav_pulses} pulses')
    print(f'Difference: {wav_pulses - (total_pilot_pulses + total_data_pulses)}')
