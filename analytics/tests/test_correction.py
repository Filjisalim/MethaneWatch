"""
test_correction.py – Uji Unit Modul Koreksi Sensor
"""

import os
import sys
import warnings

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from methanewatch.correction import SensorCorrector


@pytest.fixture
def corrector():
    return SensorCorrector()


def make_synthetic_data(n=100, seed=42):
    rng = np.random.default_rng(seed)
    temp = 25.0 + rng.normal(0, 3.0, n)
    rh   = 60.0 + rng.normal(0, 8.0, n)
    # Data referensi "bersih"
    ch4_ref  = 300.0 + rng.normal(0, 5.0, n)
    # Sensor murah: terpengaruh suhu (+2 ppm/°C) dan RH (+0.5 ppm/%RH) + noise
    ch4_raw  = ch4_ref + 2.0 * (temp - 25.0) + 0.5 * (rh - 60.0) + rng.normal(0, 3.0, n)
    return ch4_raw, temp, rh, ch4_ref


def test_correct_returns_array(corrector):
    ch4_raw = np.array([300.0, 310.0, 320.0])
    temp    = np.array([25.0, 27.0, 23.0])
    rh      = np.array([60.0, 65.0, 55.0])
    result  = corrector.correct(ch4_raw, temp, rh)
    assert len(result.ch4_corrected) == 3


def test_fit_reduces_mae():
    """Setelah fitting, MAE harus lebih kecil dari sebelum fitting."""
    ch4_raw, temp, rh, ch4_ref = make_synthetic_data()
    corrector = SensorCorrector()
    corrector.fit(ch4_raw, temp, rh, ch4_ref)
    result = corrector.correct(ch4_raw, temp, rh, ch4_reference=ch4_ref)
    assert result.mae_after < result.mae_before, (
        f"MAE setelah ({result.mae_after:.2f}) harus < sebelum ({result.mae_before:.2f})"
    )


def test_default_coefficients_produce_warning(corrector):
    """Koreksi tanpa fitting harus menghasilkan peringatan."""
    ch4_raw = np.array([300.0, 310.0])
    temp    = np.array([25.0, 27.0])
    rh      = np.array([60.0, 65.0])
    result  = corrector.correct(ch4_raw, temp, rh)
    assert "Verifikasi" in result.warning or "kalibrasi" in result.warning.lower(), (
        "Harus ada peringatan bahwa koefisien belum dikalibrasi"
    )


def test_no_reference_gives_nan_metrics(corrector):
    ch4_raw = np.array([300.0, 310.0, 320.0])
    temp    = np.array([25.0, 27.0, 23.0])
    rh      = np.array([60.0, 65.0, 55.0])
    result  = corrector.correct(ch4_raw, temp, rh, ch4_reference=None)
    assert np.isnan(result.mae_before), "MAE harus NaN jika tidak ada referensi"
    assert np.isnan(result.mae_after),  "MAE harus NaN jika tidak ada referensi"


def test_small_calibration_data_warns():
    corrector = SensorCorrector()
    ch4_raw = np.array([300.0, 305.0])  # < 10 sampel
    temp    = np.array([25.0, 26.0])
    rh      = np.array([60.0, 61.0])
    ch4_ref = np.array([298.0, 302.0])
    with pytest.warns(UserWarning, match="sedikit"):
        corrector.fit(ch4_raw, temp, rh, ch4_ref)


def test_coefficients_dict_keys(corrector):
    result = corrector.correct(
        np.array([300.0]), np.array([25.0]), np.array([60.0])
    )
    expected_keys = {
        "alpha_ppm_per_degC", "beta_ppm_per_pct_rh", "offset_ppm",
        "t_ref_c", "rh_ref_pct", "fitted_from_data"
    }
    assert expected_keys.issubset(set(result.coefficients.keys()))
