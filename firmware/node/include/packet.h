/**
 * packet.h – Definisi Format Paket Data MethaneWatch
 * ====================================================
 * Format paket biner ringkas dengan CRC16-CCITT.
 *
 * Prototipe awal. Belum diuji di lapangan.
 * Semua nilai adalah asumsi sampai diverifikasi.
 *
 * FORMAT PAKET (22 byte total):
 * ┌──────────────────────────────────────────────────────────────┐
 * │ Byte │ Nama           │ Tipe   │ Keterangan                  │
 * ├──────────────────────────────────────────────────────────────┤
 * │  0   │ magic[0]       │ uint8  │ 0xMW (0x4D = 'M')           │
 * │  1   │ magic[1]       │ uint8  │ 0x57 = 'W'                  │
 * │  2   │ node_id        │ uint8  │ ID node (1–255)             │
 * │  3   │ fw_version     │ uint8  │ Versi firmware              │
 * │ 4–7  │ seq_num        │ uint32 │ Nomor urut paket (LE)       │
 * │ 8–11 │ timestamp_unix │ uint32 │ Unix timestamp (LE)         │
 * │12–13 │ ch4_raw_mv     │ uint16 │ Tegangan output MQ4 (mV,LE) │
 * │14–15 │ temp_x10       │ int16  │ Suhu ×10 (°C, LE)           │
 * │16–17 │ rh_x10         │ uint16 │ Kelembapan ×10 (%, LE)      │
 * │18–19 │ vbat_mv        │ uint16 │ Tegangan baterai (mV, LE)   │
 * │  20  │ flags          │ uint8  │ Bit flags (lihat komentar)  │
 * │21–22 │ crc16          │ uint16 │ CRC16-CCITT (LE)            │
 * └──────────────────────────────────────────────────────────────┘
 * Total: 23 byte
 *
 * FLAGS (bit 20):
 *   bit 0: SIM_MODE   – 1 jika data simulasi
 *   bit 1: WARMUP_OK  – 1 jika waktu pemanasan sensor terpenuhi
 *   bit 2: BME_OK     – 1 jika sensor BME280 berhasil dibaca
 *   bit 3: LORA_RETRY – 1 jika ada percobaan ulang pengiriman
 *   bit 4–7: reserved
 *
 * CATATAN:
 *   - Semua multi-byte dalam little-endian.
 *   - ch4_raw_mv: tegangan output MQ4 setelah dikoreksi faktor pembagi
 *     (bukan konsentrasi ppm langsung karena konversi Vout→ppm
 *     memerlukan kalibrasi sensor nyata). [Verifikasi]
 *   - Konversi ke ppm dilakukan di sisi analitik Python.
 */

#pragma once

#include <stdint.h>
#include <stddef.h>

// Magic bytes pengenal paket MethaneWatch
#define MW_MAGIC_0  0x4D  // 'M'
#define MW_MAGIC_1  0x57  // 'W'

// Ukuran paket dalam byte (header + payload + CRC)
#define MW_PACKET_SIZE  23

// Flags
#define FLAG_SIM_MODE   (1 << 0)
#define FLAG_WARMUP_OK  (1 << 1)
#define FLAG_BME_OK     (1 << 2)
#define FLAG_LORA_RETRY (1 << 3)

/**
 * Struktur paket data node.
 *
 * Gunakan attribute packed agar tidak ada padding.
 * [Verifikasi: pastikan compiler Anda mendukung __attribute__((packed))]
 */
typedef struct __attribute__((packed)) {
    uint8_t  magic[2];         // 0x4D, 0x57
    uint8_t  node_id;
    uint8_t  fw_version;
    uint32_t seq_num;          // little-endian
    uint32_t timestamp_unix;   // Unix timestamp UTC, little-endian
    uint16_t ch4_raw_mv;       // Tegangan output MQ4 setelah pembagi (mV)
    int16_t  temp_x10;         // Suhu × 10 (contoh: 275 = 27,5 °C)
    uint16_t rh_x10;           // Kelembapan × 10 (contoh: 653 = 65,3 %)
    uint16_t vbat_mv;          // Tegangan baterai (mV)
    uint8_t  flags;
    uint16_t crc16;            // CRC16-CCITT dari byte 0..20
} MWPacket;

// Verifikasi ukuran compile-time
// (Jika gagal kompilasi, berarti ada padding yang tidak diinginkan)
#ifdef __GNUC__
_Static_assert(sizeof(MWPacket) == MW_PACKET_SIZE,
    "Ukuran MWPacket tidak sesuai harapan – cek struct padding");
#endif

// ---------------------------------------------------------------
// Fungsi-fungsi paket
// ---------------------------------------------------------------

/**
 * Hitung CRC16-CCITT (polynomial 0x1021, init 0xFFFF).
 *
 * @param data  Pointer ke buffer data.
 * @param len   Panjang data dalam byte.
 * @return      Nilai CRC16.
 */
uint16_t mw_crc16(const uint8_t *data, size_t len);

/**
 * Bangun paket biner dari data sensor.
 * Mengisi semua field termasuk magic bytes dan CRC.
 *
 * @param pkt           Pointer ke struct MWPacket yang akan diisi.
 * @param node_id       ID node.
 * @param fw_version    Versi firmware.
 * @param seq_num       Nomor urut paket.
 * @param timestamp     Unix timestamp UTC.
 * @param ch4_raw_mv    Tegangan output MQ4 setelah pembagi (mV).
 * @param temp_c        Suhu (°C). Akan dikali 10 dan disimpan sebagai int16.
 * @param rh_pct        Kelembapan (%). Akan dikali 10 dan disimpan sebagai uint16.
 * @param vbat_mv       Tegangan baterai (mV).
 * @param flags         Byte flags.
 */
void mw_build_packet(
    MWPacket *pkt,
    uint8_t   node_id,
    uint8_t   fw_version,
    uint32_t  seq_num,
    uint32_t  timestamp,
    uint16_t  ch4_raw_mv,
    float     temp_c,
    float     rh_pct,
    uint16_t  vbat_mv,
    uint8_t   flags
);

/**
 * Validasi CRC paket yang diterima.
 *
 * @param pkt  Pointer ke paket.
 * @return     true jika CRC valid.
 */
bool mw_validate_crc(const MWPacket *pkt);

/**
 * Validasi magic bytes paket.
 *
 * @param pkt  Pointer ke paket.
 * @return     true jika magic bytes cocok.
 */
bool mw_validate_magic(const MWPacket *pkt);

/**
 * Serialize paket ke buffer byte (untuk transmisi LoRa).
 *
 * @param pkt   Pointer ke struct MWPacket.
 * @param buf   Buffer tujuan (minimal MW_PACKET_SIZE byte).
 */
void mw_serialize(const MWPacket *pkt, uint8_t *buf);

/**
 * Deserialize buffer byte ke struct MWPacket.
 *
 * @param buf   Buffer sumber.
 * @param pkt   Pointer ke struct MWPacket tujuan.
 */
void mw_deserialize(const uint8_t *buf, MWPacket *pkt);

/**
 * Format paket ke string JSON untuk debug (output ke Serial).
 * Tidak digunakan dalam pengiriman LoRa normal.
 *
 * @param pkt   Pointer ke paket.
 * @param buf   Buffer string tujuan (minimal 256 byte).
 * @param len   Panjang buffer.
 */
void mw_to_json(const MWPacket *pkt, char *buf, size_t len);
