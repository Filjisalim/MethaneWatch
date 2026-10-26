#!/usr/bin/env python3
"""
gateway_rpi.py – Gateway MethaneWatch untuk Raspberry Pi
==========================================================
Menerima paket LoRa dari node (via serial ESP32 atau SX127x langsung),
memvalidasi CRC, menyimpan ke SQLite, dan meneruskan ke MQTT (opsional).

Offline-first: semua data disimpan lokal dulu. MQTT opsional.

KESELAMATAN: Lihat docs/SAFETY.md
Prototipe awal. Belum diuji di lapangan.
Semua nilai bersifat asumsi sampai diverifikasi.

Penggunaan:
    python gateway_rpi.py [--port /dev/ttyUSB0] [--db gateway.db] [--mqtt-host localhost]

Dependensi:
    pip install pyserial paho-mqtt
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import signal
import sqlite3
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

# ---------------------------------------------------------------
# Logging
# ---------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("mw-gateway")

# ---------------------------------------------------------------
# Konstanta format paket (harus sinkron dengan packet.h node)
# ---------------------------------------------------------------
MW_MAGIC     = b"\x4D\x57"
MW_PKT_SIZE  = 23
MW_PKT_FMT   = "<2sBBI I HhH H B H"
# Field: magic(2), node_id(1), fw_version(1), seq_num(4),
#        timestamp(4), ch4_raw_mv(2), temp_x10(2s), rh_x10(2),
#        vbat_mv(2), flags(1), crc16(2)

FLAG_SIM_MODE   = 0x01
FLAG_WARMUP_OK  = 0x02
FLAG_BME_OK     = 0x04
FLAG_LORA_RETRY = 0x08


# ---------------------------------------------------------------
# CRC16-CCITT (Python mirror dari implementasi C)
# ---------------------------------------------------------------

def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if (crc & 0x8000) else (crc << 1)
        crc &= 0xFFFF
    return crc


# ---------------------------------------------------------------
# Parsing paket
# ---------------------------------------------------------------

def parse_packet(raw: bytes) -> Optional[dict]:
    """
    Parse paket biner MethaneWatch.

    Returns dict dengan semua field, atau None jika invalid.
    """
    if len(raw) != MW_PKT_SIZE:
        log.warning("Ukuran paket salah: %d byte (harapan: %d)", len(raw), MW_PKT_SIZE)
        return None

    if raw[:2] != MW_MAGIC:
        log.warning("Magic bytes tidak cocok: %s", raw[:2].hex())
        return None

    # Verifikasi CRC
    computed_crc = crc16_ccitt(raw[:-2])
    recv_crc     = struct.unpack_from("<H", raw, MW_PKT_SIZE - 2)[0]
    if computed_crc != recv_crc:
        log.warning("CRC gagal: dihitung=0x%04X diterima=0x%04X", computed_crc, recv_crc)
        return None

    try:
        fields = struct.unpack(MW_PKT_FMT, raw)
    except struct.error as e:
        log.error("Parse struct gagal: %s", e)
        return None

    magic, node_id, fw_ver, seq_num, ts, ch4_mv, temp_x10, rh_x10, vbat_mv, flags, crc16 = fields

    return {
        "node_id":         node_id,
        "fw_version":      fw_ver,
        "seq_num":         seq_num,
        "timestamp_unix":  ts,
        "timestamp_utc":   datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        "ch4_raw_mv":      ch4_mv,
        "temp_c":          round(temp_x10 / 10.0, 1),
        "rh_pct":          round(rh_x10 / 10.0, 1),
        "vbat_mv":         vbat_mv,
        "flags":           flags,
        "sim_mode":        bool(flags & FLAG_SIM_MODE),
        "warmup_ok":       bool(flags & FLAG_WARMUP_OK),
        "bme_ok":          bool(flags & FLAG_BME_OK),
        "lora_retry":      bool(flags & FLAG_LORA_RETRY),
        "crc16":           crc16,
        "received_at_utc": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------
# Storage (SQLite + CSV)
# ---------------------------------------------------------------

class PacketStorage:
    """Menyimpan paket ke SQLite dan CSV. Offline-first."""

    def __init__(self, db_path: str = "gateway.db", csv_path: str = "gateway_data.csv"):
        self.db_path  = db_path
        self.csv_path = csv_path
        self._init_db()
        self._init_csv()

    def _init_db(self) -> None:
        con = sqlite3.connect(self.db_path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS packets (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id         INTEGER NOT NULL,
                fw_version      INTEGER,
                seq_num         INTEGER NOT NULL,
                timestamp_unix  INTEGER,
                timestamp_utc   TEXT,
                ch4_raw_mv      INTEGER,
                temp_c          REAL,
                rh_pct          REAL,
                vbat_mv         INTEGER,
                flags           INTEGER,
                sim_mode        INTEGER,
                warmup_ok       INTEGER,
                bme_ok          INTEGER,
                lora_retry      INTEGER,
                received_at_utc TEXT,
                UNIQUE(node_id, seq_num)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS missing_packets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id     INTEGER,
                expected_seq INTEGER,
                detected_at TEXT
            )
        """)
        con.commit()
        con.close()

    def _init_csv(self) -> None:
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                f.write("# MethaneWatch Gateway Data\n")
                f.write("# Prototipe awal. Belum diuji di lapangan.\n")
                w = csv.DictWriter(f, fieldnames=[
                    "node_id","fw_version","seq_num","timestamp_unix","timestamp_utc",
                    "ch4_raw_mv","temp_c","rh_pct","vbat_mv","flags",
                    "sim_mode","warmup_ok","bme_ok","lora_retry","received_at_utc"
                ])
                w.writeheader()

    def save(self, pkt: dict) -> bool:
        """Simpan ke SQLite (primary) dan CSV (backup). Return True jika berhasil."""
        try:
            con = sqlite3.connect(self.db_path)
            con.execute("""
                INSERT OR IGNORE INTO packets
                (node_id, fw_version, seq_num, timestamp_unix, timestamp_utc,
                 ch4_raw_mv, temp_c, rh_pct, vbat_mv, flags,
                 sim_mode, warmup_ok, bme_ok, lora_retry, received_at_utc)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                pkt["node_id"], pkt["fw_version"], pkt["seq_num"],
                pkt["timestamp_unix"], pkt["timestamp_utc"],
                pkt["ch4_raw_mv"], pkt["temp_c"], pkt["rh_pct"],
                pkt["vbat_mv"], pkt["flags"],
                int(pkt["sim_mode"]), int(pkt["warmup_ok"]),
                int(pkt["bme_ok"]), int(pkt["lora_retry"]),
                pkt["received_at_utc"],
            ))
            con.commit()
            con.close()

            # Juga tulis ke CSV
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=[
                    "node_id","fw_version","seq_num","timestamp_unix","timestamp_utc",
                    "ch4_raw_mv","temp_c","rh_pct","vbat_mv","flags",
                    "sim_mode","warmup_ok","bme_ok","lora_retry","received_at_utc"
                ])
                w.writerow({k: pkt[k] for k in w.fieldnames})

            return True
        except Exception as e:
            log.error("Gagal menyimpan paket: %s", e)
            return False

    def record_missing(self, node_id: int, expected_seq: int) -> None:
        try:
            con = sqlite3.connect(self.db_path)
            con.execute(
                "INSERT INTO missing_packets (node_id, expected_seq, detected_at) VALUES (?,?,?)",
                (node_id, expected_seq, datetime.now(timezone.utc).isoformat())
            )
            con.commit()
            con.close()
        except Exception as e:
            log.error("Gagal menyimpan info paket hilang: %s", e)


# ---------------------------------------------------------------
# Deteksi paket hilang
# ---------------------------------------------------------------

class SequenceTracker:
    """Melacak seq_num per node untuk mendeteksi paket hilang."""

    def __init__(self):
        self._last: dict[int, int] = {}

    def check(self, node_id: int, seq_num: int) -> list[int]:
        """Return daftar seq_num yang hilang antara last+1 dan seq_num-1."""
        if node_id not in self._last:
            self._last[node_id] = seq_num
            return []
        expected = self._last[node_id] + 1
        missing  = list(range(expected, seq_num))
        self._last[node_id] = seq_num
        return missing


# ---------------------------------------------------------------
# MQTT Forwarder (opsional)
# ---------------------------------------------------------------

class MQTTForwarder:
    """Teruskan paket ke MQTT broker. Opsional dan gracefully skip jika tidak tersedia."""

    def __init__(self, host: str, port: int = 1883, topic_prefix: str = "methanewatch"):
        self.host         = host
        self.port         = port
        self.topic_prefix = topic_prefix
        self._client      = None
        self._try_connect()

    def _try_connect(self) -> None:
        try:
            import paho.mqtt.client as mqtt  # type: ignore
            self._client = mqtt.Client()
            self._client.connect(self.host, self.port, keepalive=60)
            self._client.loop_start()
            log.info("MQTT terhubung ke %s:%d", self.host, self.port)
        except ImportError:
            log.warning("paho-mqtt tidak tersedia. Terusan MQTT dinonaktifkan.")
            self._client = None
        except Exception as e:
            log.warning("Koneksi MQTT gagal: %s. Terusan MQTT dinonaktifkan.", e)
            self._client = None

    def publish(self, pkt: dict) -> None:
        if self._client is None:
            return
        topic   = f"{self.topic_prefix}/node/{pkt['node_id']}/data"
        payload = json.dumps(pkt)
        try:
            self._client.publish(topic, payload, qos=1, retain=False)
        except Exception as e:
            log.warning("MQTT publish gagal: %s", e)


# ---------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------

def run_gateway(
    port: Optional[str],
    db_path: str,
    csv_path: str,
    mqtt_host: Optional[str],
    sim_mode: bool,
) -> None:
    storage  = PacketStorage(db_path=db_path, csv_path=csv_path)
    tracker  = SequenceTracker()
    forwarder: Optional[MQTTForwarder] = None
    if mqtt_host:
        forwarder = MQTTForwarder(host=mqtt_host)

    # Tangani Ctrl+C dengan bersih
    running = [True]
    def _stop(sig, frame):
        log.info("Menghentikan gateway...")
        running[0] = False
    signal.signal(signal.SIGINT, _stop)

    if sim_mode:
        log.warning("[SIMULASI] Mode simulasi aktif. Data BUKAN dari LoRa nyata.")
        # Buat beberapa paket palsu
        from methanewatch.sim_data import SimDataGenerator, DEFAULT_NODES
        gen = SimDataGenerator(seed=42)
        records = gen.generate_normal(n_samples=10)
        for r in records:
            pkt = {
                "node_id":         r.node_id,
                "fw_version":      1,
                "seq_num":         r.seq,
                "timestamp_unix":  int(time.time()),
                "timestamp_utc":   r.timestamp_utc,
                "ch4_raw_mv":      int(r.ch4_raw_ppm * 2.0),  # estimasi kasar [Verifikasi]
                "temp_c":          r.temp_c,
                "rh_pct":          r.rh_pct,
                "vbat_mv":         int(r.vbat_v * 1000),
                "flags":           0x07,
                "sim_mode":        True,
                "warmup_ok":       True,
                "bme_ok":          True,
                "lora_retry":      False,
                "received_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            missing = tracker.check(pkt["node_id"], pkt["seq_num"])
            for m in missing:
                log.warning("Paket hilang: node=%d seq=%d", pkt["node_id"], m)
                storage.record_missing(pkt["node_id"], m)
            storage.save(pkt)
            if forwarder:
                forwarder.publish(pkt)
            log.info("Disimpan [SIMULASI]: node=%d seq=%d ch4_mv=%d",
                     pkt["node_id"], pkt["seq_num"], pkt["ch4_raw_mv"])
        log.info("[SIMULASI] Selesai. Periksa %s dan %s.", db_path, csv_path)
        return

    # Mode hardware: baca dari serial
    if port is None:
        log.error("Port serial diperlukan di mode hardware. Gunakan --port /dev/ttyUSB0")
        sys.exit(1)

    try:
        import serial  # type: ignore
    except ImportError:
        log.error("pyserial tidak tersedia. Install: pip install pyserial")
        sys.exit(1)

    log.info("Membuka port serial %s ...", port)
    try:
        ser = serial.Serial(port, 115200, timeout=2.0)
    except serial.SerialException as e:
        log.error("Gagal membuka port serial: %s", e)
        sys.exit(1)

    log.info("Gateway aktif. Menunggu paket LoRa via serial...")
    buf = bytearray()

    while running[0]:
        try:
            data = ser.read(MW_PKT_SIZE)
            if not data:
                continue
            buf.extend(data)

            # Cari magic bytes dan ekstrak paket
            while len(buf) >= MW_PKT_SIZE:
                idx = buf.find(bytes(MW_MAGIC))
                if idx < 0:
                    buf.clear()
                    break
                if idx > 0:
                    buf = buf[idx:]
                if len(buf) < MW_PKT_SIZE:
                    break

                raw = bytes(buf[:MW_PKT_SIZE])
                buf = buf[MW_PKT_SIZE:]
                pkt = parse_packet(raw)

                if pkt is None:
                    log.warning("Paket tidak valid dibuang.")
                    continue

                missing = tracker.check(pkt["node_id"], pkt["seq_num"])
                for m in missing:
                    log.warning("Paket hilang: node=%d seq=%d", pkt["node_id"], m)
                    storage.record_missing(pkt["node_id"], m)

                storage.save(pkt)
                if forwarder:
                    forwarder.publish(pkt)

                sim_tag = " [SIMULASI]" if pkt["sim_mode"] else ""
                log.info("Diterima%s: node=%d seq=%d ch4_mv=%d temp=%.1f rh=%.1f vbat=%d",
                         sim_tag, pkt["node_id"], pkt["seq_num"],
                         pkt["ch4_raw_mv"], pkt["temp_c"], pkt["rh_pct"], pkt["vbat_mv"])

        except Exception as e:
            log.error("Error loop: %s", e)
            time.sleep(1.0)

    ser.close()
    log.info("Gateway berhenti.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MethaneWatch Gateway – Prototipe awal, belum diuji di lapangan."
    )
    parser.add_argument("--port",      default=None,         help="Port serial (/dev/ttyUSB0). Opsional jika --sim.")
    parser.add_argument("--db",        default="gateway.db", help="Path file SQLite.")
    parser.add_argument("--csv",       default="gateway_data.csv", help="Path file CSV backup.")
    parser.add_argument("--mqtt-host", default=None,         help="Host MQTT broker (opsional).")
    parser.add_argument("--sim",       action="store_true",  help="Mode simulasi (tanpa hardware).")
    args = parser.parse_args()

    run_gateway(
        port=args.port,
        db_path=args.db,
        csv_path=args.csv,
        mqtt_host=args.mqtt_host,
        sim_mode=args.sim,
    )


if __name__ == "__main__":
    main()
