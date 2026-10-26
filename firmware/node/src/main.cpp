/**
 * main.cpp – Firmware Utama Node MethaneWatch
 * =============================================
 * Siklus kerja node:
 *   1. Bangun dari deep sleep
 *   2. Aktifkan & hangatkan sensor MQ-4
 *   3. Baca sensor (suhu, kelembapan, CH4, baterai)
 *   4. Bentuk paket biner + CRC
 *   5. Kirim via LoRa (retry jika gagal → buffer lokal)
 *   6. Kembali ke deep sleep
 *
 * KESELAMATAN (baca SAFETY.md sebelum melanjutkan):
 *   - Uji hanya di bangku (bench) di lingkungan aman
 *   - JANGAN memasang di TPA tanpa izin, pendamping, dan penilaian keselamatan
 *   - Metana mudah terbakar; jaga percikan api
 *
 * Prototipe awal. Belum diuji di lapangan.
 * Semua nilai teknis adalah asumsi sampai diverifikasi ke datasheet.
 */

#ifndef NATIVE_TEST
  #include <Arduino.h>
  #include <esp_sleep.h>
  #include <time.h>
#endif

#include "config.h"
#include "packet.h"
#include "sensors.h"
#include "lora_comm.h"
#include "power.h"

// ---------------------------------------------------------------
// Variabel di RTC memory (bertahan saat deep sleep)
// ---------------------------------------------------------------

#ifndef NATIVE_TEST
// RTC_DATA_ATTR bertahan selama deep sleep di ESP32
RTC_DATA_ATTR static uint32_t g_seq_num    = 0;
RTC_DATA_ATTR static uint32_t g_boot_count = 0;

// Buffer paket yang gagal kirim (tersimpan di RTC memory)
// [Verifikasi: RTC SRAM ESP32 terbatas, ~8 KB. Sesuaikan LOCAL_BUFFER_SIZE]
RTC_DATA_ATTR static uint8_t g_local_buf[LOCAL_BUFFER_SIZE][MW_PACKET_SIZE];
RTC_DATA_ATTR static uint8_t g_buf_head  = 0;
RTC_DATA_ATTR static uint8_t g_buf_count = 0;
#else
// Stub untuk native test
static uint32_t g_seq_num    = 0;
static uint32_t g_boot_count = 0;
#endif

// ---------------------------------------------------------------
// Fungsi bantu: simpan paket ke buffer lokal
// ---------------------------------------------------------------

#if !defined(NATIVE_TEST)
static void buffer_push(const uint8_t *pkt_bytes) {
    if (g_buf_count >= LOCAL_BUFFER_SIZE) {
        // Buffer penuh – buang paket tertua (FIFO overwrite)
        g_buf_head = (g_buf_head + 1) % LOCAL_BUFFER_SIZE;
        g_buf_count--;
    }
    uint8_t idx = (g_buf_head + g_buf_count) % LOCAL_BUFFER_SIZE;
    memcpy(g_local_buf[idx], pkt_bytes, MW_PACKET_SIZE);
    g_buf_count++;
}

static bool buffer_pop(uint8_t *pkt_bytes) {
    if (g_buf_count == 0) return false;
    memcpy(pkt_bytes, g_local_buf[g_buf_head], MW_PACKET_SIZE);
    g_buf_head  = (g_buf_head + 1) % LOCAL_BUFFER_SIZE;
    g_buf_count--;
    return true;
}
#endif

// ---------------------------------------------------------------
// Setup (berjalan sekali per boot dari deep sleep)
// ---------------------------------------------------------------

void setup() {
#ifndef NATIVE_TEST
    Serial.begin(115200);
    delay(100);

    g_boot_count++;

    Serial.println(F("=== MethaneWatch Node Firmware ==="));
    Serial.println(F("Prototipe awal. Belum diuji di lapangan."));
    Serial.print(F("Boot #")); Serial.println(g_boot_count);
    Serial.print(F("Seq # ")); Serial.println(g_seq_num);

    #if SIM_MODE == 1
    Serial.println(F("[SIMULASI] Mode simulasi aktif. Data BUKAN dari sensor nyata."));
    #endif

    // Inisialisasi sensor
    if (!sensors_init()) {
        Serial.println(F("[ERROR] Inisialisasi sensor gagal."));
        // Lanjut; bme_ok=false akan ditandai di flags paket
    }

    // Aktifkan daya sensor MQ-4 dan tunggu pemanasan
    #if SIM_MODE == 0
    sensors_power_on();
    Serial.print(F("Menunggu pemanasan sensor "));
    Serial.print(SENSOR_WARMUP_SEC);
    Serial.println(F(" detik... [Verifikasi: cek datasheet MQ-4 untuk waktu pemanasan]"));
    delay((uint32_t)SENSOR_WARMUP_SEC * 1000UL);
    #endif

    // Baca sensor
    SensorReading reading = sensors_read();

    if (!reading.valid && strlen(reading.error_msg) > 0) {
        Serial.print(F("[WARN] "));
        Serial.println(reading.error_msg);
    }

    // Dapatkan timestamp
    // [Verifikasi: tambahkan sinkronisasi NTP atau RTC hardware untuk timestamp akurat]
    uint32_t ts = (uint32_t)(millis() / 1000UL);  // ASUMSI: pakai uptime saja [Verifikasi]
    Serial.println(F("[Verifikasi] Timestamp menggunakan uptime, bukan waktu nyata. Tambahkan RTC/NTP."));

    // Build flags
    uint8_t flags = 0;
    #if SIM_MODE == 1
    flags |= FLAG_SIM_MODE;
    #endif
    if (reading.warmup_ok) flags |= FLAG_WARMUP_OK;
    if (reading.bme_ok)    flags |= FLAG_BME_OK;

    // Bangun paket
    MWPacket pkt;
    mw_build_packet(
        &pkt,
        (uint8_t)NODE_ID,
        FIRMWARE_VERSION,
        g_seq_num,
        ts,
        reading.ch4_raw_mv,
        reading.temp_c,
        reading.rh_pct,
        reading.vbat_mv,
        flags
    );
    g_seq_num++;

    // Debug JSON ke Serial
    char json_buf[256];
    mw_to_json(&pkt, json_buf, sizeof(json_buf));
    Serial.print(F("[PKT] "));
    Serial.println(json_buf);

    // Serialize paket
    uint8_t pkt_bytes[MW_PACKET_SIZE];
    mw_serialize(&pkt, pkt_bytes);

    // Inisialisasi LoRa
    bool lora_ok = lora_init();
    if (!lora_ok) {
        Serial.println(F("[ERROR] LoRa tidak terdeteksi. Paket disimpan ke buffer."));
        buffer_push(pkt_bytes);
    } else {
        // Coba kirim paket yang ada di buffer dulu (offline-first)
        uint8_t buffered[MW_PACKET_SIZE];
        uint8_t flushed = 0;
        while (g_buf_count > 0 && flushed < 5) {
            if (buffer_pop(buffered)) {
                bool sent = lora_send(buffered, MW_PACKET_SIZE);
                if (!sent) {
                    // Kembalikan ke buffer
                    buffer_push(buffered);
                    break;
                }
                flushed++;
            }
        }

        // Kirim paket saat ini
        bool sent = false;
        for (int attempt = 0; attempt < LORA_MAX_RETRIES; attempt++) {
            if (attempt > 0) {
                flags |= FLAG_LORA_RETRY;
                // Update flag di paket (rebuild)
                mw_build_packet(&pkt,
                    (uint8_t)NODE_ID, FIRMWARE_VERSION, pkt.seq_num,
                    pkt.timestamp_unix, reading.ch4_raw_mv,
                    reading.temp_c, reading.rh_pct, reading.vbat_mv, flags);
                mw_serialize(&pkt, pkt_bytes);
            }

            sent = lora_send(pkt_bytes, MW_PACKET_SIZE);
            if (sent) {
                Serial.print(F("[LoRa] Paket terkirim pada percobaan ke-"));
                Serial.println(attempt + 1);
                break;
            }
            Serial.print(F("[LoRa] Percobaan ke-"));
            Serial.print(attempt + 1);
            Serial.println(F(" gagal."));
            delay(500);
        }

        if (!sent) {
            Serial.println(F("[LoRa] Gagal mengirim. Disimpan ke buffer lokal."));
            buffer_push(pkt_bytes);
        }
    }

    // Matikan sensor dan LoRa sebelum tidur
    sensors_power_off();
    lora_sleep();

    // Tidur
    Serial.print(F("Deep sleep selama "));
    Serial.print(SAMPLING_INTERVAL_SEC);
    Serial.println(F(" detik."));
    Serial.flush();

    esp_sleep_enable_timer_wakeup((uint64_t)SAMPLING_INTERVAL_SEC * 1000000ULL);
    esp_deep_sleep_start();

#endif  // !NATIVE_TEST
}

// ---------------------------------------------------------------
// Loop (tidak digunakan – selalu deep sleep setelah setup)
// ---------------------------------------------------------------

void loop() {
    // Tidak digunakan. ESP32 masuk deep sleep di akhir setup().
    // Fungsi ini seharusnya tidak pernah dipanggil.
#ifndef NATIVE_TEST
    esp_deep_sleep_start();
#endif
}
