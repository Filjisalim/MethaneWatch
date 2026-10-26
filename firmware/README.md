# MethaneWatch Firmware & Protokol Komunikasi

> **Firmware Node Sensor (ESP32) & Gateway LoRa (ESP32 / Raspberry Pi)**  
> Sub-sistem perangkat tertanam untuk proyek **MethaneWatch** (MAJU:ON University Track 2026-27).  
> *Status:* **Prototipe Awal &bull; Belum diuji di lapangan &bull; Nilai parameter bersifat asumsi sampai diverifikasi**

---

## 📡 1. Format Paket Data Biner (24 Bytes)

Komunikasi radio LoRa dioptimalkan menggunakan paket biner ringkas 24-byte untuk meminimalkan *Time-on-Air* (ToA), menghemat konsumsi energi baterai, serta mematuhi batas *duty cycle* spektrum frekuensi ISM:

| Offset (Byte) | Tipe Data | Bidang / Variabel | Keterangan |
|---|---|---|---|
| `0..1` | `uint16_t` | `magic_bytes` | Pengenal protokol: `0x4D57` ("MW") |
| `2` | `uint8_t` | `protocol_version`| Versi protokol: `0x01` |
| `3` | `uint8_t` | `node_id` | Identitas node (1 - 254) |
| `4..7` | `uint32_t` | `timestamp` | Waktu Unix epoch (detik) atau counter RTC |
| `8..9` | `uint16_t` | `sequence_number` | Nomor urut paket (deteksi paket hilang) |
| `10..11` | `int16_t` | `temperature_c_x100` | Suhu udara (°C × 100), misal: 2850 = 28.50°C |
| `12..13` | `uint16_t` | `humidity_pct_x100` | Kelembapan relatif (%RH × 100) |
| `14..15` | `uint16_t` | `ch4_raw_adc` | Pembacaan ADC mentah MQ-4 (0 - 4095) |
| `16..17` | `uint16_t` | `ch4_ppm_approx` | Estimasi awal konsentrasi metana (ppm) |
| `18..19` | `uint16_t` | `battery_mv` | Tegangan baterai Li-ion (mV) |
| `20` | `uint8_t` | `battery_soc_pct` | Estimasi kapasitas baterai (0 - 100%) |
| `21` | `uint8_t` | `status_flags` | Flag status bitmask (bit 0: sensor warm, bit 1: low bat, bit 2: anomaly, bit 3: sim mode) |
| `22..23` | `uint16_t` | `crc16` | Checksum CRC16-CCITT (Polinom: `0x1021`, Init: `0xFFFF`) |

---

## 🔄 2. Siklus Kerja Node Sensor (ESP32 Deep Sleep)

```
       ┌────────────────────────────────────────────────────────┐
       │               ESP32 Masuk Deep Sleep                   │
       │        (Periode tidur standar: 5 - 15 menit)           │
       └───────────────────────────┬────────────────────────────┘
                                   │
                           Timer RTC Bangun
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │   Nyalakan Daya Sensor MQ-4 & Pemanasan (Warmup)       │
       │   [Verifikasi waktu warmup: hemat energi vs akurasi]   │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │       Pengambilan Sampel Sensor & Filter Median        │
       │     • Suhu & Kelembapan (BME280 via I²C)               │
       │     • Gas Metana CH4 (MQ-4 via ADC + Multi-sampling)   │
       │     • Tegangan Baterai (ADC Voltage Divider)           │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │   Penyusunan Paket Biner 24-Byte & Kalkulasi CRC16     │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             Transmisi Paket via LoRa                   │
       │          (Modul SX1276 / SX1278 SPI)                   │
       └───────────────────────────┬────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
              Sukses│                             │Gagal
                    ▼                             ▼
       ┌────────────────────────┐    ┌────────────────────────┐
       │ Matikan daya periferik │    │ Simpan ke buffer RTC / │
       │ dan kembali Deep Sleep │    │ SPIFFS untuk re-trans  │
       └────────────────────────┘    └────────────────────────┘
```

---

## 🗄️ 3. LoRa Gateway (Offline-First Architecture)

Gateway dirancang dengan prinsip **offline-first**, memastikan data tidak hilang meskipun jaringan seluler/internet di area TPA terputus:

1. **Gateway ESP32 (`firmware/gateway/src/main.cpp`):**
   - Menerima paket via modul LoRa SX1276/SX1278.
   - Memvalidasi CRC16; membuang paket yang korup.
   - Melacak `sequence_number` tiap `node_id` untuk mencatat tingkat kehilangan paket (*packet loss rate*).
   - Mengeluarkan data terurai via UART Serial dalam format CSV ramah parser.

2. **Gateway Raspberry Pi (`firmware/gateway/rpi/gateway_rpi.py`):**
   - Membaca aliran serial dari bridge ESP32 (atau SPI LoRa HAT).
   - Menyimpan seluruh transaksi secara atomik ke database relasional lokal **SQLite** (`gateway.db`) dan berkas harian **CSV**.
   - Dilengkapi *MQTT publisher* otomatis yang aktif bila koneksi internet/WiFi tersedia.
   - Mendukung mode pengujian sintetis (`--sim`) tanpa perangkat keras.

---

## 🛠️ 4. Panduan Kompilasi & Pengujian

### Prasyarat
- [PlatformIO Core (CLI)](https://platformio.org/) atau ekstensi PlatformIO di VS Code.
- Toolchain C++ / GCC (untuk menjalankan `pio test -e native` di Windows/Linux).

### Kompilasi & Testing Node
```bash
cd firmware/node

# 1. Jalankan unit test native di PC (validasi CRC16 & packing):
pio test -e native

# 2. Kompilasi firmware simulasi untuk ESP32:
pio run -e esp32_sim

# 3. Flash firmware ke modul ESP32 fisik via kabel USB:
pio run -e esp32_hw -t upload
```

### Menjalankan Gateway Raspberry Pi
```bash
cd firmware/gateway/rpi

# Jalankan dalam mode simulasi:
python gateway_rpi.py --sim --db test_gateway.db --csv-dir ./logs

# Jalankan dengan koneksi serial hardware ESP32:
python gateway_rpi.py --port /dev/ttyUSB0 --baud 115200 --db tpa_gateway.db
```
