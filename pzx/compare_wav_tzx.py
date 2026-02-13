#!/usr/bin/env python3
"""Comparar WAV vs TZX para el bloque 6 de Dan Dare 2"""
import struct
import wave

# Leer TZX
tzx_path = "Dan Dare 2 - Mekon's Revenge.tzx"
with open(tzx_path, 'rb') as f:
    tzx_data = f.read()

# Bloque 6 @ offset 10434
offset = 10434
print(f'=== TZX BLOQUE 6 ===')
print(f'Byte en offset {offset}: 0x{tzx_data[offset]:02X}')

blockLen = struct.unpack('<I', tzx_data[offset+1:offset+5])[0]
pause = struct.unpack('<H', tzx_data[offset+5:offset+7])[0]
TOTP = struct.unpack('<I', tzx_data[offset+7:offset+11])[0]
NPP = tzx_data[offset+11]
ASP = tzx_data[offset+12]
TOTD = struct.unpack('<I', tzx_data[offset+13:offset+17])[0]
NPD = tzx_data[offset+17]
ASD = tzx_data[offset+18]

print(f'blockLen={blockLen}, pause={pause}ms')
print(f'TOTP={TOTP}, NPP={NPP}, ASP={ASP}')
print(f'TOTD={TOTD}, NPD={NPD}, ASD={ASD}')

symdef_offset = offset + 19
print('\n--- PILOT SYMBOLS ---')
for i in range(ASP):
    sym_offset = symdef_offset + i * (1 + NPP * 2)
    flags = tzx_data[sym_offset]
    pulses = []
    for p in range(NPP):
        pulse = struct.unpack('<H', tzx_data[sym_offset+1+p*2:sym_offset+3+p*2])[0]
        pulses.append(pulse)
    active = len([p for p in pulses if p != 0])
    us_values = [p/3.5 for p in pulses]
    print(f'Sym {i}: flag={flags}, T={pulses}, us=[{us_values[0]:.1f}, {us_values[1]:.1f}] -> {active} pulso(s)')

# Leer WAV
print('\n=== WAV BLOQUE 6 ===')
wav_path = 'pzxsamples/gdb/Dan Dare 2.wav'
with wave.open(wav_path, 'rb') as wav:
    sr = wav.getframerate()
    wav_data = wav.readframes(wav.getnframes())

samples = [wav_data[i] - 128 for i in range(len(wav_data))]

# Detectar pulsos
threshold = 0
pulses = []
current_level = 1 if samples[0] > threshold else 0
pulse_start = 0

for i, s in enumerate(samples):
    level = 1 if s > threshold else 0
    if level != current_level:
        duration_samples = i - pulse_start
        duration_us = (duration_samples / sr) * 1000000
        pulses.append((pulse_start, duration_us, 'H' if current_level == 1 else 'L'))
        pulse_start = i
        current_level = level

# El bloque 6 está entre el silencio de 6972ms y el de 1761ms
block6_start = None
block6_end = None
for i, (start, dur, level) in enumerate(pulses):
    if dur > 6900000 and dur < 7100000:
        block6_start = i + 1
    if dur > 1700000 and dur < 1850000:
        block6_end = i

if block6_start and block6_end:
    block6_pulses = pulses[block6_start:block6_end]
    print(f'Total pulsos en bloque 6: {len(block6_pulses)}')
    
    print('\nPrimeros 20 pulsos:')
    for i, (start, dur, level) in enumerate(block6_pulses[:20]):
        t_states = dur * 3.5
        print(f'  {i}: {dur:.1f}us ({t_states:.0f}T) {level}')

print('\n=== COMPARACIÓN ===')
print('TZX Symbol 0: [2168, 0] = 1 semi-pulso de 619us')
print('WAV muestra: pares de ~615us H + ~625us L')
print('')
print('El WAV tiene pulsos COMPLETOS (onda cuadrada)')
print('El TZX define solo semi-pulsos')
print('')
print('Esto significa que el Symbol 0 con [2168, 0] debería')
print('generar UN pulso de 619us, y luego alternar automáticamente')
print('para el siguiente pulso de 619us.')
