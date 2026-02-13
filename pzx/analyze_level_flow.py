#!/usr/bin/env python3
"""
Análisis detallado del flujo de niveles entre bloques TZX
Simula exactamente cómo debería comportarse el código según la especificación
"""

# Simulación del estado global
EDGE_EAR_IS = "down"  # Estado inicial

def get_channel_amplitude(change_next_edge):
    """Simula getChannelAmplitude() de ZXProcessor.h"""
    global EDGE_EAR_IS
    
    if EDGE_EAR_IS == "down":
        if change_next_edge:
            # Devuelve HIGH y alterna a up
            EDGE_EAR_IS = "up"
            return "HIGH"
        else:
            return "LOW"
    else:  # up
        if change_next_edge:
            # Devuelve LOW y alterna a down
            EDGE_EAR_IS = "down"
            return "LOW"
        else:
            return "HIGH"

def pilot_tone(num_pulses, block_name):
    """Simula pilotTone()"""
    global EDGE_EAR_IS
    print(f"\n  {block_name} - pilotTone({num_pulses} pulses)")
    print(f"    Nivel inicial: EDGE_EAR_IS = {EDGE_EAR_IS}")
    
    first_level = None
    last_level = None
    
    for i in range(num_pulses):
        level = get_channel_amplitude(True)  # Siempre changeNextEARedge=true
        if i == 0:
            first_level = level
        last_level = level
        if i < 3 or i >= num_pulses - 3:
            print(f"    Pulso {i}: {level}")
        elif i == 3:
            print(f"    ... ({num_pulses - 6} pulsos intermedios) ...")
    
    print(f"    Primer pulso: {first_level}, Último pulso: {last_level}")
    print(f"    Nivel final: EDGE_EAR_IS = {EDGE_EAR_IS}")
    return first_level, last_level

def sync_tone(name):
    """Simula syncTone()"""
    global EDGE_EAR_IS
    level = get_channel_amplitude(True)
    print(f"    {name}: {level}, EDGE_EAR_IS = {EDGE_EAR_IS}")
    return level

def silence(duration_ms, block_name):
    """Simula silence() con changeNextEARedge=true por defecto"""
    global EDGE_EAR_IS
    print(f"\n  {block_name} - silence({duration_ms}ms)")
    print(f"    Nivel antes del silencio: EDGE_EAR_IS = {EDGE_EAR_IS}")
    
    if duration_ms > 0:
        # pulseSilence() llama a getChannelAmplitude(true)
        level = get_channel_amplitude(True)
        print(f"    Silencio generado en nivel: {level}")
        print(f"    ¡PROBLEMA! El silencio alterna el nivel al empezar")
    
    print(f"    Nivel después del silencio: EDGE_EAR_IS = {EDGE_EAR_IS}")

def simulate_data_stream(num_bits, block_name):
    """Simula el envío de datos (simplificado)"""
    global EDGE_EAR_IS
    print(f"\n  {block_name} - sendDataArray({num_bits} bits)")
    print(f"    Nivel inicial: EDGE_EAR_IS = {EDGE_EAR_IS}")
    
    # Cada bit genera 2 semi-pulsos (para bit 0 y bit 1)
    # Simplificamos: asumimos que el número de semi-pulsos es par
    # entonces el nivel final depende de si empezamos en up o down
    for i in range(num_bits * 2):  # 2 semi-pulsos por bit
        get_channel_amplitude(True)
    
    print(f"    Nivel final: EDGE_EAR_IS = {EDGE_EAR_IS}")

def simulate_gdb_pilot(pilot_stream, block_name):
    """Simula el pilot del GDB"""
    global EDGE_EAR_IS
    print(f"\n  {block_name} - GDB Pilot Stream")
    print(f"    Nivel inicial: EDGE_EAR_IS = {EDGE_EAR_IS}")
    
    total_pulses = sum(item['repeat'] for item in pilot_stream)
    print(f"    Total pulsos en pilot stream: {total_pulses}")
    
    first_level = None
    pulse_count = 0
    
    for item in pilot_stream:
        symbol_id = item['symbol']
        repeat = item['repeat']
        # Asumimos polarity=0 (change edge) para todos
        for r in range(repeat):
            level = get_channel_amplitude(True)
            if first_level is None:
                first_level = level
            pulse_count += 1
            if pulse_count <= 3 or pulse_count > total_pulses - 3:
                print(f"    Pulso {pulse_count}: symbol={symbol_id}, level={level}")
            elif pulse_count == 4:
                print(f"    ... ({total_pulses - 6} pulsos intermedios) ...")
    
    print(f"    Primer pulso: {first_level}")
    print(f"    Nivel final: EDGE_EAR_IS = {EDGE_EAR_IS}")

def simulate_gdb_data(num_symbols, block_name):
    """Simula los datos del GDB"""
    global EDGE_EAR_IS
    print(f"\n  {block_name} - GDB Data Stream ({num_symbols} símbolos)")
    print(f"    Nivel inicial: EDGE_EAR_IS = {EDGE_EAR_IS}")
    
    # Cada símbolo tiene 2 pulsos (bit 0 o bit 1, ambos tienen 2 semi-pulsos)
    for i in range(num_symbols * 2):
        get_channel_amplitude(True)
    
    print(f"    Nivel final: EDGE_EAR_IS = {EDGE_EAR_IS}")

print("="*70)
print("SIMULACIÓN DEL FLUJO DE NIVELES - Book of the Dead TZX")
print("="*70)

# Según el análisis anterior:
# Block 1: Standard (8063 pilot), pause=1ms
# Block 2: Standard (3223 pilot), pause=0ms
# Block 3: Standard (8063 pilot), pause=1ms
# Block 5: Standard (8063 pilot), pause=2677ms
# Block 6: GDB (8063+2 pilot = 8065), pause=30741ms
# Block 7: Standard (8063 pilot), pause=0ms

print("\n" + "="*70)
print("BLOQUE 5 (Standard - pause=2677ms)")
print("="*70)

EDGE_EAR_IS = "down"  # Asumimos que empieza en down

pilot_tone(8063, "Block 5")
sync_tone("SYNC1")
sync_tone("SYNC2")
simulate_data_stream(100, "Block 5")  # Simplificado
silence(2677, "Block 5")

print("\n" + "="*70)
print("BLOQUE 6 (GDB - pause=30741ms)")
print("="*70)

# El GDB debería heredar el nivel del bloque anterior
print(f"\nNivel heredado del bloque 5: EDGE_EAR_IS = {EDGE_EAR_IS}")

# Pilot stream del GDB: 8063 pulsos + 2 pulsos SYNC
gdb_pilot_stream = [
    {'symbol': 0, 'repeat': 8063},  # Pilot
    {'symbol': 1, 'repeat': 1},      # SYNC1
    {'symbol': 2, 'repeat': 1},      # SYNC2
]
simulate_gdb_pilot(gdb_pilot_stream, "Block 6")

# Data del GDB
simulate_gdb_data(100, "Block 6")  # Simplificado
silence(30741, "Block 6")

print("\n" + "="*70)
print("BLOQUE 7 (Standard - después del GDB)")
print("="*70)

# El bloque 7 debería heredar el nivel del bloque 6
print(f"\nNivel heredado del bloque 6: EDGE_EAR_IS = {EDGE_EAR_IS}")

pilot_tone(8063, "Block 7")

print("\n" + "="*70)
print("ANÁLISIS DEL PROBLEMA")
print("="*70)

print("""
El problema está en silence():

1. silence() llama a pulseSilence() con changeNextEARedge=true
2. pulseSilence() llama a getChannelAmplitude(true) que ALTERNA el nivel
3. Esto significa que el silencio se genera en un nivel DIFERENTE al último pulso de datos

Según la especificación TZX:
- "A 'Pause' block consists of a 'low' pulse level"
- "At the end of a 'Pause' block the 'current pulse level' is low"

El silencio debería:
1. Completar el último flanco si es necesario (1ms de terminador)
2. Generar el resto del silencio en nivel LOW
3. Dejar EDGE_EAR_IS = down al final

El código actual:
1. Alterna el nivel AL EMPEZAR el silencio
2. Genera todo el silencio en ESE nivel (que puede ser HIGH o LOW)
3. Deja EDGE_EAR_IS en el nivel opuesto al silencio

SOLUCIÓN PROPUESTA:
En pulseSilence(), NO alternar el nivel. El silencio debe:
- Si el nivel actual es HIGH: generar 1ms en HIGH (terminator), luego LOW
- Si el nivel actual es LOW: generar directamente en LOW
- Al final: EDGE_EAR_IS = down (siempre)
""")
