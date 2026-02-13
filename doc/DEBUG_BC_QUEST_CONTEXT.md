# Debug Context: BC's Quest for Tires - Spectrum+ Reset Issue

**Fecha:** 7 Enero 2026  
**Estado:** EN PROGRESO - Spectrum+ se reinicia durante carga GDB  
**Archivo problemático:** `BC's Quest for Tires.tzx`

---

## RESUMEN DEL PROBLEMA

BC's Quest for Tires causa **RESET del Spectrum+** durante la reproducción del bloque GDB, específicamente después del tono guía (pilot/sync). La carga se inicia pero el Spectrum se reinicia antes de completar.

---

## ESTRUCTURA DEL ARCHIVO BC's Quest (Bloque GDB - ID 0x19)

```
TOTP = 3          (3 entradas PRLE, NO 3 pulsos)
NPP = 2           (2 pulsos por símbolo pilot)
ASP = 3           (3 símbolos pilot definidos)
TOTD = 393184     (total pulsos de datos)
NPD = 2           (2 pulsos por símbolo de datos)
ASD = 2           (2 símbolos de datos definidos)

PILOT SYMBOLS:
  Symbol 0: [2168, 0]      - Pilot tone (2168 T-states, 0=fin)
  Symbol 1: [667, 735]     - Sync1
  Symbol 2: [780, 1170] x4 pulsos - Sync2 (4 semi-pulsos)

DATA SYMBOLS:
  Symbol 0: [780, 780]     - SIMÉTRICO (bit 0)
  Symbol 1: [780, 1560]    - **ASIMÉTRICO** (bit 1) ← PROBLEMA POTENCIAL

PRLE (Pilot Run-Length Encoding):
  Entry 0: Symbol 0 x 3223 repeticiones (pilot tone)
  Entry 1: Symbol 1 x 1 repetición (sync1)
  Entry 2: Symbol 2 x 4 repeticiones (sync2)
  TOTAL: 3228 símbolos de pilot/sync

DATA:
  NB = 1 (1 bit por símbolo)
  DS = 49148 bytes de datos
```

---

## CORRECCIONES APLICADAS (en TZXprocessor.h)

### 1. PRLE Parsing (líneas ~1255-1295)
**CORREGIDO:** Ahora lee exactamente TOTP entradas del PRLE.
```cpp
for (int i=0;i<TOTP;i++)
{
    _myTZX.descriptor[currentBlock].symbol.pilotStream[i].symbol = getBYTE(mFile,coff);
    coff++;
    _myTZX.descriptor[currentBlock].symbol.pilotStream[i].repeat = getWORD(mFile,coff);
    coff+=2;
}
_myTZX.descriptor[currentBlock].symbol.numPrleEntries = TOTP;
```

### 2. Polarity Fix - PILOT/SYNC (líneas ~3900-3950)
**APLICADO:** Solo el primer pulso (r==0) usa el flag de polaridad del símbolo. Los pulsos siguientes SIEMPRE alternan.

### 3. Polarity Fix - DATA (líneas ~3998-4060)
**APLICADO:** Misma lógica - primer pulso usa flag, resto alterna.

---

## COMPARACIÓN CON ARCHIVOS QUE FUNCIONAN

| Archivo | Data Symbols | Estado |
|---------|--------------|--------|
| Dan Dare 2 | [555,555] y [1110,1110] SIMÉTRICOS | ✅ FUNCIONA |
| test_gdb_sym_v2.tzx | [855,855] y [1710,1710] SIMÉTRICOS | ✅ FUNCIONA |
| test_gdb_asym_v2.tzx | [855,855] y [855,1710] ASIMÉTRICOS | ❌ FALLA (esperado) |
| BC's Quest | [780,780] y [780,1560] **ASIMÉTRICOS** | ❌ RESET |

**CONCLUSIÓN:** El problema parece estar relacionado con los **símbolos de datos asimétricos** [780, 1560].

---

## HIPÓTESIS PENDIENTES DE INVESTIGAR

### Hipótesis 1: Timing incorrecto en símbolos asimétricos
El símbolo [780, 1560] genera una forma de onda donde:
- Primer semi-pulso: 780 T-states
- Segundo semi-pulso: 1560 T-states

Esto podría estar confundiendo al ROM loader del Spectrum que espera pulsos simétricos.

### Hipótesis 2: Overflow o corrupción en reproducción de datos
Con 393184 pulsos totales y datos asimétricos, podría haber:
- Desbordamiento de buffer
- Timing drift acumulado
- Problema con el cálculo de duración total

### Hipótesis 3: Problema con la polaridad en transición pilot→data
La transición entre la sección pilot/sync y la sección de datos podría no mantener la polaridad correcta.

### Hipótesis 4: El reset es por señal de audio incorrecta
Una señal de audio malformada podría causar que el Spectrum interprete algo como un RESET (poco probable pero posible).

---

## ARCHIVOS DE PRUEBA CREADOS

En carpeta `pzx/`:
- `test_pilot_zero_clean.tzx` - Solo pilot [2168,0] → **FUNCIONA**
- `test_gdb_sym_v2.tzx` - GDB con datos simétricos → **FUNCIONA**
- `test_gdb_asym_v2.tzx` - GDB con datos asimétricos → **FALLA**
- `test_standard.tzx` - Bloque estándar ID 0x10 → **FUNCIONA**
- `quick_check.py` - Script para analizar estructura TZX

---

## PRÓXIMOS PASOS SUGERIDOS

1. **Verificar transición pilot→data:** Añadir debug para ver el estado de polaridad justo antes de empezar los datos.

2. **Comparar timing con emulador:** Usar un emulador que muestre la forma de onda y comparar con lo que genera PowaDCR.

3. **Probar con pausa entre pilot y data:** Añadir pequeña pausa para ver si el problema es de timing.

4. **Investigar el comportamiento del ROM loader con pulsos asimétricos:** El ROM loader del Spectrum espera pulsos de duración específica. Los pulsos asimétricos podrían estar fuera de tolerancia.

5. **Revisar ZXProcessor.h:** La función `playCustomSymbol()` podría tener problemas con duraciones asimétricas.

---

## CÓDIGO RELEVANTE PARA REVISAR

### TZXprocessor.h
- Líneas 1255-1295: Parsing PRLE
- Líneas 3850-3970: Reproducción PILOT/SYNC
- Líneas 3998-4100: Reproducción DATA
- Líneas 1370-1445: Parsing data stream

### ZXProcessor.h
- Función `playCustomSymbol()`: Cómo genera los pulsos

### globales.h
- Estructura `tSymbol`: Contiene `numPrleEntries`

---

## NOTAS ADICIONALES

- Knight Rider (Speedlock): **FUNCIONA** tras correcciones previas
- Dan Dare 2: **FUNCIONA** (usa GDB con símbolos simétricos)
- El problema es específico de GDB con **datos asimétricos**
- El Spectrum+ 48K es el hardware de prueba

---

**Guardado:** 7 Enero 2026
