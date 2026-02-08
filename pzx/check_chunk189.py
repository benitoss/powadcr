# -*- coding: utf-8 -*-
"""
Analiza exactamente qué debería estar pasando en el chunk 189 del datastream.
El error empieza en byte 48506 que es el byte 122 del chunk 189.
"""

# Leer el archivo OK
with open('bc_data_ok.txt', 'r') as f:
    content = f.read()
    
# Parsear bytes
bytes_list = []
for part in content.strip().split(','):
    part = part.strip()
    if part.startswith('0x'):
        try:
            bytes_list.append(int(part, 16))
        except:
            pass

print(f"Total bytes en OK: {len(bytes_list)}")

# Verificar el patrón de bytes alrededor del error
error_byte = 48506
nbytespart = 256

# El chunk 189 cubre bytes 48384-48639
# El chunk 188 cubre bytes 48128-48383
chunk188_start = 188 * nbytespart  # 48128
chunk189_start = 189 * nbytespart  # 48384

print(f"\nChunk 188: bytes {chunk188_start} - {chunk188_start + 255}")
print(f"Chunk 189: bytes {chunk189_start} - {chunk189_start + 255}")
print(f"Error byte {error_byte} está en chunk {error_byte // nbytespart} (posición {error_byte % nbytespart} dentro del chunk)")

# El archivo tiene 49148 bytes
# parts = 49148 // 256 = 191
# rest = 49148 % 256 = 252
DS = 49148
parts = DS // nbytespart
rest = DS % nbytespart
print(f"\nDS = {DS}")
print(f"parts = {parts}")
print(f"rest = {rest}")
print(f"Último byte de datos: {parts * nbytespart + rest - 1}")

# ¿Qué pasa si hay un off-by-one error?
# Si parts se calcula como 192 en lugar de 191...
# O si el último chunk (chunk 190) se procesa mal...

# Vamos a ver qué bytes exactos son los problemáticos
print("\n=== Comparación de datos ===")
print(f"\nBytes que DEBERÍAN estar en posición {error_byte} (chunk 189, offset 122):")
for j in range(10):
    idx = error_byte + j
    if idx < len(bytes_list):
        print(f"  OK[{idx}] = 0x{bytes_list[idx]:02x}")

print(f"\nBytes que ESTÁN en posición {error_byte - 256} (chunk 188, offset 122):")
for j in range(10):
    idx = error_byte - 256 + j
    if idx < len(bytes_list):
        print(f"  OK[{idx}] = 0x{bytes_list[idx]:02x}")

# Si la hipótesis es correcta, los datos KO son exactamente los de 256 bytes antes
# Eso podría significar que:
# 1. mFile.read() no leyó los datos del chunk 189
# 2. El índice p*nbytespart + i se calculó mal
# 3. El archivo no avanzó la posición después de leer el chunk 188

print("\n=== Verificación de file position ===")
print("La función mFile.read() debería avanzar automáticamente la posición del archivo.")
print("Si no lo hace, o si hay un problema de buffering, podría re-leer el mismo chunk.")
print("")
print("Posibles causas:")
print("1. mFile.read() retornó menos bytes de los esperados")
print("2. Un problema con ps_malloc retornando un buffer no inicializado")
print("3. El tempBuffer del chunk anterior no se limpió correctamente")
