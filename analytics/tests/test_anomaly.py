"""
test_anomaly.py – Uji Unit Modul Deteksi Anomali
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from methanewatch.anomaly import AnomalyDetector
from methanewatch.sim_data import SimDataGenerator, DEFAULT_NODES, DEFAULT_SEED


@pytest.fixture
def detector():
    return AnomalyDetector(
        window_size=10,
        spike_z_threshold=3.0,
        stuck_variance_threshold=0.05,
        stuck_min_window=5,
        drift_threshold_ppm=80.0,
        drift_min_windows=3,
    )


@pytest.fixture
def gen():
    return SimDataGenerator(seed=DEFAULT_SEED)


# ------------------------------------------------------------------ spike

def test_spike_detected(detector):
    """Lonjakan yang diinjeksi harus terdeteksi."""
    n = 60
    vals  = np.random.default_rng(42).normal(300, 5, n)
    seqs  = list(range(n))
    times = [f"2026-11-01T{i:02d}:00:00" for i in range(n)]

    # Injeksi lonjakan pada posisi 30
    vals[30] = 900.0

    result = detector.detect_spikes(vals, node_id=1, timestamps=times, seqs=seqs)
    spike_seqs = [r.seq for r in result]
    assert 30 in spike_seqs, "Lonjakan pada seq=30 harus terdeteksi"


def test_no_spike_in_normal(detector):
    """Data normal tidak boleh memicu alarm spike."""
    rng  = np.random.default_rng(0)
    vals = rng.normal(300, 5, 80)  # noise kecil
    seqs  = list(range(len(vals)))
    times = [f"t{i}" for i in range(len(vals))]
    result = detector.detect_spikes(vals, node_id=1, timestamps=times, seqs=seqs)
    assert len(result) == 0, "Tidak ada spike di data normal"


# ------------------------------------------------------------------ stuck

def test_stuck_detected(detector):
    """Sensor yang mengirim nilai konstan harus terdeteksi sebagai stuck."""
    vals = np.concatenate([
        np.random.default_rng(1).normal(300, 5, 30),
        np.full(20, 312.0),   # stuck
        np.random.default_rng(1).normal(300, 5, 30),
    ])
    seqs  = list(range(len(vals)))
    times = [f"t{i}" for i in range(len(vals))]
    result = detector.detect_stuck(vals, node_id=1, timestamps=times, seqs=seqs)
    assert len(result) > 0, "Sensor macet harus terdeteksi"
    for r in result:
        assert r.anomaly_type == "stuck"


def test_no_stuck_in_normal(detector):
    """Data normal tidak boleh memicu stuck alarm."""
    rng  = np.random.default_rng(2)
    vals = rng.normal(300, 5, 80)
    seqs  = list(range(len(vals)))
    times = [f"t{i}" for i in range(len(vals))]
    result = detector.detect_stuck(vals, node_id=1, timestamps=times, seqs=seqs)
    assert len(result) == 0


# ------------------------------------------------------------------ run_all via sim data

def test_run_all_spike_scenario(detector, gen):
    """run_all harus mendeteksi spike yang diinjeksi di skenario spike."""
    records = gen.generate_spike(
        n_samples=80,
        spike_node_id=1,
        spike_indices=[30, 31, 32],
        spike_magnitude=800.0,
    )
    df = pd.DataFrame([
        {
            "node_id": r.node_id,
            "seq": r.seq,
            "timestamp_utc": r.timestamp_utc,
            "ch4_corrected_ppm": r.ch4_corrected_ppm,
        }
        for r in records
    ])
    result_df = detector.run_all(df)
    spike_rows = result_df[result_df["anomaly_type"] == "spike"]
    assert len(spike_rows) > 0, "Spike harus terdeteksi di skenario spike"


def test_run_all_stuck_scenario(detector, gen):
    """run_all harus mendeteksi stuck di skenario stuck."""
    records = gen.generate_stuck(
        n_samples=80,
        stuck_node_id=2,
        stuck_start=40,
        stuck_end=60,
    )
    df = pd.DataFrame([
        {
            "node_id": r.node_id,
            "seq": r.seq,
            "timestamp_utc": r.timestamp_utc,
            "ch4_corrected_ppm": r.ch4_corrected_ppm,
        }
        for r in records
    ])
    result_df = detector.run_all(df)
    stuck_rows = result_df[result_df["anomaly_type"] == "stuck"]
    assert len(stuck_rows) > 0, "Stuck harus terdeteksi di skenario stuck"


def test_run_all_returns_dataframe(detector, gen):
    records = gen.generate_normal(n_samples=20)
    df = pd.DataFrame([
        {
            "node_id": r.node_id,
            "seq": r.seq,
            "timestamp_utc": r.timestamp_utc,
            "ch4_corrected_ppm": r.ch4_corrected_ppm,
        }
        for r in records
    ])
    result_df = detector.run_all(df)
    assert isinstance(result_df, pd.DataFrame)
