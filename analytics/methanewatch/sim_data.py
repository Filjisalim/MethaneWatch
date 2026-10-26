"""
sim_data.py – Generator Data Simulasi Deterministik
=====================================================
PERINGATAN: Semua data yang dihasilkan modul ini adalah SIMULASI.
Bukan data lapangan nyata. Digunakan hanya untuk pengujian dan demonstrasi.

Prototipe awal. Belum diuji di lapangan.
Semua nilai bersifat asumsi sampai diverifikasi.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Iterator, List, Optional

import numpy as np

# ------------------------------------------------------------------
# Seed tetap untuk reprodusibilitas
# ------------------------------------------------------------------
DEFAULT_SEED = 42

# ------------------------------------------------------------------
# Konfigurasi skenario
# ------------------------------------------------------------------

@dataclass
class NodeConfig:
    """Konfigurasi satu node sensor (koordinat dan ID)."""
    node_id: int
    lat: float
    lon: float
    label: str = ""


# Koordinat fiktif – SIMULASI, bukan lokasi TPA Air Dingin yang sesungguhnya
DEFAULT_NODES: List[NodeConfig] = [
    NodeConfig(node_id=1, lat=-0.9550, lon=100.3520, label="zona_aktif"),
    NodeConfig(node_id=2, lat=-0.9570, lon=100.3545, label="zona_tengah"),
    NodeConfig(node_id=3, lat=-0.9590, lon=100.3510, label="batas_selatan"),
    NodeConfig(node_id=4, lat=-0.9535, lon=100.3560, label="dekat_permukiman"),
]


@dataclass
class SimRecord:
    """Satu baris data simulasi."""
    # Metadata
    scenario: str          # SIMULASI: normal | spike | stuck | drift
    node_id: int
    lat: float
    lon: float
    timestamp_utc: str
    seq: int

    # Pembacaan sensor (unit: ppm untuk CH4; °C; % RH; V)
    ch4_raw_ppm: float     # Pembacaan mentah sensor murah (SIMULASI)
    ch4_corrected_ppm: float  # Setelah koreksi (SIMULASI)
    temp_c: float
    rh_pct: float
    vbat_v: float
    rssi_dbm: int

    # Tanda kualitas
    anomaly_flag: str      # "" | "spike" | "stuck" | "drift"
    anomaly_reason: str


# ------------------------------------------------------------------
# Generator utama
# ------------------------------------------------------------------

class SimDataGenerator:
    """
    Generator data simulasi deterministik.

    Semua metode menghasilkan data berlabel 'SIMULASI'.
    Jangan menggunakan data ini sebagai acuan teknis atau klaim hasil.
    """

    def __init__(self, seed: int = DEFAULT_SEED):
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------ helpers

    def _base_timestamps(
        self,
        n_samples: int,
        interval_minutes: int = 15,
        start: Optional[datetime] = None,
    ) -> List[str]:
        """Buat daftar stempel waktu UTC."""
        if start is None:
            start = datetime(2026, 11, 1, 0, 0, 0, tzinfo=timezone.utc)
        ts = []
        for i in range(n_samples):
            t = start + timedelta(minutes=i * interval_minutes)
            ts.append(t.isoformat())
        return ts

    def _base_ch4(self, n: int, base_ppm: float = 350.0, noise_std: float = 15.0) -> np.ndarray:
        """Pola CH4 dasar: baseline + noise + tren harian sinusoidal (SIMULASI)."""
        t = np.linspace(0, 2 * np.pi, n)
        diurnal = 40.0 * np.sin(t)  # amplitudo diurnal fiktif
        noise = self.rng.normal(0, noise_std, n)
        return base_ppm + diurnal + noise

    def _base_env(self, n: int) -> tuple[np.ndarray, np.ndarray]:
        """Suhu (°C) dan kelembapan (%) dasar (SIMULASI)."""
        t = np.linspace(0, 2 * np.pi, n)
        temp = 28.0 + 5.0 * np.sin(t - 0.5) + self.rng.normal(0, 0.5, n)
        rh   = 75.0 - 8.0 * np.sin(t - 0.5) + self.rng.normal(0, 1.5, n)
        return temp, rh

    def _simple_correction(self, ch4_raw: np.ndarray, temp: np.ndarray, rh: np.ndarray) -> np.ndarray:
        """
        Koreksi linear sederhana (SIMULASI).
        ch4_corrected = ch4_raw - alpha*(temp - T_ref) - beta*(rh - RH_ref)

        Koefisien alpha dan beta adalah ASUMSI untuk tujuan simulasi.
        Nilai nyata harus dikalibrasi terhadap sensor referensi. [Verifikasi]
        """
        T_ref  = 25.0   # °C referensi
        RH_ref = 60.0   # % referensi
        alpha  = 2.5    # ppm/°C  – ASUMSI [Verifikasi]
        beta   = 0.8    # ppm/%RH – ASUMSI [Verifikasi]
        return ch4_raw - alpha * (temp - T_ref) - beta * (rh - RH_ref)

    def _vbat(self, n: int) -> np.ndarray:
        """Tegangan baterai yang perlahan turun (SIMULASI). [Verifikasi kurva baterai nyata]"""
        return np.linspace(4.10, 3.75, n) + self.rng.normal(0, 0.02, n)

    def _rssi(self, n: int, base: int = -75) -> np.ndarray:
        """RSSI (dBm) acak (SIMULASI)."""
        return (base + self.rng.integers(-10, 11, n)).astype(int)

    # ------------------------------------------------------------------ skenario

    def generate_normal(
        self,
        nodes: List[NodeConfig] = DEFAULT_NODES,
        n_samples: int = 96,   # 96 × 15 menit = 24 jam
        interval_minutes: int = 15,
    ) -> List[SimRecord]:
        """Skenario normal: semua node berfungsi baik (SIMULASI)."""
        records: List[SimRecord] = []
        timestamps = self._base_timestamps(n_samples, interval_minutes)

        for node in nodes:
            ch4_raw  = self._base_ch4(n_samples, base_ppm=300.0 + node.node_id * 30)
            temp, rh = self._base_env(n_samples)
            ch4_corr = self._simple_correction(ch4_raw, temp, rh)
            vbat     = self._vbat(n_samples)
            rssi     = self._rssi(n_samples)

            for i in range(n_samples):
                records.append(SimRecord(
                    scenario="SIMULASI:normal",
                    node_id=node.node_id,
                    lat=node.lat,
                    lon=node.lon,
                    timestamp_utc=timestamps[i],
                    seq=i,
                    ch4_raw_ppm=round(float(ch4_raw[i]), 2),
                    ch4_corrected_ppm=round(float(ch4_corr[i]), 2),
                    temp_c=round(float(temp[i]), 2),
                    rh_pct=round(float(rh[i]), 2),
                    vbat_v=round(float(vbat[i]), 3),
                    rssi_dbm=int(rssi[i]),
                    anomaly_flag="",
                    anomaly_reason="",
                ))

        return records

    def generate_spike(
        self,
        nodes: List[NodeConfig] = DEFAULT_NODES,
        n_samples: int = 96,
        interval_minutes: int = 15,
        spike_indices: Optional[List[int]] = None,
        spike_node_id: int = 1,
        spike_magnitude: float = 800.0,
    ) -> List[SimRecord]:
        """
        Skenario lonjakan: satu node mengalami lonjakan CH4 (SIMULASI).
        Digunakan untuk menguji modul deteksi anomali.
        """
        records = self.generate_normal(nodes, n_samples, interval_minutes)

        if spike_indices is None:
            spike_indices = [30, 31, 32]  # lonjakan pada sampel ke-30 s.d. 32

        for r in records:
            if r.node_id == spike_node_id and r.seq in spike_indices:
                r.ch4_raw_ppm = round(r.ch4_raw_ppm + spike_magnitude, 2)
                r.ch4_corrected_ppm = round(r.ch4_corrected_ppm + spike_magnitude, 2)
                r.anomaly_flag = "spike"
                r.anomaly_reason = f"Injected spike +{spike_magnitude} ppm at seq={r.seq} [SIMULASI]"
                r.scenario = "SIMULASI:spike"

        return records

    def generate_stuck(
        self,
        nodes: List[NodeConfig] = DEFAULT_NODES,
        n_samples: int = 96,
        interval_minutes: int = 15,
        stuck_node_id: int = 2,
        stuck_start: int = 40,
        stuck_end: int = 70,
    ) -> List[SimRecord]:
        """
        Skenario sensor macet: satu node mengirimkan nilai konstan (SIMULASI).
        Digunakan untuk menguji deteksi sensor stuck.
        """
        records = self.generate_normal(nodes, n_samples, interval_minutes)
        stuck_value: Optional[float] = None

        for r in records:
            if r.node_id == stuck_node_id and stuck_start <= r.seq <= stuck_end:
                if stuck_value is None:
                    stuck_value = r.ch4_raw_ppm
                r.ch4_raw_ppm = stuck_value
                r.ch4_corrected_ppm = stuck_value
                r.anomaly_flag = "stuck"
                r.anomaly_reason = f"Sensor stuck at {stuck_value} ppm from seq={stuck_start} [SIMULASI]"
                r.scenario = "SIMULASI:stuck"

        return records

    def generate_drift(
        self,
        nodes: List[NodeConfig] = DEFAULT_NODES,
        n_samples: int = 96,
        interval_minutes: int = 15,
        drift_node_id: int = 3,
        drift_start: int = 50,
        drift_rate_ppm_per_sample: float = 5.0,
    ) -> List[SimRecord]:
        """
        Skenario drift: satu node mengalami pergeseran pembacaan bertahap (SIMULASI).
        Digunakan untuk menguji deteksi drift.
        """
        records = self.generate_normal(nodes, n_samples, interval_minutes)

        for r in records:
            if r.node_id == drift_node_id and r.seq >= drift_start:
                offset = (r.seq - drift_start) * drift_rate_ppm_per_sample
                r.ch4_raw_ppm = round(r.ch4_raw_ppm + offset, 2)
                r.ch4_corrected_ppm = round(r.ch4_corrected_ppm + offset, 2)
                r.anomaly_flag = "drift"
                r.anomaly_reason = (
                    f"Simulated drift +{offset:.1f} ppm from seq={drift_start} "
                    f"(rate {drift_rate_ppm_per_sample} ppm/sample) [SIMULASI]"
                )
                r.scenario = "SIMULASI:drift"

        return records

    # ------------------------------------------------------------------ export

    @staticmethod
    def to_csv(records: List[SimRecord], filepath: str) -> None:
        """Tulis daftar SimRecord ke file CSV. File berlabel SIMULASI di baris pertama."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None

        header_comment = (
            "# PERINGATAN: FILE INI BERISI DATA SIMULASI.\n"
            "# Bukan data lapangan nyata. Digunakan hanya untuk pengujian.\n"
            "# Prototipe awal. Belum diuji di lapangan.\n"
        )

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            f.write(header_comment)
            if not records:
                return
            writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()))
            writer.writeheader()
            for r in records:
                writer.writerow(asdict(r))


# ------------------------------------------------------------------
# Entry point: buat semua file simulasi
# ------------------------------------------------------------------

def generate_all_sim_files(output_dir: str = "data") -> None:
    """Buat keempat file simulasi di direktori output."""
    gen = SimDataGenerator(seed=DEFAULT_SEED)

    scenarios = {
        "sim_normal.csv":  gen.generate_normal(),
        "sim_spike.csv":   gen.generate_spike(),
        "sim_stuck.csv":   gen.generate_stuck(),
        "sim_drift.csv":   gen.generate_drift(),
    }

    for filename, records in scenarios.items():
        path = os.path.join(output_dir, filename)
        SimDataGenerator.to_csv(records, path)
        print(f"[sim_data] Dibuat: {path} ({len(records)} baris) [SIMULASI]")


if __name__ == "__main__":
    generate_all_sim_files()
