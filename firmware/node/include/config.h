/**
 * config.h – Konfigurasi Node MethaneWatch
 * ==========================================
 * Edit file ini untuk menyesuaikan ID node, interval sampling,
 * dan parameter LoRa.
 *
 * JANGAN simpan kunci API, password, atau token di sini.
 * JANGAN commit nilai rahasia ke repositori.
 *
 * Prototipe awal. Belum diuji di lapangan.
 * Semua nilai teknis adalah asumsi sampai diverifikasi ke datasheet.
 */

#pragma once

// ---------------------------------------------------------------
// Identitas Node
// ---------------------------------------------------------------
// NODE_ID biasanya di-set dari platformio.ini (-D NODE_ID=X)
// Fallback jika tidak di-set dari build flags:
#ifndef NODE_ID
  #define NODE_ID 1
#endif

// Versi firmware (untuk identifikasi paket)
#define FIRMWARE_VERSION 0x01

// ---------------------------------------------------------------
// Interval sampling dan deep sleep
// ---------------------------------------------------------------

/**
 * Interval antara pengukuran (detik).
 * Selama interval ini, ESP32 berada dalam deep sleep.
 *
 * [Verifikasi: sesuaikan dengan anggaran daya aktual setelah mengukur
 * konsumsi arus komponen di lapangan]
 */
#define SAMPLING_INTERVAL_SEC 900   // 15 menit

/**
 * Durasi pemanasan sensor MQ-4 sebelum pembacaan (detik).
 *
 * [Verifikasi: cek datasheet MQ-4. Pemanasan penuh pertama kali
 *  bisa mencapai 48 jam; per siklus biasanya 30–60 detik.
 *  Nilai ini sangat memengaruhi konsumsi daya.]
 *
 * ASUMSI SEMENTARA: 60 detik [Verifikasi datasheet MQ-4]
 */
#define SENSOR_WARMUP_SEC 60

/**
 * Jumlah sampel yang diambil per siklus (untuk median).
 * Mengambil median dari beberapa sampel membantu meredam noise.
 *
 * [Verifikasi: seimbangkan antara stabilitas data dan waktu pemanasan]
 */
#define NUM_SAMPLES 5

/**
 * Jeda antar sampel (milidetik).
 */
#define SAMPLE_INTERVAL_MS 1000

// ---------------------------------------------------------------
// Pin ESP32 – Konfigurasi Hardware
// ---------------------------------------------------------------

/**
 * Pin ADC untuk pembacaan sensor MQ-4 (setelah pembagi tegangan).
 *
 * CATATAN PENTING – PEMBAGI TEGANGAN:
 *   Output analog MQ-4 adalah 0–5 V (saat beroperasi pada 5 V).
 *   ADC ESP32 hanya menerima maksimum 3,3 V.
 *   Diperlukan pembagi tegangan resistor:
 *
 *       MQ-4 AOUT ──── R1 ──── [PIN_MQ4_ADC] ──── R2 ──── GND
 *
 *   Rumus: V_adc = V_out × R2 / (R1 + R2)
 *   Agar V_adc_max = 3,3 V saat V_out_max = 5,0 V:
 *     R2 / (R1 + R2) = 3,3 / 5,0 = 0,66
 *   Contoh nilai: R1 = 10 kΩ, R2 = 20 kΩ  →  V_adc = 5,0 × 20/30 = 3,33 V
 *
 *   [Verifikasi: hitung ulang dengan multimeter sebelum menghubungkan ke ESP32.
 *    Tegangan di atas 3,6 V dapat merusak ADC ESP32. Periksa tegangan aktual
 *    MQ-4 di pengaturan Anda karena bisa berbeda dari spesifikasi.]
 *
 * [Verifikasi: cek pin ADC yang tersedia dan kualitas ADC di board Anda.
 *  ADC ESP32 memiliki ketidaklinearitas yang perlu dikompensasi. Beberapa
 *  pin ADC (GPIO 34–39) hanya input (tidak ada pull-up internal).]
 */
#define PIN_MQ4_ADC     34   // GPIO34 – hanya input [Verifikasi pin Anda]

/**
 * Pin I²C untuk BME280 (suhu, kelembapan, tekanan).
 * [Verifikasi: sesuaikan dengan wiring aktual Anda]
 */
#define PIN_I2C_SDA     21   // [Verifikasi]
#define PIN_I2C_SCL     22   // [Verifikasi]

/** Alamat I²C BME280 (default: 0x76 atau 0x77 tergantung pin SDO). */
#define BME280_I2C_ADDR 0x76  // [Verifikasi: cek pin SDO di modul Anda]

/**
 * Pin SPI untuk modul LoRa SX1276/SX1278.
 * [Verifikasi: sesuaikan dengan modul LoRa yang Anda gunakan]
 */
#define PIN_LORA_SCK    18   // [Verifikasi]
#define PIN_LORA_MISO   19   // [Verifikasi]
#define PIN_LORA_MOSI   23   // [Verifikasi]
#define PIN_LORA_CS     5    // [Verifikasi]
#define PIN_LORA_RST    14   // [Verifikasi]
#define PIN_LORA_DIO0   26   // [Verifikasi]

/**
 * Pin pembacaan tegangan baterai (melalui pembagi tegangan).
 *
 * CATATAN: Baterai Li-ion 3,7 V (full charge ~4,2 V) juga perlu pembagi tegangan
 * agar tidak melampaui 3,3 V ADC ESP32.
 *
 * Rumus pembagi: R1 = 100 kΩ, R2 = 100 kΩ → V_adc = V_bat / 2
 * Agar aman: V_bat_max = 4,2 V → V_adc = 2,1 V (aman untuk 3,3 V ADC)
 *
 * [Verifikasi: sesuaikan R1/R2 dengan kondisi baterai Anda]
 */
#define PIN_VBAT_ADC    35   // GPIO35 – hanya input [Verifikasi]
#define VBAT_DIVIDER    2.0f // Faktor pembagi [Verifikasi dengan nilai R aktual]

/**
 * Pin untuk mengaktifkan (enable) power ke sensor MQ-4.
 * Memutus daya selama deep sleep untuk menghemat energi.
 * Hubungkan ke gate MOSFET atau pin EN modul daya.
 *
 * [Verifikasi: pastikan rangkaian daya mendukung switching ini]
 */
#define PIN_SENSOR_POWER 27  // [Verifikasi]

// ---------------------------------------------------------------
// Konfigurasi LoRa
// ---------------------------------------------------------------

/**
 * Frekuensi operasi LoRa (Hz).
 * [Verifikasi: cek alokasi frekuensi ISM Indonesia di SDPPI/Kominfo.
 *  Opsi yang sering disebut: 915 MHz atau 923 MHz.
 *  JANGAN mengoperasikan di frekuensi yang tidak diizinkan.]
 */
#ifndef LORA_FREQ_HZ
  #define LORA_FREQ_HZ 923000000L  // [Verifikasi regulasi]
#endif

/**
 * Spreading Factor LoRa (SF7–SF12).
 * SF lebih tinggi = jangkauan lebih jauh, bitrate lebih rendah.
 * [Verifikasi: pilih berdasarkan jangkauan dan duty cycle yang diperlukan]
 */
#define LORA_SF    9    // [Verifikasi]

/**
 * Bandwidth LoRa (Hz). Opsi: 125000, 250000, 500000.
 * [Verifikasi: sesuaikan dengan regulasi dan kebutuhan]
 */
#define LORA_BW    125000  // [Verifikasi]

/**
 * Coding Rate LoRa (4/5 = 5, 4/6 = 6, dst.).
 * [Verifikasi]
 */
#define LORA_CR    5  // [Verifikasi]

/**
 * Daya TX LoRa (dBm). Maksimum tergantung regulasi dan hardware.
 * [Verifikasi: cek batas daya pancar di regulasi Kominfo dan kemampuan modul]
 */
#define LORA_TX_POWER 14  // dBm [Verifikasi regulasi dan spesifikasi modul]

/**
 * Timeout pengiriman LoRa (milidetik).
 */
#define LORA_TX_TIMEOUT_MS 5000

/**
 * Jumlah percobaan ulang pengiriman sebelum menyimpan ke buffer lokal.
 */
#define LORA_MAX_RETRIES 3

// ---------------------------------------------------------------
// Konfigurasi Buffer Lokal
// ---------------------------------------------------------------

/**
 * Ukuran buffer paket yang gagal kirim (tersimpan di RTC memory atau flash).
 * [Verifikasi: sesuaikan dengan kapasitas memori ESP32]
 */
#define LOCAL_BUFFER_SIZE 32

// ---------------------------------------------------------------
// Kalibrasi ADC – ASUMSI AWAL
// ---------------------------------------------------------------

/**
 * Resolusi ADC ESP32 (12-bit = 4096 langkah).
 * [Verifikasi: bisa dikurangi ke 10-bit jika noise menjadi masalah]
 */
#define ADC_RESOLUTION    4096
#define ADC_VREF_MV       3300  // Tegangan referensi ADC (mV) [Verifikasi dengan pengukuran]

/**
 * Faktor konversi ADC ke tegangan MQ-4 setelah pembagi.
 * V_mq4 = (adc_raw / ADC_RESOLUTION) × ADC_VREF_MV × VDIVIDER_FACTOR_MQ4
 *
 * Dengan R1=10kΩ, R2=20kΩ: faktor = (10+20)/20 = 1,5
 * [Verifikasi: hitung ulang dengan nilai R aktual yang diukur]
 */
#define VDIVIDER_FACTOR_MQ4 1.5f  // [Verifikasi dengan R aktual]

// ---------------------------------------------------------------
// Mode Simulasi
// ---------------------------------------------------------------

/**
 * SIM_MODE=1: Gunakan pembacaan sensor palsu berpola.
 * SIM_MODE=0: Gunakan hardware nyata.
 *
 * Di-set melalui build flags di platformio.ini.
 */
#ifndef SIM_MODE
  #define SIM_MODE 0
#endif
