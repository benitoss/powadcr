#!/usr/bin/env python3
"""Analiza en detalle el pilot stream del bloque GDB de Book of the Dead"""

import struct
import os

def analyze_gdb_detailed(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Buscar el bloque GDB (ID 0x19)
    pos = 10  # Después de la cabecera TZX
    
    while pos < len(data):
        block_id = data[pos]
        
        if block_id == 0x19:  # GDB
            print(f"Encontrado bloque GDB @ offset 0x{pos:06X}")
            
            length = struct.unpack('<I', data[pos+1:pos+5])[0]
            gdb_offset = pos + 5
            
            pause = struct.unpack('<H', data[gdb_offset:gdb_offset+2])[0]
            totp = struct.unpack('<I', data[gdb_offset+2:gdb_offset+6])[0]
            npp = data[gdb_offset+6]
            asp = data[gdb_offset+7]
            totd = struct.unpack('<I', data[gdb_offset+8:gdb_offset+12])[0]
            npd = data[gdb_offset+12]
            asd = data[gdb_offset+13]
            
            print(f"\n=== PARÁMETROS GDB ===")
            print(f"TOTP: {totp} (entradas en pilot stream)")
            print(f"NPP: {npp} (max pulsos por símbolo pilot)")
            print(f"ASP: {asp} (definiciones de símbolo pilot)")
            print(f"TOTD: {totd}")
            print(f"NPD: {npd}")
            print(f"ASD: {asd}")
            
            # Leer definiciones de símbolos pilot/sync
            symdef_offset = gdb_offset + 14
            print(f"\n=== SYMBOL DEFINITIONS (pilot/sync) ===")
            
            symbol_defs = []
            for s in range(asp):
                flags = data[symdef_offset]
                pulses = []
                for p in range(npp):
                    pulse_len = struct.unpack('<H', data[symdef_offset+1+p*2:symdef_offset+3+p*2])[0]
                    pulses.append(pulse_len)
                symbol_defs.append({'flags': flags, 'pulses': pulses})
                print(f"  Symbol {s}: flags=0x{flags:02X}, pulses={pulses}")
                symdef_offset += 1 + npp * 2
            
            # Leer pilot stream
            print(f"\n=== PILOT STREAM (TOTP={totp} entradas) ===")
            pilot_stream = []
            
            for i in range(totp):
                symbol = data[symdef_offset]
                repeat = struct.unpack('<H', data[symdef_offset+1:symdef_offset+3])[0]
                pilot_stream.append({'symbol': symbol, 'repeat': repeat})
                print(f"  Entry {i}: symbol={symbol}, repeat={repeat}")
                symdef_offset += 3
            
            # Calcular total de pulsos
            print(f"\n=== ANÁLISIS DE PULSOS ===")
            total_pulses = 0
            level = 'LOW'  # Nivel inicial típico
            
            print(f"Nivel inicial: {level}")
            print()
            
            for entry in pilot_stream:
                sym_id = entry['symbol']
                rep = entry['repeat']
                sym_def = symbol_defs[sym_id]
                
                # Contar pulsos no-cero en este símbolo
                non_zero_pulses = [p for p in sym_def['pulses'] if p > 0]
                pulses_per_symbol = len(non_zero_pulses)
                
                # Total pulsos = pulsos_por_símbolo * repeticiones
                entry_pulses = pulses_per_symbol * rep
                total_pulses += entry_pulses
                
                print(f"Symbol {sym_id} x {rep}:")
                print(f"  Pulsos por símbolo: {pulses_per_symbol} ({non_zero_pulses})")
                print(f"  Total pulsos esta entrada: {entry_pulses}")
                
                # Simular el nivel después de esta entrada
                for _ in range(rep):
                    for p in non_zero_pulses:
                        level = 'HIGH' if level == 'LOW' else 'LOW'
                
                print(f"  Nivel después: {level}")
                print()
            
            print(f"=== RESUMEN ===")
            print(f"Total pulsos pilot+sync: {total_pulses}")
            print(f"Nivel final después de pilot+sync: {level}")
            
            if total_pulses % 2 == 0:
                print(f"\n⚠️  Número PAR de pulsos ({total_pulses})")
                print(f"   Si empezamos en LOW, terminamos en LOW")
                print(f"   El primer pulso de DATA empezará en HIGH (con polarity=0)")
            else:
                print(f"\n⚠️  Número IMPAR de pulsos ({total_pulses})")
                print(f"   Si empezamos en LOW, terminamos en HIGH")
                print(f"   El primer pulso de DATA empezará en LOW (con polarity=0)")
            
            break
        
        # Saltar al siguiente bloque
        if block_id == 0x10:
            length = struct.unpack('<H', data[pos+3:pos+5])[0]
            pos += 5 + length
        elif block_id == 0x19:
            length = struct.unpack('<I', data[pos+1:pos+5])[0]
            pos += 5 + length
        elif block_id == 0x32:
            length = struct.unpack('<H', data[pos+1:pos+3])[0]
            pos += 3 + length
        else:
            # Intentar parsear como bloque genérico
            print(f"Bloque 0x{block_id:02X} @ 0x{pos:06X} - saltando")
            pos += 1  # Mover al menos 1 byte

if __name__ == '__main__':
    filepath = r"pzxsamples\gdb\Book Of The Dead - Part 1 (CRL).tzx"
    if os.path.exists(filepath):
        analyze_gdb_detailed(filepath)
    else:
        print(f"No se encuentra: {filepath}")
