/**
 * test_packet.cpp – Uji Unit PlatformIO Native untuk Paket MethaneWatch
 * =======================================================================
 * Uji menggunakan framework Unity (bawaan PlatformIO native test).
 *
 * Jalankan dengan:
 *   pio test -e native_test
 *
 * Prototipe awal. Belum diuji di lapangan.
 * Semua nilai adalah asumsi sampai diverifikasi.
 */

#define NATIVE_TEST 1

#include <unity.h>
#include <string.h>
#include <stdint.h>

// Sertakan implementasi langsung (bukan Arduino)
#include "../src/packet.cpp"
#include "../src/power.cpp"

// ---------------------------------------------------------------
// Helper
// ---------------------------------------------------------------

static MWPacket make_test_packet(
    uint8_t  node_id  = 1,
    uint32_t seq      = 42,
    uint32_t ts       = 1730000000,
    uint16_t ch4_mv   = 1500,
    float    temp_c   = 27.5f,
    float    rh_pct   = 65.0f,
    uint16_t vbat_mv  = 3900,
    uint8_t  flags    = FLAG_SIM_MODE | FLAG_WARMUP_OK | FLAG_BME_OK
) {
    MWPacket pkt;
    mw_build_packet(&pkt, node_id, 0x01, seq, ts,
                    ch4_mv, temp_c, rh_pct, vbat_mv, flags);
    return pkt;
}

// ---------------------------------------------------------------
// Test: Magic bytes
// ---------------------------------------------------------------

void test_magic_bytes(void) {
    MWPacket pkt = make_test_packet();
    TEST_ASSERT_EQUAL_UINT8(MW_MAGIC_0, pkt.magic[0]);
    TEST_ASSERT_EQUAL_UINT8(MW_MAGIC_1, pkt.magic[1]);
    TEST_ASSERT_TRUE(mw_validate_magic(&pkt));
}

// ---------------------------------------------------------------
// Test: CRC valid setelah build
// ---------------------------------------------------------------

void test_crc_valid_after_build(void) {
    MWPacket pkt = make_test_packet();
    TEST_ASSERT_TRUE(mw_validate_crc(&pkt));
}

// ---------------------------------------------------------------
// Test: CRC gagal setelah data diubah
// ---------------------------------------------------------------

void test_crc_fails_after_tamper(void) {
    MWPacket pkt = make_test_packet();
    pkt.ch4_raw_mv ^= 0xFF;  // Ubah satu bit
    TEST_ASSERT_FALSE(mw_validate_crc(&pkt));
}

// ---------------------------------------------------------------
// Test: Serialize/deserialize identik
// ---------------------------------------------------------------

void test_serialize_deserialize(void) {
    MWPacket original = make_test_packet(2, 99, 1730001000, 1234, 28.3f, 70.1f, 3850, 0x07);
    uint8_t buf[MW_PACKET_SIZE];
    mw_serialize(&original, buf);

    MWPacket restored;
    mw_deserialize(buf, &restored);

    TEST_ASSERT_EQUAL_UINT8(original.node_id,        restored.node_id);
    TEST_ASSERT_EQUAL_UINT32(original.seq_num,       restored.seq_num);
    TEST_ASSERT_EQUAL_UINT32(original.timestamp_unix, restored.timestamp_unix);
    TEST_ASSERT_EQUAL_UINT16(original.ch4_raw_mv,    restored.ch4_raw_mv);
    TEST_ASSERT_EQUAL_INT16(original.temp_x10,       restored.temp_x10);
    TEST_ASSERT_EQUAL_UINT16(original.rh_x10,        restored.rh_x10);
    TEST_ASSERT_EQUAL_UINT16(original.vbat_mv,       restored.vbat_mv);
    TEST_ASSERT_EQUAL_UINT8(original.flags,          restored.flags);
    TEST_ASSERT_EQUAL_UINT16(original.crc16,         restored.crc16);
}

// ---------------------------------------------------------------
// Test: Ukuran paket
// ---------------------------------------------------------------

void test_packet_size(void) {
    TEST_ASSERT_EQUAL_INT(MW_PACKET_SIZE, sizeof(MWPacket));
}

// ---------------------------------------------------------------
// Test: Encoding suhu
// ---------------------------------------------------------------

void test_temperature_encoding(void) {
    MWPacket pkt = make_test_packet(1, 1, 0, 0, 27.5f, 60.0f, 3900, 0);
    // 27.5 × 10 = 275
    TEST_ASSERT_EQUAL_INT16(275, pkt.temp_x10);
}

void test_negative_temperature_encoding(void) {
    MWPacket pkt = make_test_packet(1, 1, 0, 0, -5.3f, 60.0f, 3900, 0);
    // -5.3 × 10 = -53
    TEST_ASSERT_EQUAL_INT16(-53, pkt.temp_x10);
}

// ---------------------------------------------------------------
// Test: Encoding kelembapan
// ---------------------------------------------------------------

void test_rh_encoding(void) {
    MWPacket pkt = make_test_packet(1, 1, 0, 0, 25.0f, 65.3f, 3900, 0);
    // 65.3 × 10 = 653
    TEST_ASSERT_EQUAL_UINT16(653, pkt.rh_x10);
}

// ---------------------------------------------------------------
// Test: Flags SIM_MODE
// ---------------------------------------------------------------

void test_sim_mode_flag(void) {
    MWPacket pkt = make_test_packet(1, 1, 0, 0, 25.0f, 60.0f, 3900, FLAG_SIM_MODE);
    TEST_ASSERT_TRUE(pkt.flags & FLAG_SIM_MODE);
}

// ---------------------------------------------------------------
// Test: CRC16 deterministik
// ---------------------------------------------------------------

void test_crc_deterministic(void) {
    uint8_t data[] = {0x4D, 0x57, 0x01, 0x01};
    uint16_t crc1 = mw_crc16(data, sizeof(data));
    uint16_t crc2 = mw_crc16(data, sizeof(data));
    TEST_ASSERT_EQUAL_UINT16(crc1, crc2);
}

// ---------------------------------------------------------------
// Test: JSON output mengandung field utama
// ---------------------------------------------------------------

void test_json_output(void) {
    MWPacket pkt = make_test_packet();
    char buf[512];
    mw_to_json(&pkt, buf, sizeof(buf));
    TEST_ASSERT_NOT_NULL(strstr(buf, "node_id"));
    TEST_ASSERT_NOT_NULL(strstr(buf, "seq"));
    TEST_ASSERT_NOT_NULL(strstr(buf, "ch4_raw_mv"));
    TEST_ASSERT_NOT_NULL(strstr(buf, "crc_valid"));
}

// ---------------------------------------------------------------
// Test: SOC baterai
// ---------------------------------------------------------------

void test_soc_pct_bounds(void) {
    TEST_ASSERT_EQUAL_UINT8(0,   power_get_soc_pct(3500));
    TEST_ASSERT_EQUAL_UINT8(100, power_get_soc_pct(4200));
    TEST_ASSERT_EQUAL_UINT8(0,   power_get_soc_pct(3000));  // di bawah minimum
    TEST_ASSERT_EQUAL_UINT8(100, power_get_soc_pct(4500)); // di atas maksimum
}

void test_soc_pct_midpoint(void) {
    // 3850 mV → 50% dari [3500, 4200]
    uint8_t soc = power_get_soc_pct(3850);
    TEST_ASSERT_EQUAL_UINT8(50, soc);
}

// ---------------------------------------------------------------
// Main
// ---------------------------------------------------------------

int main(int argc, char **argv) {
    UNITY_BEGIN();

    RUN_TEST(test_magic_bytes);
    RUN_TEST(test_crc_valid_after_build);
    RUN_TEST(test_crc_fails_after_tamper);
    RUN_TEST(test_serialize_deserialize);
    RUN_TEST(test_packet_size);
    RUN_TEST(test_temperature_encoding);
    RUN_TEST(test_negative_temperature_encoding);
    RUN_TEST(test_rh_encoding);
    RUN_TEST(test_sim_mode_flag);
    RUN_TEST(test_crc_deterministic);
    RUN_TEST(test_json_output);
    RUN_TEST(test_soc_pct_bounds);
    RUN_TEST(test_soc_pct_midpoint);

    return UNITY_END();
}
