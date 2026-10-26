/**
 * lora_comm.h – Antarmuka Komunikasi LoRa
 * =========================================
 * Mendukung modul SX1276/SX1278 via library RadioLib atau LoRa.h.
 *
 * [Verifikasi: frekuensi operasi harus sesuai regulasi Kominfo Indonesia]
 *
 * Prototipe awal. Belum diuji di lapangan.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>

/**
 * Inisialisasi modul LoRa dengan parameter dari config.h.
 *
 * @return true jika berhasil.
 */
bool lora_init(void);

/**
 * Kirim buffer data via LoRa.
 *
 * @param data  Pointer ke data.
 * @param len   Panjang data (byte).
 * @return      true jika berhasil terkirim.
 */
bool lora_send(const uint8_t *data, uint8_t len);

/**
 * Masukkan modul LoRa ke mode sleep untuk hemat daya.
 */
void lora_sleep(void);
