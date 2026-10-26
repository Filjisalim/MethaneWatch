"""
generate_report.py – Skrip Laporan Markdown dari CSV
======================================================
Membaca satu file CSV data sensor dan menghasilkan laporan Markdown
yang mencakup: statistik ringkas, anomali terdeteksi, dan estimasi
potensi gas (ilustrasi).

Penggunaan:
    python generate_report.py <input_csv> [output_md]

Contoh:
    python generate_report.py ../../data/sim_normal.csv report.md

CATATAN:
- Input harus berformat CSV yang dihasilkan oleh sim_data.py atau
  data lapangan nyata dengan header yang sama.
- Jika dari data simulasi: semua nilai berlabel [SIMULASI].
- Prototipe awal. Belum diuji di lapangan.
"""

from __future__ import annotations

import argparse
import os
import sys
import warnings
from datetime import datetime

import pandas as pd

# Tambahkan path parent agar impor methanewatch bekerja
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from methanewatch.anomaly import AnomalyDetector
from methanewatch.estimation import GasEstimator, EstimationParams


def load_csv(filepath: str) -> pd.DataFrame:
    """Baca CSV, lewati baris komentar yang diawali '#'."""
    try:
        df = pd.read_csv(filepath, comment="#")
    except Exception as e:
        print(f"[ERROR] Gagal membaca {filepath}: {e}", file=sys.stderr)
        sys.exit(1)
    return df


def is_simulation(df: pd.DataFrame) -> bool:
    """Cek apakah data berlabel SIMULASI."""
    if "scenario" in df.columns:
        return df["scenario"].str.contains("SIMULASI", na=False).any()
    return False


def generate_report(df: pd.DataFrame, source_file: str) -> str:
    """
    Buat laporan Markdown dari DataFrame data sensor.

    Returns
    -------
    str : Isi laporan Markdown.
    """
    sim_label = "[SIMULASI]" if is_simulation(df) else "[DATA LAPANGAN]"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n_rows    = len(df)
    n_nodes   = df["node_id"].nunique() if "node_id" in df.columns else "?"

    # ------------------------------------------------------------------ header
    lines = [
        "# Laporan MethaneWatch",
        "",
        f"> **Status:** Prototipe awal. Belum diuji di lapangan. "
        f"Semua nilai bersifat asumsi sampai diverifikasi.",
        f"> **Sumber data:** `{os.path.basename(source_file)}` {sim_label}",
        f"> **Dibuat:** {timestamp}",
        f"> **Jumlah baris:** {n_rows} | **Jumlah node:** {n_nodes}",
        "",
        "---",
        "",
    ]

    # ------------------------------------------------------------------ statistik ringkas
    lines += [
        "## 1. Statistik Ringkas",
        "",
    ]

    value_col = "ch4_corrected_ppm" if "ch4_corrected_ppm" in df.columns else "ch4_raw_ppm"
    if value_col not in df.columns:
        lines.append("_Kolom CH4 tidak ditemukan di CSV._")
    else:
        label_note = f"{sim_label} – bukan data lapangan tervalidasi" if is_simulation(df) else ""
        stats = df.groupby("node_id")[value_col].agg(["mean", "std", "min", "max", "count"]).round(2)
        lines += [
            f"Kolom nilai: `{value_col}` {label_note}",
            "",
            "| Node ID | Rata-rata (ppm) | Std (ppm) | Min | Maks | Sampel |",
            "|---------|-----------------|-----------|-----|------|--------|",
        ]
        for node_id, row in stats.iterrows():
            lines.append(
                f"| {node_id} | {row['mean']} | {row['std']} | "
                f"{row['min']} | {row['max']} | {int(row['count'])} |"
            )
        lines.append("")

    # ------------------------------------------------------------------ anomali
    lines += [
        "---",
        "",
        "## 2. Anomali Terdeteksi",
        "",
    ]

    if value_col in df.columns and "node_id" in df.columns and "seq" in df.columns:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            detector = AnomalyDetector()
            anomaly_df = detector.run_all(df, value_col=value_col)

        if anomaly_df.empty:
            lines.append("_Tidak ada anomali yang terdeteksi dengan parameter saat ini._")
        else:
            n_anomalies = len(anomaly_df)
            type_counts = anomaly_df["anomaly_type"].value_counts().to_dict()
            lines += [
                f"Total anomali terdeteksi: **{n_anomalies}**",
                "",
                "| Tipe | Jumlah |",
                "|------|--------|",
            ]
            for atype, count in type_counts.items():
                lines.append(f"| {atype} | {count} |")

            lines += [
                "",
                "Detail (10 pertama):",
                "",
                "| Node | Seq | Waktu | Tipe | Nilai (ppm) | Alasan |",
                "|------|-----|-------|------|-------------|--------|",
            ]
            for _, row in anomaly_df.head(10).iterrows():
                reason_short = str(row["reason"])[:80] + "…" if len(str(row["reason"])) > 80 else row["reason"]
                lines.append(
                    f"| {row['node_id']} | {row['seq']} | {row['timestamp_utc']} | "
                    f"**{row['anomaly_type']}** | {row['value_ppm']:.1f} | {reason_short} |"
                )
            lines.append("")
    else:
        lines.append("_Kolom yang diperlukan (node_id, seq, ch4_corrected_ppm) tidak ditemukan._")

    # ------------------------------------------------------------------ estimasi
    lines += [
        "---",
        "",
        "## 3. Estimasi Potensi Gas (ILUSTRASI)",
        "",
        "> ⚠️ Bagian ini adalah **ilustrasi** yang dihasilkan dari asumsi default.",
        "> BUKAN klaim hasil pengukuran. Ganti parameter dengan data nyata dari pengelola TPA.",
        "",
    ]

    avg_ch4 = df[value_col].mean() if value_col in df.columns else None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        estimator = GasEstimator()
        result = estimator.estimate(
            params=EstimationParams(),
            measured_avg_ch4_ppm=avg_ch4,
        )

    lines.append(GasEstimator.format_report(result))
    lines.append("")

    # ------------------------------------------------------------------ footer
    lines += [
        "---",
        "",
        "## 4. Catatan dan Keterbatasan",
        "",
        "- Laporan ini dibuat dari prototipe awal yang belum diuji di lapangan.",
        "- Semua threshold anomali dan koefisien koreksi adalah asumsi. [Verifikasi]",
        "- Estimasi potensi gas adalah ilustrasi – tidak untuk pengambilan keputusan.",
        "- Sistem ini BUKAN pengganti alat deteksi gas bersertifikat.",
        "- Lihat `docs/limitations.md` untuk daftar lengkap keterbatasan.",
        "",
        f"_Laporan dibuat oleh MethaneWatch Analytics v{_get_version()} – {timestamp}_",
    ]

    return "\n".join(lines)


def _get_version() -> str:
    try:
        from methanewatch import __version__
        return __version__
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MethaneWatch: Buat laporan Markdown dari file CSV data sensor."
    )
    parser.add_argument("input_csv", help="Path ke file CSV data sensor.")
    parser.add_argument(
        "output_md",
        nargs="?",
        default=None,
        help="Path file Markdown output. Default: <input_csv>.report.md",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_csv):
        print(f"[ERROR] File tidak ditemukan: {args.input_csv}", file=sys.stderr)
        sys.exit(1)

    output = args.output_md or (os.path.splitext(args.input_csv)[0] + ".report.md")

    df = load_csv(args.input_csv)
    report = generate_report(df, args.input_csv)

    with open(output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[generate_report] Laporan disimpan: {output}")


if __name__ == "__main__":
    main()
