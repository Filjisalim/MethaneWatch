"""
spatial.py – Modul Interpolasi Spasial
========================================
Menginterpolasi konsentrasi CH4 pada grid dari pembacaan titik node
menggunakan metode Inverse Distance Weighting (IDW).

CATATAN:
- IDW adalah estimasi, bukan ukuran langsung. Hasilnya tergantung konfigurasi
  node dan distribusi sumber emisi yang sebenarnya.
- Penambahan data arah angin dapat membantu memperbaiki estimasi, namun
  implementasinya masih bersifat percobaan.
- Prototipe awal. Belum diuji di lapangan.
- Semua nilai bersifat asumsi sampai diverifikasi.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from numpy.typing import NDArray


# ------------------------------------------------------------------
# Struktur hasil interpolasi
# ------------------------------------------------------------------

@dataclass
class SpatialGrid:
    """Grid hasil interpolasi IDW."""
    lat_grid: NDArray[np.float64]   # shape (rows, cols)
    lon_grid: NDArray[np.float64]   # shape (rows, cols)
    values: NDArray[np.float64]     # shape (rows, cols) – CH4 ppm
    resolution_deg: float
    power: float                    # pangkat IDW
    n_nodes: int
    timestamp_label: str
    warning: str = ""


# ------------------------------------------------------------------
# Interpolator IDW
# ------------------------------------------------------------------

class IDWInterpolator:
    """
    Interpolasi Inverse Distance Weighting (IDW) untuk konsentrasi CH4.

    Formula IDW:
        z(x) = Σ(w_i * z_i) / Σ(w_i)
        w_i  = 1 / d(x, x_i)^p

    di mana p = power parameter. Nilai p lebih besar membuat pengaruh
    titik jauh lebih kecil. Nilai default p=2 adalah konvensi umum.
    [Verifikasi: pilih p berdasarkan cross-validation dari data nyata]
    """

    def __init__(
        self,
        power: float = 2.0,
        resolution_deg: float = 0.0005,   # ~55 m di khatulistiwa [Verifikasi]
        grid_padding_deg: float = 0.001,
    ):
        """
        Parameters
        ----------
        power : float
            Pangkat IDW. [Verifikasi dengan data nyata]
        resolution_deg : float
            Resolusi grid dalam derajat. [Verifikasi kebutuhan resolusi nyata]
        grid_padding_deg : float
            Padding tambahan di sekeliling bounding box node.
        """
        self.power           = power
        self.resolution_deg  = resolution_deg
        self.grid_padding    = grid_padding_deg

    def interpolate(
        self,
        lats: NDArray[np.float64],
        lons: NDArray[np.float64],
        values: NDArray[np.float64],
        timestamp_label: str = "",
        wind_direction_deg: Optional[float] = None,
        wind_speed_mps: Optional[float] = None,
    ) -> SpatialGrid:
        """
        Lakukan interpolasi IDW dari data titik node.

        Parameters
        ----------
        lats : array
            Lintang node (derajat).
        lons : array
            Bujur node (derajat).
        values : array
            Nilai CH4 di setiap node (ppm).
        timestamp_label : str
            Label waktu untuk annotasi output.
        wind_direction_deg : float, optional
            Arah angin (derajat meteorologis, 0°=Utara, searah jarum jam).
            Jika disediakan, digunakan untuk anotasi peta saja (belum memengaruhi
            interpolasi). [Verifikasi: implementasi adveksi lebih lanjut diperlukan]
        wind_speed_mps : float, optional
            Kecepatan angin (m/s). Lihat catatan di atas.

        Returns
        -------
        SpatialGrid
        """
        lats   = np.asarray(lats,   dtype=np.float64)
        lons   = np.asarray(lons,   dtype=np.float64)
        values = np.asarray(values, dtype=np.float64)

        if len(lats) < 2:
            raise ValueError("Dibutuhkan minimal 2 node untuk interpolasi.")

        warn_str = ""
        if len(lats) < 3:
            warn_str = (
                "Hanya 2 node. Hasil interpolasi sangat tidak dapat diandalkan. "
                "Direkomendasikan minimal 4-6 node. [Verifikasi]"
            )
            warnings.warn(warn_str, UserWarning, stacklevel=2)

        if wind_direction_deg is not None:
            warn_str += (
                " Data angin tersedia tetapi belum digunakan dalam perhitungan IDW. "
                "Adveksi akan diimplementasikan di versi mendatang. [Verifikasi]"
            )

        # Buat grid
        lat_min = lats.min() - self.grid_padding
        lat_max = lats.max() + self.grid_padding
        lon_min = lons.min() - self.grid_padding
        lon_max = lons.max() + self.grid_padding

        lat_vec = np.arange(lat_min, lat_max, self.resolution_deg)
        lon_vec = np.arange(lon_min, lon_max, self.resolution_deg)
        lon_grid, lat_grid = np.meshgrid(lon_vec, lat_vec)

        # Hitung IDW
        shape = lat_grid.shape
        result = np.zeros(shape, dtype=np.float64)
        weight_sum = np.zeros(shape, dtype=np.float64)

        for lat_i, lon_i, val_i in zip(lats, lons, values):
            d = np.sqrt((lat_grid - lat_i)**2 + (lon_grid - lon_i)**2)
            # Hindari pembagian nol: jika titik grid tepat di atas node,
            # gunakan nilai node langsung.
            exact = d < 1e-9
            d_safe = np.where(exact, 1.0, d)
            w = 1.0 / (d_safe ** self.power)
            w = np.where(exact, 1e9, w)  # bobot sangat besar di titik node
            result     += w * val_i
            weight_sum += w

        interpolated = result / weight_sum

        return SpatialGrid(
            lat_grid=lat_grid,
            lon_grid=lon_grid,
            values=interpolated,
            resolution_deg=self.resolution_deg,
            power=self.power,
            n_nodes=len(lats),
            timestamp_label=timestamp_label,
            warning=warn_str.strip(),
        )

    # ------------------------------------------------------------------ export

    @staticmethod
    def to_csv(grid: SpatialGrid, filepath: str) -> None:
        """
        Ekspor grid interpolasi sebagai CSV flat.
        Format: lat, lon, ch4_ppm
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
        rows, cols = grid.lat_grid.shape
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# PERINGATAN: Nilai interpolasi IDW – estimasi, bukan ukuran langsung.\n")
            f.write("# Prototipe awal. Belum diuji di lapangan.\n")
            f.write(f"# Timestamp: {grid.timestamp_label}\n")
            f.write(f"# IDW power: {grid.power}, resolusi: {grid.resolution_deg}°\n")
            f.write("lat,lon,ch4_ppm_interpolated\n")
            for r in range(rows):
                for c in range(cols):
                    f.write(
                        f"{grid.lat_grid[r,c]:.6f},"
                        f"{grid.lon_grid[r,c]:.6f},"
                        f"{grid.values[r,c]:.2f}\n"
                    )

    @staticmethod
    def to_image(
        grid: SpatialGrid,
        filepath: str,
        node_lats: Optional[NDArray] = None,
        node_lons: Optional[NDArray] = None,
        node_values: Optional[NDArray] = None,
    ) -> None:
        """
        Ekspor grid interpolasi sebagai gambar PNG menggunakan matplotlib.

        Memerlukan matplotlib. Jika tidak tersedia, lewati dengan peringatan.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.colors as mcolors
        except ImportError:
            warnings.warn(
                "matplotlib tidak tersedia. Ekspor gambar dilewati. "
                "Install dengan: pip install matplotlib",
                ImportWarning,
                stacklevel=2,
            )
            return

        fig, ax = plt.subplots(figsize=(8, 6), dpi=120)
        cf = ax.contourf(
            grid.lon_grid, grid.lat_grid, grid.values,
            levels=20, cmap="YlOrRd", alpha=0.85
        )
        plt.colorbar(cf, ax=ax, label="CH₄ (ppm) – Estimasi IDW [SIMULASI/BELUM TERVALIDASI]")

        if node_lats is not None and node_lons is not None:
            ax.scatter(node_lons, node_lats, c="blue", s=80, zorder=5,
                       label="Node sensor")
            if node_values is not None:
                for lat, lon, val in zip(node_lats, node_lons, node_values):
                    ax.annotate(f"{val:.0f}", (lon, lat),
                                textcoords="offset points", xytext=(5, 5),
                                fontsize=7)

        ax.set_xlabel("Bujur (°)")
        ax.set_ylabel("Lintang (°)")
        ax.set_title(
            f"Peta Konsentrasi CH₄ – Interpolasi IDW\n"
            f"{grid.timestamp_label} | {grid.n_nodes} node | "
            f"[ESTIMASI – Belum Tervalidasi]",
            fontsize=10,
        )
        ax.legend(loc="upper right", fontsize=8)
        ax.text(
            0.01, 0.01,
            "SIMULASI / PROTOTIPE – Bukan data lapangan tervalidasi",
            transform=ax.transAxes, fontsize=7, color="red", alpha=0.7,
        )

        os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
        fig.tight_layout()
        fig.savefig(filepath, dpi=120)
        plt.close(fig)
        print(f"[spatial] Peta disimpan: {filepath}")
