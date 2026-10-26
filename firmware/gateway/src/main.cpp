/**
 * main.cpp – Firmware Gateway MethaneWatch (ESP32 + LoRa)
 * ==========================================================
 * Menerima paket LoRa dari node, memvalidasi CRC,
 * mendeteksi paket hilang, dan menyimpan ke serial/CSV.
 *
 * Untuk Raspberry Pi: gunakan gateway_rpi.py di folder /gateway/rpi/
 *
 * KESELAMATAN: Lihat docs/SAFETY.md
 * Prototipe awal. Belum diuji di lapangan.
 */

#ifndef NATIVE_TEST
  #include <Arduino.h>
#endif

// ---------------------------------------------------------------
// Salin definisi paket dari node (share melalui header bersama)
// Di repositori nyata, packet.h/cpp sebaiknya jadi library bersama.
// ---------------------------------------------------------------

#define MW_MAGIC_0  0x4D
#define MW_MAGIC_1  0x57
#define MW_PACKET_SIZE 23

typedef struct __attribute__((packed)) {
    uint8_t  magic[2];
    uint8_t  node_id;
    uint8_t  fw_version;
    uint32_t seq_num;
    uint32_t timestamp_unix;
    uint16_t ch4_raw_mv;
    int16_t  temp_x10;
    uint16_t rh_x10;
    uint16_t vbat_mv;
    uint8_t  flags;
    uint16_t crc16;
} MWPacket;

// CRC16-CCITT
static uint16_t gw_crc16(const uint8_t *data, size_t len) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        for (int j = 0; j < 8; j++) {
            crc = (crc & 0x8000) ? ((crc << 1) ^ 0x1021) : (crc << 1);
        }
    }
    return crc;
}

// Pelacak seq_num per node untuk deteksi paket hilang
static uint32_t last_seq[256] = {0};
static bool     first_pkt[256];

void setup() {
    memset(first_pkt, true, sizeof(first_pkt));

#ifndef NATIVE_TEST
    Serial.begin(115200);
    delay(200);
    Serial.println(F("=== MethaneWatch Gateway ==="));
    Serial.println(F("Prototipe awal. Belum diuji di lapangan."));

    #if SIM_MODE == 1
    Serial.println(F("[SIMULASI] Mode simulasi: mencetak paket simulasi ke Serial."));
    // Dalam mode simulasi, cetak beberapa paket palsu lalu berhenti
    // Ini memungkinkan pengujian logika parsing tanpa hardware LoRa.
    for (int i = 0; i < 5; i++) {
        // Buat paket palsu
        MWPacket fake;
        memset(&fake, 0, sizeof(fake));
        fake.magic[0]       = MW_MAGIC_0;
        fake.magic[1]       = MW_MAGIC_1;
        fake.node_id        = 1;
        fake.fw_version     = 0x01;
        fake.seq_num        = (uint32_t)i;
        fake.timestamp_unix = 1730000000UL + i * 900;
        fake.ch4_raw_mv     = (uint16_t)(1200 + i * 50);
        fake.temp_x10       = (int16_t)(275 + i);
        fake.rh_x10         = (uint16_t)(700 - i * 2);
        fake.vbat_mv        = (uint16_t)(4100 - i * 10);
        fake.flags          = 0x07;
        fake.crc16 = gw_crc16((const uint8_t*)&fake, sizeof(MWPacket) - 2);

        // Validasi dan cetak
        bool crc_ok = (gw_crc16((const uint8_t*)&fake, sizeof(MWPacket) - 2) == fake.crc16);

        // Deteksi paket hilang
        uint8_t nid = fake.node_id;
        int32_t missing = 0;
        if (!first_pkt[nid]) {
            int32_t expected = (int32_t)(last_seq[nid] + 1);
            missing = (int32_t)fake.seq_num - expected;
            if (missing < 0) missing = 0;
        }
        first_pkt[nid]  = false;
        last_seq[nid]   = fake.seq_num;

        // Output CSV ke Serial (untuk capture oleh RPi atau PC)
        Serial.print(F("[SIMULASI] node="));
        Serial.print(fake.node_id);
        Serial.print(F(",seq="));
        Serial.print(fake.seq_num);
        Serial.print(F(",ts="));
        Serial.print(fake.timestamp_unix);
        Serial.print(F(",ch4_mv="));
        Serial.print(fake.ch4_raw_mv);
        Serial.print(F(",temp="));
        Serial.print(fake.temp_x10 / 10.0f, 1);
        Serial.print(F(",rh="));
        Serial.print(fake.rh_x10 / 10.0f, 1);
        Serial.print(F(",vbat="));
        Serial.print(fake.vbat_mv);
        Serial.print(F(",crc_ok="));
        Serial.print(crc_ok ? 1 : 0);
        Serial.print(F(",missing_pkts="));
        Serial.println(missing);

        delay(500);
    }
    Serial.println(F("[SIMULASI] Selesai. Untuk gateway nyata, gunakan mode SIM_MODE=0 + hardware LoRa."));
    #endif  // SIM_MODE
#endif  // !NATIVE_TEST
}

void loop() {
#ifndef NATIVE_TEST
  #if SIM_MODE == 0
    // Terima paket LoRa
    // [Verifikasi: tambahkan inisialisasi LoRa dan handler penerimaan di sini]
    // Contoh implementasi menggunakan library LoRa.h:
    //
    // int pkt_size = LoRa.parsePacket();
    // if (pkt_size == MW_PACKET_SIZE) {
    //     uint8_t buf[MW_PACKET_SIZE];
    //     for (int i = 0; i < pkt_size; i++) buf[i] = LoRa.read();
    //     MWPacket *pkt = (MWPacket*)buf;
    //     bool crc_ok = (gw_crc16(buf, MW_PACKET_SIZE - 2) == pkt->crc16);
    //     // ... simpan ke SQLite/CSV via Serial ke RPi atau SD card
    // }
    delay(10);
  #endif
#endif
}
