"""
estimation.py – Modul Estimasi Potensi Gas (ILUSTRASI)
=========================================================
PERINGATAN PENTING:
- Modul ini menghasilkan ESTIMASI ILUSTRASI dari potensi gas TPA.
- Bukan klaim hasil pengukuran atau produksi nyata.
- Semua parameter masukan adalah ASUMSI yang HARUS diverifikasi
  dengan data lapangan, pengelola TPA, dan ahli teknik lingkungan.
- Output SELALU disertai rentang ketidakpastian dan label "ILUSTRASI".
- Sistem ini TIDAK mengklaim total emisi atau potensi listrik.
- Prototipe awal. Belum diuji di lapangan.

Referensi metodologi (perlu diverifikasi):
- Model LandGEM (EPA) [Verifikasi: https://www.epa.gov/]
- IPCC 2006 Waste Guidelines [Verifikasi]
- Studi TPA Air Dingin (lihat docs/architecture.md untuk sumber)
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import numpy as np


# ------------------------------------------------------------------
# Parameter masukan
# ------------------------------------------------------------------

@dataclass
class EstimationParams:
    """
    Parameter untuk estimasi potensi gas TPA.

    SEMUA NILAI ADALAH ASUMSI AWAL.
    Tim HARUS mengganti dengan nilai dari data lapangan, pengelola TPA,
    dan literatur yang relevan. [Verifikasi setiap parameter]
    """

    # Parameter TPA
    area_active_m2: float = 10_000.0
    """Luas zona aktif TPA (m²). [Verifikasi ke pengelola TPA]"""

    waste_density_kg_m3: float = 700.0
    """Densitas sampah padat (kg/m³). [Verifikasi: Asumsi. Cek literatur lokal]"""

    depth_active_m: float = 5.0
    """Kedalaman rata-rata zona aktif (m). [Verifikasi ke pengelola TPA]"""

    # Komposisi gas
    ch4_fraction: float = 0.50
    """Fraksi metana dalam gas TPA (0–1). Kisaran: 0.45–0.60. [Verifikasi Sumber 3 / datasheet lokal]"""

    ch4_fraction_uncertainty: float = 0.08
    """Ketidakpastian fraksi metana (±). [Verifikasi]"""

    # Efisiensi pengambilan
    extraction_efficiency: float = 0.50
    """Efisiensi pengambilan gas (0–1). Asumsi sangat kasar. [Verifikasi]"""

    extraction_efficiency_uncertainty: float = 0.20
    """Ketidakpastian efisiensi pengambilan (±). [Verifikasi]"""

    # Parameter listrik (jika relevan di masa depan)
    generator_efficiency: float = 0.30
    """Efisiensi generator gas (0–1). [Verifikasi: Asumsi sementara]"""

    ch4_energy_density_mj_m3: float = 35.8
    """Energi kalor metana (MJ/m³ pada kondisi standar). [Verifikasi NIST/literatur]"""

    # Periode estimasi
    period_years: float = 1.0
    """Periode estimasi (tahun). [Verifikasi ke roadmap proyek]"""

    # Catatan
    notes: str = (
        "Semua parameter adalah ASUMSI AWAL untuk ilustrasi. "
        "Wajib diverifikasi dengan data lapangan dan ahli sebelum digunakan "
        "untuk pengambilan keputusan. [Verifikasi]"
    )


# ------------------------------------------------------------------
# Struktur hasil
# ------------------------------------------------------------------

@dataclass
class EstimationResult:
    """
    Hasil estimasi potensi gas TPA.

    SELURUH ANGKA ADALAH ILUSTRASI – BELUM TERVALIDASI.
    """

    # Volume gas total yang bisa diambil (m³/tahun)
    gas_volume_m3_per_year_est: float
    gas_volume_m3_per_year_low: float   # batas bawah (ketidakpastian)
    gas_volume_m3_per_year_high: float  # batas atas (ketidakpastian)

    # Potensi energi dari metana (MJ/tahun)
    energy_mj_per_year_est: float
    energy_mj_per_year_low: float
    energy_mj_per_year_high: float

    # Parameter yang digunakan
    params_used: EstimationParams

    # Label dan peringatan wajib
    label: str = "ILUSTRASI – Belum Tervalidasi"
    disclaimer: str = (
        "Estimasi ini adalah ilustrasi kasar berdasarkan asumsi yang belum diverifikasi. "
        "Sistem MethaneWatch TIDAK mengklaim total emisi, potensi listrik, atau debit gas nyata. "
        "Gunakan hanya sebagai pengantar diskusi, bukan untuk pengambilan keputusan. "
        "Semua nilai harus diverifikasi dengan data lapangan, pengelola TPA, dan ahli teknik lingkungan."
    )
    assumptions_not_verified: list = field(default_factory=list)


# ------------------------------------------------------------------
# Estimator
# ------------------------------------------------------------------

class GasEstimator:
    """
    Estimator potensi gas TPA – hanya untuk ilustrasi.

    Pendekatan sederhana:
    1. Perkirakan volume sampah di zona aktif.
    2. Terapkan fraksi metana dan efisiensi pengambilan.
    3. Hasilkan rentang ketidakpastian dari variasi parameter.

    Pendekatan ini SANGAT disederhanakan. Model yang lebih akurat
    (LandGEM, IPCC First Order Decay) memerlukan data temporal
    sampah yang masuk, yang tidak tersedia di prototipe ini.
    [Verifikasi dengan dosen teknik lingkungan]
    """

    ASSUMPTIONS_NOT_VERIFIED = [
        "Luas dan kedalaman zona aktif TPA [Verifikasi ke pengelola]",
        "Densitas sampah 700 kg/m³ [Verifikasi literatur lokal]",
        "Fraksi metana 50% ± 8% [Verifikasi sampel gas nyata]",
        "Efisiensi pengambilan 50% ± 20% [Verifikasi desain sistem]",
        "Model volume sederhana (bukan LandGEM/IPCC FOD) [Verifikasi metode]",
        "Produksi gas per satuan massa sampah tidak dimodelkan [Verifikasi]",
    ]

    def estimate(
        self,
        params: Optional[EstimationParams] = None,
        measured_avg_ch4_ppm: Optional[float] = None,
    ) -> EstimationResult:
        """
        Hitung estimasi potensi gas.

        Parameters
        ----------
        params : EstimationParams, optional
            Parameter estimasi. Jika None, gunakan default (asumsi).
        measured_avg_ch4_ppm : float, optional
            Rata-rata CH4 terukur dari node sensor (ppm).
            Saat ini belum diintegrasikan ke formula utama karena
            konsentrasi ambien ≠ laju emisi. [Verifikasi metodologi]

        Returns
        -------
        EstimationResult dengan label ILUSTRASI.
        """
        if params is None:
            params = EstimationParams()
            warnings.warn(
                "[Estimasi] Menggunakan parameter default (ASUMSI). "
                "Ganti dengan data nyata sebelum publikasi. [Verifikasi]",
                UserWarning, stacklevel=2,
            )

        if measured_avg_ch4_ppm is not None:
            warnings.warn(
                f"[Estimasi] ch4 terukur rata-rata {measured_avg_ch4_ppm:.1f} ppm diterima, "
                "tetapi belum diintegrasikan ke formula estimasi karena konsentrasi ambien "
                "≠ laju emisi dan memerlukan data fluks. [Verifikasi metodologi]",
                UserWarning, stacklevel=2,
            )

        # Volume sampah (sangat kasar)
        waste_volume_m3 = params.area_active_m2 * params.depth_active_m
        waste_mass_kg   = waste_volume_m3 * params.waste_density_kg_m3

        # Asumsi sangat kasar: ~100 m³ gas / ton sampah (BELUM TERVALIDASI)
        # [Verifikasi: gunakan data lapangan atau model FOD]
        GAS_PER_TON_M3 = 100.0  # m³ gas / ton sampah – ASUMSI KASAR [Verifikasi]
        gas_total_m3 = (waste_mass_kg / 1000.0) * GAS_PER_TON_M3 * params.period_years

        # Fraksi metana + efisiensi
        ch4_low  = params.ch4_fraction - params.ch4_fraction_uncertainty
        ch4_high = params.ch4_fraction + params.ch4_fraction_uncertainty
        eff_low  = params.extraction_efficiency - params.extraction_efficiency_uncertainty
        eff_high = params.extraction_efficiency + params.extraction_efficiency_uncertainty

        ch4_low  = max(0.0, ch4_low)
        ch4_high = min(1.0, ch4_high)
        eff_low  = max(0.0, eff_low)
        eff_high = min(1.0, eff_high)

        vol_est  = gas_total_m3 * params.ch4_fraction          * params.extraction_efficiency
        vol_low  = gas_total_m3 * ch4_low                      * eff_low
        vol_high = gas_total_m3 * ch4_high                     * eff_high

        # Energi
        e_est  = vol_est  * params.ch4_energy_density_mj_m3
        e_low  = vol_low  * params.ch4_energy_density_mj_m3
        e_high = vol_high * params.ch4_energy_density_mj_m3

        return EstimationResult(
            gas_volume_m3_per_year_est=round(vol_est,  1),
            gas_volume_m3_per_year_low=round(vol_low,  1),
            gas_volume_m3_per_year_high=round(vol_high, 1),
            energy_mj_per_year_est=round(e_est,  1),
            energy_mj_per_year_low=round(e_low,  1),
            energy_mj_per_year_high=round(e_high, 1),
            params_used=params,
            label="ILUSTRASI – Belum Tervalidasi",
            disclaimer=(
                "Estimasi ini adalah ilustrasi kasar berdasarkan asumsi yang belum diverifikasi. "
                "Sistem MethaneWatch TIDAK mengklaim total emisi, potensi listrik, atau debit gas nyata. "
                "Gunakan hanya sebagai pengantar diskusi, bukan untuk pengambilan keputusan. "
                "Semua nilai harus diverifikasi dengan data lapangan dan ahli teknik lingkungan."
            ),
            assumptions_not_verified=self.ASSUMPTIONS_NOT_VERIFIED.copy(),
        )

    @staticmethod
    def format_report(result: EstimationResult) -> str:
        """Format hasil estimasi sebagai teks Markdown."""
        lines = [
            "## Estimasi Potensi Gas TPA – ILUSTRASI",
            "",
            f"> **{result.label}**",
            f"> {result.disclaimer}",
            "",
            "### Hasil Estimasi (rentang ketidakpastian)",
            "",
            f"| Metrik | Rendah | Estimasi Tengah | Tinggi |",
            f"|--------|--------|-----------------|--------|",
            f"| Volume CH₄ dapat diambil (m³/tahun) | "
            f"{result.gas_volume_m3_per_year_low:,.0f} | "
            f"{result.gas_volume_m3_per_year_est:,.0f} | "
            f"{result.gas_volume_m3_per_year_high:,.0f} |",
            f"| Energi potensial (MJ/tahun) | "
            f"{result.energy_mj_per_year_low:,.0f} | "
            f"{result.energy_mj_per_year_est:,.0f} | "
            f"{result.energy_mj_per_year_high:,.0f} |",
            "",
            "### Asumsi Yang Belum Diverifikasi",
            "",
        ]
        for i, assumption in enumerate(result.assumptions_not_verified, 1):
            lines.append(f"{i}. {assumption}")

        lines += [
            "",
            "### Parameter Yang Digunakan",
            "",
            f"| Parameter | Nilai |",
            f"|-----------|-------|",
            f"| Luas zona aktif | {result.params_used.area_active_m2:,.0f} m² [Verifikasi] |",
            f"| Kedalaman zona aktif | {result.params_used.depth_active_m:.1f} m [Verifikasi] |",
            f"| Densitas sampah | {result.params_used.waste_density_kg_m3:.0f} kg/m³ [Verifikasi] |",
            f"| Fraksi CH₄ | {result.params_used.ch4_fraction:.0%} ± {result.params_used.ch4_fraction_uncertainty:.0%} [Verifikasi] |",
            f"| Efisiensi pengambilan | {result.params_used.extraction_efficiency:.0%} ± {result.params_used.extraction_efficiency_uncertainty:.0%} [Verifikasi] |",
            f"| Periode estimasi | {result.params_used.period_years:.1f} tahun |",
            "",
            "_Catatan: Angka-angka di atas BUKAN hasil pengukuran. "
            "Mereka adalah ilustrasi perhitungan yang menunggu verifikasi data lapangan._",
        ]
        return "\n".join(lines)
