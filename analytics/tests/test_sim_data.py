"""
test_sim_data.py – Uji Unit Generator Data Simulasi
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from methanewatch.sim_data import SimDataGenerator, DEFAULT_NODES, DEFAULT_SEED


@pytest.fixture
def gen():
    return SimDataGenerator(seed=DEFAULT_SEED)


def test_normal_count(gen):
    records = gen.generate_normal(n_samples=10)
    # 4 node × 10 sampel = 40 baris
    assert len(records) == len(DEFAULT_NODES) * 10


def test_normal_scenario_label(gen):
    records = gen.generate_normal(n_samples=5)
    for r in records:
        assert "SIMULASI" in r.scenario, "Setiap record harus berlabel SIMULASI"


def test_spike_injected(gen):
    records = gen.generate_spike(
        n_samples=50, spike_node_id=1, spike_indices=[30, 31],
        spike_magnitude=800.0
    )
    spike_records = [r for r in records if r.anomaly_flag == "spike"]
    assert len(spike_records) == 2, "Harus ada tepat 2 spike yang diinjeksi"


def test_stuck_constant_value(gen):
    records = gen.generate_stuck(
        n_samples=80, stuck_node_id=2, stuck_start=40, stuck_end=60
    )
    stuck = [r for r in records if r.node_id == 2 and r.anomaly_flag == "stuck"]
    if len(stuck) > 1:
        # Semua nilai stuck harus sama
        vals = set(r.ch4_raw_ppm for r in stuck)
        assert len(vals) == 1, "Nilai sensor macet harus konstan"


def test_drift_increases(gen):
    records = gen.generate_drift(
        n_samples=80, drift_node_id=3, drift_start=50,
        drift_rate_ppm_per_sample=5.0
    )
    drift_records = sorted(
        [r for r in records if r.node_id == 3 and r.anomaly_flag == "drift"],
        key=lambda r: r.seq,
    )
    if len(drift_records) > 1:
        # Nilai harus meningkat (drift ke atas)
        first_val = drift_records[0].ch4_raw_ppm
        last_val  = drift_records[-1].ch4_raw_ppm
        assert last_val > first_val, "Nilai drift harus meningkat seiring waktu"


def test_deterministic(gen):
    """Seed tetap harus menghasilkan output yang sama."""
    gen2 = SimDataGenerator(seed=DEFAULT_SEED)
    r1 = gen.generate_normal(n_samples=5)
    r2 = gen2.generate_normal(n_samples=5)
    for a, b in zip(r1, r2):
        assert a.ch4_raw_ppm == b.ch4_raw_ppm, "Output harus deterministik dengan seed yang sama"


def test_to_csv(gen, tmp_path):
    records = gen.generate_normal(n_samples=5)
    filepath = str(tmp_path / "test_sim.csv")
    SimDataGenerator.to_csv(records, filepath)
    assert os.path.exists(filepath)
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    assert "SIMULASI" in content, "File CSV harus memuat label SIMULASI"
