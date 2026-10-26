"""
anomaly.py – Modul Deteksi Anomali
=====================================
Mendeteksi tiga jenis anomali:
1. Lonjakan (spike): nilai jauh di luar distribusi normal jendela bergerak.
2. Sensor macet (stuck): varians nyaris nol dalam jendela bergerak.
3. Drift: pembacaan satu node menyimpang konsisten dari node tetangga.

CATATAN:
- Threshold dan parameter adalah ASUMSI awal. [Verifikasi dengan data lapangan]
- Prototipe awal. Belum diuji di lapangan.
- Semua nilai bersifat asumsi sampai diverifikasi.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from numpy.typing import NDArray


# ------------------------------------------------------------------
# Struktur hasil anomali
# ------------------------------------------------------------------

@dataclass
class AnomalyRecord:
    """Satu kejadian anomali yang terdeteksi."""
    node_id: int
    seq: int
    timestamp_utc: str
    anomaly_type: str          # "spike" | "stuck" | "drift" | "ok"
    reason: str                # Penjelasan terbaca manusia
    value_ppm: float
    z_score: Optional[float] = None
    window_std: Optional[float] = None
    neighbor_delta_ppm: Optional[float] = None


# ------------------------------------------------------------------
# Detektor utama
# ------------------------------------------------------------------

class AnomalyDetector:
    """
    Detektor anomali berbasis statistik untuk data pembacaan CH4.

    Semua parameter threshold adalah ASUMSI awal.
    Nilai nyata harus dikalibrasi dari data baseline lapangan. [Verifikasi]
    """

    def __init__(
        self,
        window_size: int = 12,
        spike_z_threshold: float = 3.5,
        stuck_variance_threshold: float = 0.01,
        stuck_min_window: int = 5,
        drift_threshold_ppm: float = 100.0,
        drift_min_windows: int = 4,
    ):
        """
        Parameters
        ----------
        window_size : int
            Ukuran jendela bergerak (jumlah sampel). [Verifikasi]
        spike_z_threshold : float
            Z-score minimum untuk menandai lonjakan. [Verifikasi]
        stuck_variance_threshold : float
            Varians maksimum untuk menganggap sensor macet (ppm²). [Verifikasi]
        stuck_min_window : int
            Jumlah sampel berturut-turut dengan varians rendah sebelum ditandai stuck.
        drift_threshold_ppm : float
            Selisih absolut maksimum antara satu node dan median tetangga (ppm). [Verifikasi]
        drift_min_windows : int
            Jumlah jendela berturut-turut di atas threshold sebelum ditandai drift.
        """
        self.window_size             = window_size
        self.spike_z_threshold       = spike_z_threshold
        self.stuck_variance_threshold = stuck_variance_threshold
        self.stuck_min_window        = stuck_min_window
        self.drift_threshold_ppm     = drift_threshold_ppm
        self.drift_min_windows       = drift_min_windows

    # ------------------------------------------------------------------ spike

    def detect_spikes(
        self, values: NDArray[np.float64], node_id: int,
        timestamps: List[str], seqs: List[int],
    ) -> List[AnomalyRecord]:
        """
        Deteksi lonjakan menggunakan z-score pada jendela bergerak.

        Z = (x_i - mean_window) / std_window
        Jika |Z| > spike_z_threshold → tandai sebagai spike.
        """
        records: List[AnomalyRecord] = []
        n = len(values)
        w = self.window_size

        for i in range(n):
            start = max(0, i - w)
            window = values[start:i + 1]
            if len(window) < 3:
                continue  # Terlalu sedikit data untuk z-score bermakna
            mu  = np.mean(window)
            std = np.std(window, ddof=1)
            if std < 1e-6:
                continue  # Hindari pembagian nol
            z = (values[i] - mu) / std
            if abs(z) > self.spike_z_threshold:
                records.append(AnomalyRecord(
                    node_id=node_id,
                    seq=seqs[i],
                    timestamp_utc=timestamps[i],
                    anomaly_type="spike",
                    reason=(
                        f"Z-score={z:.2f} melebihi threshold {self.spike_z_threshold} "
                        f"(window={w} sampel, mean={mu:.1f}, std={std:.1f} ppm)"
                    ),
                    value_ppm=float(values[i]),
                    z_score=round(float(z), 4),
                    window_std=round(float(std), 4),
                ))
        return records

    # ------------------------------------------------------------------ stuck

    def detect_stuck(
        self, values: NDArray[np.float64], node_id: int,
        timestamps: List[str], seqs: List[int],
    ) -> List[AnomalyRecord]:
        """
        Deteksi sensor macet: varians jendela bergerak mendekati nol selama
        beberapa jendela berturut-turut.
        """
        records: List[AnomalyRecord] = []
        n = len(values)
        w = self.stuck_min_window
        stuck_counter = 0

        for i in range(n):
            start = max(0, i - w + 1)
            window = values[start:i + 1]
            if len(window) < w:
                stuck_counter = 0
                continue
            var = float(np.var(window, ddof=0))
            if var <= self.stuck_variance_threshold:
                stuck_counter += 1
                if stuck_counter >= self.stuck_min_window:
                    records.append(AnomalyRecord(
                        node_id=node_id,
                        seq=seqs[i],
                        timestamp_utc=timestamps[i],
                        anomaly_type="stuck",
                        reason=(
                            f"Varians={var:.4f} ppm² di bawah threshold "
                            f"{self.stuck_variance_threshold} ppm² selama "
                            f"{stuck_counter} sampel. Sensor mungkin macet."
                        ),
                        value_ppm=float(values[i]),
                        window_std=round(float(np.sqrt(var)), 6),
                    ))
            else:
                stuck_counter = 0

        return records

    # ------------------------------------------------------------------ drift

    def detect_drift(
        self,
        node_data: Dict[int, NDArray[np.float64]],
        seqs_per_node: Dict[int, List[int]],
        timestamps_per_node: Dict[int, List[str]],
        target_node_id: int,
    ) -> List[AnomalyRecord]:
        """
        Deteksi drift: pembacaan satu node menyimpang konsisten dari median
        node-node tetangga.

        Hanya menggunakan data dari titik waktu yang sama (seq yang sama).
        """
        records: List[AnomalyRecord] = []

        if target_node_id not in node_data or len(node_data) < 2:
            return records

        target_vals = node_data[target_node_id]
        target_seqs = seqs_per_node[target_node_id]
        target_ts   = timestamps_per_node[target_node_id]
        neighbor_ids = [nid for nid in node_data if nid != target_node_id]

        drift_counter = 0
        w = self.window_size

        for i, (seq, ts) in enumerate(zip(target_seqs, target_ts)):
            neighbor_vals_at_seq = []
            for nid in neighbor_ids:
                nseqs = seqs_per_node[nid]
                if seq in nseqs:
                    idx = nseqs.index(seq)
                    neighbor_vals_at_seq.append(node_data[nid][idx])

            if not neighbor_vals_at_seq:
                drift_counter = 0
                continue

            neighbor_median = float(np.median(neighbor_vals_at_seq))
            delta = float(target_vals[i]) - neighbor_median

            if abs(delta) > self.drift_threshold_ppm:
                drift_counter += 1
                if drift_counter >= self.drift_min_windows:
                    records.append(AnomalyRecord(
                        node_id=target_node_id,
                        seq=seq,
                        timestamp_utc=ts,
                        anomaly_type="drift",
                        reason=(
                            f"Selisih dari median tetangga = {delta:+.1f} ppm "
                            f"(threshold: ±{self.drift_threshold_ppm} ppm) "
                            f"selama {drift_counter} sampel berturut-turut."
                        ),
                        value_ppm=float(target_vals[i]),
                        neighbor_delta_ppm=round(delta, 2),
                    ))
            else:
                drift_counter = 0

        return records

    # ------------------------------------------------------------------ unified API

    def run_all(
        self,
        df: pd.DataFrame,
        value_col: str = "ch4_corrected_ppm",
        node_col: str = "node_id",
        seq_col: str = "seq",
        ts_col: str = "timestamp_utc",
    ) -> pd.DataFrame:
        """
        Jalankan semua detektor pada DataFrame dan kembalikan baris anomali.

        Parameters
        ----------
        df : DataFrame
            Data sensor. Harus memiliki kolom: node_id, seq, timestamp_utc,
            dan kolom nilai (default: ch4_corrected_ppm).

        Returns
        -------
        DataFrame berisi semua anomali yang terdeteksi.
        """
        all_records: List[AnomalyRecord] = []

        # Kelompokkan per node
        node_arrays: Dict[int, NDArray] = {}
        seqs_dict:   Dict[int, List[int]] = {}
        ts_dict:     Dict[int, List[str]] = {}

        for node_id, grp in df.sort_values(seq_col).groupby(node_col):
            vals  = grp[value_col].to_numpy(dtype=np.float64)
            seqs  = grp[seq_col].tolist()
            times = grp[ts_col].tolist()

            node_arrays[node_id] = vals
            seqs_dict[node_id]   = seqs
            ts_dict[node_id]     = times

            all_records.extend(self.detect_spikes(vals, node_id, times, seqs))
            all_records.extend(self.detect_stuck(vals, node_id, times, seqs))

        # Drift (antar node)
        for node_id in node_arrays:
            all_records.extend(
                self.detect_drift(node_arrays, seqs_dict, ts_dict, node_id)
            )

        if not all_records:
            return pd.DataFrame(columns=[
                "node_id", "seq", "timestamp_utc", "anomaly_type",
                "reason", "value_ppm", "z_score", "window_std", "neighbor_delta_ppm"
            ])

        return pd.DataFrame([
            {
                "node_id":            r.node_id,
                "seq":                r.seq,
                "timestamp_utc":      r.timestamp_utc,
                "anomaly_type":       r.anomaly_type,
                "reason":             r.reason,
                "value_ppm":          r.value_ppm,
                "z_score":            r.z_score,
                "window_std":         r.window_std,
                "neighbor_delta_ppm": r.neighbor_delta_ppm,
            }
            for r in all_records
        ])
