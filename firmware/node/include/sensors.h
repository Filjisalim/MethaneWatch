/**
 * sensors.h – Antarmuka Pembacaan Sensor
 * ========================================
 * Mendukung BME280 (suhu, kelembapan) dan MQ-4 (gas CH4).
 * Mode SIM_MODE menghasilkan pembacaan palsu berpola untuk pengujian.
 *
 * Prototipe awal. Belum diuji di lapangan.
 * Semua nilai teknis adalah asumsi sampai diverifikasi ke datasheet.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>

// ---------------------------------------------------------------
// Struktur hasil pembacaan sensor
// ---------------------------------------------------------------

typedef struct {
    bool    valid;           // true jika pembacaan berhasil
    float   temp_c;          // Suhu (°C)
    float   rh_pct;          // Kelembapan relatif (%)
    float   pressure_hpa;    // Tekanan (hPa) – opsional, dari BME280
    uint16_t ch4_raw_mv;     // Tegangan output MQ4 setelah pembagi (mV)
    uint16_t vbat_mv;        // Tegangan baterai (mV)
    bool    bme_ok;          // true jika BME280 berhasil diinisialisasi
    bool    warmup_ok;       // true jika waktu pemanasan terpenuhi
    char    error_msg[64];   // Pesan error jika !valid
} SensorReading;

// ---------------------------------------------------------------
// Fungsi sensor
// ---------------------------------------------------------------

/**
 * Inisialisasi sensor (BME280, ADC).
 * Harus dipanggil sekali di setup().
 *
 * @return true jika berhasil.
 */
bool sensors_init(void);

/**
 * Aktifkan daya ke sensor MQ-4.
 * Setelah ini, tunggu SENSOR_WARMUP_SEC sebelum membaca.
 *
 * [Verifikasi: periksa rangkaian switching daya Anda]
 */
void sensors_power_on(void);

/**
 * Matikan daya ke sensor MQ-4 (hemat daya saat deep sleep).
 */
void sensors_power_off(void);

/**
 * Baca semua sensor dan kembalikan hasil.
 * Mengambil NUM_SAMPLES sampel MQ-4 dan mengambil mediannya.
 *
 * @return SensorReading yang berisi semua data.
 */
SensorReading sensors_read(void);

/**
 * Konversi tegangan output MQ-4 ke estimasi konsentrasi.
 *
 * CATATAN PENTING:
 *   Konversi ini memerlukan kalibrasi terhadap sensor referensi.
 *   Nilai yang dikembalikan di sini adalah ESTIMASI KASAR menggunakan
 *   kurva karakteristik datasheet yang belum diverifikasi.
 *   [Verifikasi: kalibrasi dengan sensor referensi NDIR]
 *
 *   Konversi akhir dilakukan di sisi analitik Python menggunakan
 *   data kalibrasi yang lebih akurat.
 *
 * @param mv  Tegangan output MQ4 (mV, setelah faktor pembagi).
 * @return    Estimasi konsentrasi CH4 (ppm) – ASUMSI KASAR [Verifikasi]
 */
float sensors_mv_to_ppm_estimate(uint16_t mv);
