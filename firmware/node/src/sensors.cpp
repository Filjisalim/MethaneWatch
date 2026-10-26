/**
 * sensors.cpp – Implementasi Pembacaan Sensor
 * =============================================
 * Prototipe awal. Belum diuji di lapangan.
 *
 * MODE SIMULASI (SIM_MODE=1):
 *   Menghasilkan pembacaan palsu berpola. Tidak perlu hardware.
 *   Bukan data nyata – hanya untuk pengujian firmware.
 *
 * MODE HARDWARE (SIM_MODE=0):
 *   Memerlukan BME280 pada I²C dan MQ-4 pada ADC.
 *   [Verifikasi: pastikan wiring sesuai config.h sebelum menyalakan]
 */

#include "sensors.h"
#include "config.h"

#include <string.h>
#include <math.h>

// ---------------------------------------------------------------
// Kondisional include (Arduino vs native)
// ---------------------------------------------------------------

#ifndef NATIVE_TEST
  // Header Arduino/ESP32 hanya tersedia di lingkungan Arduino
  #include <Arduino.h>
  #if SIM_MODE == 0
    #include <Wire.h>
    #include <Adafruit_BME280.h>

    static Adafruit_BME280 _bme;
    static bool _bme_initialized = false;
  #endif  // SIM_MODE == 0
#else
  // Stub untuk native test
  #include <stdint.h>
  #include <stdlib.h>
  static uint32_t _sim_tick = 0;
#endif  // NATIVE_TEST

// ---------------------------------------------------------------
// Variabel internal
// ---------------------------------------------------------------

static uint32_t _sim_tick_internal = 0;

// ---------------------------------------------------------------
// Implementasi
// ---------------------------------------------------------------

bool sensors_init(void) {
#if SIM_MODE == 1
    _sim_tick_internal = 0;
    return true;

#else  // Hardware mode
  #ifndef NATIVE_TEST
    // Inisialisasi I²C
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);

    // Inisialisasi BME280
    if (!_bme.begin(BME280_I2C_ADDR)) {
        // [Verifikasi: periksa alamat I²C dan wiring jika gagal di sini]
        _bme_initialized = false;
        return false;
    }
    _bme.setSampling(
        Adafruit_BME280::MODE_FORCED,
        Adafruit_BME280::SAMPLING_X1,  // suhu
        Adafruit_BME280::SAMPLING_X1,  // tekanan
        Adafruit_BME280::SAMPLING_X1,  // kelembapan
        Adafruit_BME280::FILTER_OFF
    );
    _bme_initialized = true;

    // Inisialisasi pin
    analogReadResolution(12);   // 12-bit ADC [Verifikasi: pastikan sesuai ESP32]
    pinMode(PIN_SENSOR_POWER, OUTPUT);
    digitalWrite(PIN_SENSOR_POWER, LOW);  // Matikan power sensor saat init

    return true;
  #else
    return true;
  #endif  // NATIVE_TEST
#endif  // SIM_MODE
}

void sensors_power_on(void) {
#if SIM_MODE == 0 && !defined(NATIVE_TEST)
    digitalWrite(PIN_SENSOR_POWER, HIGH);
    // Tunggu pemanasan di main.cpp menggunakan delay(SENSOR_WARMUP_SEC * 1000)
    // [Verifikasi: waktu pemanasan MQ-4 sesuai datasheet]
#endif
}

void sensors_power_off(void) {
#if SIM_MODE == 0 && !defined(NATIVE_TEST)
    digitalWrite(PIN_SENSOR_POWER, LOW);
#endif
}

// ---------------------------------------------------------------
// Fungsi median internal
// ---------------------------------------------------------------

static uint16_t _median_u16(uint16_t *arr, int n) {
    // Bubble sort sederhana (n kecil, aman untuk embedded)
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                uint16_t tmp = arr[j];
                arr[j]       = arr[j + 1];
                arr[j + 1]   = tmp;
            }
        }
    }
    return arr[n / 2];
}

// ---------------------------------------------------------------
// Pembacaan simulasi
// ---------------------------------------------------------------

#if SIM_MODE == 1
static SensorReading _read_simulated(void) {
    SensorReading r;
    memset(&r, 0, sizeof(r));

    // Pola simulasi: sinusoidal dengan tick internal
    // BUKAN data lapangan – hanya untuk pengujian
    float tick = (float)_sim_tick_internal;
    float t_cycle = 96.0f;  // satu siklus = 96 tick (96×15 menit = 24 jam simulasi)

    r.temp_c      = 27.0f + 4.0f * sinf(2.0f * 3.14159f * tick / t_cycle);
    r.rh_pct      = 72.0f - 6.0f * sinf(2.0f * 3.14159f * tick / t_cycle);
    r.pressure_hpa = 1013.0f;  // konstan (tidak ada sensor tekanan di node dasar)

    // Simulasi tegangan MQ-4: baseline + variasi diurnal + noise deterministik
    float base_mv  = 1200.0f + 200.0f * sinf(2.0f * 3.14159f * tick / t_cycle);
    float noise_mv = (float)((int)(_sim_tick_internal * 1234567 % 100) - 50) * 0.5f;
    uint16_t ch4_mv = (uint16_t)(base_mv + noise_mv);
    r.ch4_raw_mv  = ch4_mv;

    // Tegangan baterai turun perlahan
    float vbat = 4100.0f - tick * 0.5f;
    r.vbat_mv   = (uint16_t)(vbat > 3500.0f ? vbat : 3500.0f);

    r.bme_ok    = true;
    r.warmup_ok = true;
    r.valid     = true;

    _sim_tick_internal++;
    return r;
}
#endif

// ---------------------------------------------------------------
// Pembacaan hardware nyata
// ---------------------------------------------------------------

#if SIM_MODE == 0 && !defined(NATIVE_TEST)
static SensorReading _read_hardware(void) {
    SensorReading r;
    memset(&r, 0, sizeof(r));

    // Baca BME280
    if (_bme_initialized) {
        _bme.takeForcedMeasurement();  // [Verifikasi: mode forced untuk hemat daya]
        r.temp_c      = _bme.readTemperature();
        r.rh_pct      = _bme.readHumidity();
        r.pressure_hpa = _bme.readPressure() / 100.0f;
        r.bme_ok      = true;
    } else {
        // BME280 gagal – gunakan nilai default dan tandai error
        r.temp_c      = 25.0f;  // fallback [Verifikasi: jangan gunakan ini untuk kalibrasi]
        r.rh_pct      = 60.0f;  // fallback
        r.pressure_hpa = 1013.0f;
        r.bme_ok      = false;
        snprintf(r.error_msg, sizeof(r.error_msg),
                 "BME280 tidak terdeteksi. Periksa wiring pin SDA=%d SCL=%d addr=0x%02X",
                 PIN_I2C_SDA, PIN_I2C_SCL, BME280_I2C_ADDR);
    }

    // Baca MQ-4 – ambil NUM_SAMPLES dan median
    // [Verifikasi: waktu pemanasan sudah ditunggu di main.cpp sebelum fungsi ini]
    uint16_t samples[NUM_SAMPLES];
    for (int i = 0; i < NUM_SAMPLES; i++) {
        int raw = analogRead(PIN_MQ4_ADC);
        // Konversi ADC ke tegangan (mV) di titik ADC, lalu ke tegangan MQ4
        // V_adc = (raw / ADC_RESOLUTION) × ADC_VREF_MV
        // V_mq4 = V_adc × VDIVIDER_FACTOR_MQ4
        // [Verifikasi: nilai ADC_VREF_MV dan VDIVIDER_FACTOR_MQ4 di config.h]
        uint32_t v_adc_mv = ((uint32_t)raw * ADC_VREF_MV) / ADC_RESOLUTION;
        uint16_t v_mq4_mv = (uint16_t)(v_adc_mv * VDIVIDER_FACTOR_MQ4);
        samples[i] = v_mq4_mv;

        delay(SAMPLE_INTERVAL_MS);
    }
    r.ch4_raw_mv = _median_u16(samples, NUM_SAMPLES);

    // Baca tegangan baterai
    int vbat_raw = analogRead(PIN_VBAT_ADC);
    uint32_t v_adc_mv = ((uint32_t)vbat_raw * ADC_VREF_MV) / ADC_RESOLUTION;
    r.vbat_mv = (uint16_t)(v_adc_mv * VBAT_DIVIDER);
    // [Verifikasi: VBAT_DIVIDER sesuai dengan nilai R1/R2 yang dipasang]

    r.warmup_ok = true;  // Diasumsikan sudah dipanggil delay pemanasan di main.cpp
    r.valid     = r.bme_ok;  // Valid jika minimal BME280 OK
    return r;
}
#endif

// ---------------------------------------------------------------
// API publik
// ---------------------------------------------------------------

SensorReading sensors_read(void) {
#if SIM_MODE == 1
    return _read_simulated();
#elif defined(NATIVE_TEST)
    // Stub untuk native test – kembalikan data deterministik
    SensorReading r;
    memset(&r, 0, sizeof(r));
    r.temp_c     = 25.0f;
    r.rh_pct     = 60.0f;
    r.ch4_raw_mv = 1500;
    r.vbat_mv    = 3900;
    r.bme_ok     = true;
    r.warmup_ok  = true;
    r.valid      = true;
    return r;
#else
    return _read_hardware();
#endif
}

float sensors_mv_to_ppm_estimate(uint16_t mv) {
    /**
     * Konversi kasar tegangan → ppm berdasarkan karakteristik datasheet MQ-4.
     *
     * PERINGATAN:
     *   Ini adalah ESTIMASI SANGAT KASAR dan belum dikalibrasi.
     *   Konversi akurat memerlukan kalibrasi terhadap sensor referensi NDIR.
     *   [Verifikasi: gunakan modul correction.py untuk koreksi yang lebih baik]
     *
     *   Model sederhana linear: ppm = a × mv + b
     *   Koefisien a dan b adalah ASUMSI SEMENTARA. [Verifikasi datasheet MQ-4]
     */
    const float a = 0.5f;      // ppm/mV – ASUMSI [Verifikasi]
    const float b = -200.0f;   // offset – ASUMSI [Verifikasi]
    float ppm = a * (float)mv + b;
    if (ppm < 0.0f) ppm = 0.0f;
    return ppm;
}
