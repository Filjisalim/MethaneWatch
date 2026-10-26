"""
test_estimation.py – Uji Unit Modul Estimasi Potensi Gas
"""

import os
import sys
import warnings

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from methanewatch.estimation import GasEstimator, EstimationParams


@pytest.fixture
def estimator():
    return GasEstimator()


def test_estimation_returns_result(estimator):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = estimator.estimate()
    assert result is not None


def test_low_less_than_high(estimator):
    """Batas bawah harus selalu ≤ batas atas."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = estimator.estimate()
    assert result.gas_volume_m3_per_year_low <= result.gas_volume_m3_per_year_high
    assert result.energy_mj_per_year_low     <= result.energy_mj_per_year_high


def test_label_contains_ilustrasi(estimator):
    """Hasil harus selalu berlabel ILUSTRASI."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = estimator.estimate()
    assert "ILUSTRASI" in result.label.upper() or "ILUSTRASI" in result.disclaimer.upper()


def test_assumptions_list_not_empty(estimator):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = estimator.estimate()
    assert len(result.assumptions_not_verified) > 0, "Harus ada daftar asumsi yang belum diverifikasi"


def test_default_params_warns(estimator):
    """Estimasi dengan parameter default harus menghasilkan peringatan."""
    with pytest.warns(UserWarning, match="Verifikasi"):
        result = estimator.estimate()
    assert result is not None


def test_measured_ch4_warns(estimator):
    """Memasukkan ch4 terukur harus menghasilkan peringatan metodologi."""
    with pytest.warns(UserWarning):
        result = estimator.estimate(measured_avg_ch4_ppm=450.0)
    assert result is not None


def test_custom_params(estimator):
    """Estimasi dengan parameter kustom harus tetap valid."""
    params = EstimationParams(
        area_active_m2=5000.0,
        depth_active_m=3.0,
        ch4_fraction=0.55,
        ch4_fraction_uncertainty=0.05,
        extraction_efficiency=0.40,
        extraction_efficiency_uncertainty=0.15,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = estimator.estimate(params=params)
    assert result.gas_volume_m3_per_year_est > 0


def test_format_report_contains_keywords(estimator):
    """Laporan harus mengandung kata-kata kunci penting."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = estimator.estimate()
    report = GasEstimator.format_report(result)
    assert "ILUSTRASI" in report
    assert "Verifikasi" in report
    assert "ketidakpastian" in report.lower() or "Rendah" in report
