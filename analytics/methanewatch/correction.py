"""
correction.py – Modul Koreksi Sensor
======================================
Melakukan koreksi pembacaan sensor MQ-4 berdasarkan suhu dan kelembapan,
dikalibrasi terhadap sensor referensi.

CATATAN:
- Modul ini mengimplementasikan regresi linear sederhana sebagai baseline.
- Koefisien koreksi HARUS dikalibrasi ulang menggunakan data nyata dari
  sensor referensi. [Verifikasi dengan dosen/ahli sensor]
- Prototipe awal. Belum diuji di lapangan.
- Semua nilai bersifat asumsi sampai diverifikasi.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from numpy.typing import NDArray


# ------------------------------------------------------------------
# Struktur hasil koreksi
# ------------------------------------------------------------------

@dataclass
class CorrectionResult:
    """Hasil proses koreksi sensor."""
    ch4_corrected: NDArray[np.float64]
    """Pembacaan CH4 setelah koreksi (ppm)."""

    mae_before: float
    """Mean Absolute Error sebelum koreksi vs referensi (ppm). NaN jika tidak ada referensi."""

    mae_after: float
    """Mean Absolute Error setelah koreksi vs referensi (ppm). NaN jika tidak ada referensi."""

    rmse_before: float
    """RMSE sebelum koreksi vs referensi (ppm). NaN jika tidak ada referensi."""

    rmse_after: float
    """RMSE setelah koreksi vs referensi (ppm). NaN jika tidak ada referensi."""

    coefficients: dict
    """Koefisien model koreksi yang digunakan."""

    model_type: str
    """Tipe model: 'linear_temp_rh' atau 'polynomial'."""

    warning: str = ""
    """Peringatan jika ada kondisi di luar batas normal."""


# ------------------------------------------------------------------
# Model koreksi
# ------------------------------------------------------------------

class SensorCorrector:
    """
    Koreksi sensor MQ-4 terhadap suhu dan kelembapan.

    Dua mode:
    1. predict_only: terapkan koefisien yang sudah ada (dari kalibrasi sebelumnya).
    2. fit_then_predict: latih model dari data kalibrasi (sensor murah vs referensi),
       lalu terapkan ke data baru.

    Semua nilai koefisien default adalah ASUMSI SIMULASI.
    Nilai nyata HARUS diperoleh dari kalibrasi. [Verifikasi]
    """

    # Koefisien default ASUMSI [Verifikasi – kalibrasi terhadap sensor referensi]
    DEFAULT_ALPHA = 2.5    # ppm/°C
    DEFAULT_BETA  = 0.8    # ppm/%RH
    DEFAULT_T_REF = 25.0   # °C referensi kalibrasi
    DEFAULT_RH_REF = 60.0  # % RH referensi kalibrasi

    def __init__(
        self,
        alpha: float = DEFAULT_ALPHA,
        beta: float = DEFAULT_BETA,
        t_ref: float = DEFAULT_T_REF,
        rh_ref: float = DEFAULT_RH_REF,
    ):
        """
        Parameters
        ----------
        alpha : float
            Koefisien koreksi suhu (ppm/°C). [Verifikasi dengan kalibrasi nyata]
        beta : float
            Koefisien koreksi kelembapan (ppm/%RH). [Verifikasi dengan kalibrasi nyata]
        t_ref : float
            Suhu referensi kalibrasi (°C).
        rh_ref : float
            Kelembapan referensi kalibrasi (%).
        """
        self.alpha  = alpha
        self.beta   = beta
        self.t_ref  = t_ref
        self.rh_ref = rh_ref
        self._fitted = False

    # ------------------------------------------------------------------ fitting

    def fit(
        self,
        ch4_raw: NDArray[np.float64],
        temp: NDArray[np.float64],
        rh: NDArray[np.float64],
        ch4_reference: NDArray[np.float64],
    ) -> "SensorCorrector":
        """
        Latih koefisien koreksi menggunakan data kalibrasi.

        Model: ch4_ref = ch4_raw + alpha*(T - T_ref) + beta*(RH - RH_ref) + offset
        Atau ditulis: residual = ch4_ref - ch4_raw = alpha*(T-T_ref) + beta*(RH-RH_ref) + offset

        Lakukan regresi OLS untuk mencari alpha, beta, offset.

        Parameters
        ----------
        ch4_raw : array
            Pembacaan mentah sensor murah (ppm).
        temp : array
            Suhu (°C).
        rh : array
            Kelembapan relatif (%).
        ch4_reference : array
            Pembacaan sensor referensi yang lebih akurat (ppm).

        Returns
        -------
        SensorCorrector (self, untuk chaining)
        """
        ch4_raw  = np.asarray(ch4_raw,  dtype=np.float64)
        temp     = np.asarray(temp,     dtype=np.float64)
        rh       = np.asarray(rh,       dtype=np.float64)
        ch4_ref  = np.asarray(ch4_reference, dtype=np.float64)

        if len(ch4_raw) < 10:
            warnings.warn(
                "Data kalibrasi sangat sedikit (< 10 sampel). "
                "Hasil koreksi tidak dapat diandalkan. [Verifikasi protokol kalibrasi]",
                UserWarning,
                stacklevel=2,
            )

        residual = ch4_ref - ch4_raw

        # Feature matrix: [delta_T, delta_RH, 1]
        delta_T  = temp - self.t_ref
        delta_RH = rh   - self.rh_ref
        X = np.column_stack([delta_T, delta_RH, np.ones(len(ch4_raw))])

        # OLS: koefisien = (X^T X)^{-1} X^T y
        try:
            coeff, _, _, _ = np.linalg.lstsq(X, residual, rcond=None)
        except np.linalg.LinAlgError as e:
            raise ValueError(f"Regresi kalibrasi gagal: {e}") from e

        self.alpha  = coeff[0]
        self.beta   = coeff[1]
        self.offset = coeff[2]
        self._fitted = True

        return self

    # ------------------------------------------------------------------ prediction

    def correct(
        self,
        ch4_raw: NDArray[np.float64],
        temp: NDArray[np.float64],
        rh: NDArray[np.float64],
        ch4_reference: Optional[NDArray[np.float64]] = None,
    ) -> CorrectionResult:
        """
        Terapkan koreksi ke data sensor.

        Parameters
        ----------
        ch4_raw : array
            Pembacaan mentah sensor (ppm).
        temp : array
            Suhu (°C).
        rh : array
            Kelembapan relatif (%).
        ch4_reference : array, optional
            Pembacaan sensor referensi untuk menghitung metrik galat.

        Returns
        -------
        CorrectionResult
        """
        ch4_raw = np.asarray(ch4_raw, dtype=np.float64)
        temp    = np.asarray(temp,    dtype=np.float64)
        rh      = np.asarray(rh,      dtype=np.float64)

        delta_T  = temp - self.t_ref
        delta_RH = rh   - self.rh_ref
        offset   = getattr(self, "offset", 0.0)

        ch4_corr = ch4_raw + self.alpha * delta_T + self.beta * delta_RH + offset

        # Hitung galat jika ada referensi
        nan = float("nan")
        mae_before = rmse_before = nan
        mae_after  = rmse_after  = nan
        warn_str = ""

        if ch4_reference is not None:
            ref = np.asarray(ch4_reference, dtype=np.float64)
            err_before = ch4_raw  - ref
            err_after  = ch4_corr - ref
            mae_before  = float(np.mean(np.abs(err_before)))
            mae_after   = float(np.mean(np.abs(err_after)))
            rmse_before = float(np.sqrt(np.mean(err_before**2)))
            rmse_after  = float(np.sqrt(np.mean(err_after**2)))

            if mae_after >= mae_before:
                warn_str = (
                    "[Koreksi] MAE setelah koreksi tidak lebih baik dari sebelumnya. "
                    "Periksa koefisien atau data kalibrasi."
                )
                warnings.warn(warn_str, UserWarning, stacklevel=2)

        if not self._fitted:
            warn_str += " [Koreksi] Menggunakan koefisien default (ASUMSI). Kalibrasi diperlukan. [Verifikasi]"

        return CorrectionResult(
            ch4_corrected=ch4_corr,
            mae_before=mae_before,
            mae_after=mae_after,
            rmse_before=rmse_before,
            rmse_after=rmse_after,
            coefficients={
                "alpha_ppm_per_degC": round(self.alpha, 4),
                "beta_ppm_per_pct_rh": round(self.beta, 4),
                "offset_ppm": round(offset, 4),
                "t_ref_c": self.t_ref,
                "rh_ref_pct": self.rh_ref,
                "fitted_from_data": self._fitted,
            },
            model_type="linear_temp_rh",
            warning=warn_str.strip(),
        )
