/**
 * packet.cpp – Implementasi Format Paket MethaneWatch
 * =====================================================
 * Prototipe awal. Belum diuji di lapangan.
 *
 * Mendukung kompilasi native (NATIVE_TEST) dan Arduino (ESP32).
 */

#include "packet.h"
#include <string.h>
#include <stdio.h>

// ---------------------------------------------------------------
// CRC16-CCITT (polynomial 0x1021, init 0xFFFF)
// ---------------------------------------------------------------

uint16_t mw_crc16(const uint8_t *data, size_t len) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

// ---------------------------------------------------------------
// Build paket
// ---------------------------------------------------------------

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
) {
    pkt->magic[0]       = MW_MAGIC_0;
    pkt->magic[1]       = MW_MAGIC_1;
    pkt->node_id        = node_id;
    pkt->fw_version     = fw_version;
    pkt->seq_num        = seq_num;
    pkt->timestamp_unix = timestamp;
    pkt->ch4_raw_mv     = ch4_raw_mv;

    // Konversi float ke integer ×10 dengan saturasi sederhana
    int32_t temp_i = (int32_t)(temp_c * 10.0f);
    if (temp_i >  32767) temp_i =  32767;
    if (temp_i < -32768) temp_i = -32768;
    pkt->temp_x10 = (int16_t)temp_i;

    int32_t rh_i = (int32_t)(rh_pct * 10.0f);
    if (rh_i < 0)     rh_i = 0;
    if (rh_i > 65535) rh_i = 65535;
    pkt->rh_x10 = (uint16_t)rh_i;

    pkt->vbat_mv  = vbat_mv;
    pkt->flags    = flags;

    // Hitung CRC dari semua field kecuali CRC itu sendiri
    // (byte 0 sampai sizeof(MWPacket)-2 = 21 byte)
    pkt->crc16 = mw_crc16((const uint8_t *)pkt, sizeof(MWPacket) - sizeof(uint16_t));
}

// ---------------------------------------------------------------
// Validasi
// ---------------------------------------------------------------

bool mw_validate_magic(const MWPacket *pkt) {
    return (pkt->magic[0] == MW_MAGIC_0) && (pkt->magic[1] == MW_MAGIC_1);
}

bool mw_validate_crc(const MWPacket *pkt) {
    uint16_t computed = mw_crc16(
        (const uint8_t *)pkt,
        sizeof(MWPacket) - sizeof(uint16_t)
    );
    return computed == pkt->crc16;
}

// ---------------------------------------------------------------
// Serialize / Deserialize
// ---------------------------------------------------------------

void mw_serialize(const MWPacket *pkt, uint8_t *buf) {
    memcpy(buf, pkt, sizeof(MWPacket));
}

void mw_deserialize(const uint8_t *buf, MWPacket *pkt) {
    memcpy(pkt, buf, sizeof(MWPacket));
}

// ---------------------------------------------------------------
// JSON Debug
// ---------------------------------------------------------------

void mw_to_json(const MWPacket *pkt, char *buf, size_t len) {
    // [CATATAN] Output JSON hanya untuk debug Serial.
    // Tidak digunakan dalam transmisi LoRa normal.
    snprintf(buf, len,
        "{"
        "\"node_id\":%u,"
        "\"fw_ver\":%u,"
        "\"seq\":%lu,"
        "\"ts\":%lu,"
        "\"ch4_raw_mv\":%u,"
        "\"temp_c\":%.1f,"
        "\"rh_pct\":%.1f,"
        "\"vbat_mv\":%u,"
        "\"flags\":\"0x%02X\","
        "\"sim_mode\":%d,"
        "\"crc16\":\"0x%04X\","
        "\"crc_valid\":%d"
        "}",
        pkt->node_id,
        pkt->fw_version,
        (unsigned long)pkt->seq_num,
        (unsigned long)pkt->timestamp_unix,
        pkt->ch4_raw_mv,
        pkt->temp_x10 / 10.0f,
        pkt->rh_x10   / 10.0f,
        pkt->vbat_mv,
        pkt->flags,
        (pkt->flags & FLAG_SIM_MODE) ? 1 : 0,
        pkt->crc16,
        mw_validate_crc(pkt) ? 1 : 0
    );
}
