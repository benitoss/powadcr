#pragma once

// =================================================================================
// PowaDCR - Custom AudioTools Configuration
// =================================================================================
// Este fichero deshabilita las características no utilizadas de la librería AudioTools
// para reducir el uso de memoria Flash e IRAM.

#define AUI_DISABLE_LOGGING // Deshabilita el logging interno de la librería

// --- Deshabilitar Códecs de Audio no utilizados ---
#define AUI_DISABLE_AAC       // No usamos AAC
//#define AUI_DISABLE_FLAC      // No usamos FLAC
#define AUI_DISABLE_OGG       // No usamos OGG / Vorbis
#define AUI_DISABLE_OPUS      // No usamos Opus
#define AUI_DISABLE_MIDI      // No usamos MIDI
#define AUI_DISABLE_MOD       // No usamos MOD
#define AUI_DISABLE_S3M       // No usamos S3M
#define AUI_DISABLE_XM        // No usamos XM
#define AUI_DISABLE_IT        // No usamos IT
#define AUI_DISABLE_SPEEX     // No usamos Speex
#define AUI_DISABLE_M4A       // No usamos M4A (es parte de AAC)
#define AUI_DISABLE_TS        // No usamos Transport Stream

// --- Deshabilitar APIs y Salidas no utilizadas ---
#define AUI_DISABLE_API_PLAYER  // No usamos la clase AudioPlayer de alto nivel
#define AUI_DISABLE_HTTP        // No usamos el cliente HTTP interno (usamos el nuestro)
#define AUI_DISABLE_A2DP        // No usamos el A2DP de la librería (tenemos el nuestro)
#define AUI_DISABLE_SINE        // No usamos el generador de tonos sinusoidales
#define AUI_DISABLE_ESP_NOW     // No usamos ESP-NOW

// Dejamos habilitados:
// - MP3 (para la radio)
// - WAV (para la grabación)
// - I2S (para la salida al DAC)
// - StreamCopy, StreamTee, etc. (herramientas básicas)