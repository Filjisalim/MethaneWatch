/**
 * lora_comm.cpp – Implementasi Komunikasi LoRa
 * ==============================================
 * Prototipe awal. Belum diuji di lapangan.
 *
 * Menggunakan library LoRa.h (Sandeep Mistry) sebagai default.
 * Jika menggunakan RadioLib, ganti bagian yang ditandai.
 *
 * [Verifikasi: pilih library sesuai modul yang digunakan]
 */

#include "lora_comm.h"
#include "config.h"

#ifndef NATIVE_TEST
  #include <Arduino.h>
  #if SIM_MODE == 0
    // Gunakan library LoRa.h (tersedia di PlatformIO: sandeep-mistry/LoRa)
    // [Verifikasi: tambahkan library ini ke platformio.ini jika diperlukan]
    #include <LoRa.h>
  #endif
#endif

bool lora_init(void) {
#if defined(NATIVE_TEST) || SIM_MODE == 1
    // Mode simulasi/native: selalu berhasil
    return true;

#else
    // Mode hardware
    LoRa.setPins(PIN_LORA_CS, PIN_LORA_RST, PIN_LORA_DIO0);
    if (!LoRa.begin(LORA_FREQ_HZ)) {
        // [Verifikasi: pastikan frekuensi legal di Indonesia. Cek SDPPI/Kominfo.]
        return false;
    }
    LoRa.setSpreadingFactor(LORA_SF);
    LoRa.setSignalBandwidth(LORA_BW);
    LoRa.setCodingRate4(LORA_CR);
    LoRa.setTxPower(LORA_TX_POWER);
    // [Verifikasi: TX power sesuai regulasi dan kemampuan modul]
    return true;
#endif
}

bool lora_send(const uint8_t *data, uint8_t len) {
#if defined(NATIVE_TEST) || SIM_MODE == 1
    // Mode simulasi: pura-pura berhasil kirim
    return true;

#else
    LoRa.beginPacket();
    LoRa.write(data, len);
    int result = LoRa.endPacket(false);  // false = blocking mode
    return (result == 1);
#endif
}

void lora_sleep(void) {
#if defined(NATIVE_TEST) || SIM_MODE == 1
    return;
#else
    LoRa.sleep();
    // [Verifikasi: beberapa modul memerlukan delay setelah perintah sleep]
#endif
}
