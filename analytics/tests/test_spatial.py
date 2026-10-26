"""
test_spatial.py – Uji Unit Modul Interpolasi Spasial
"""

import os
import sys
import warnings

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from methanewatch.spatial import IDWInterpolator, SpatialGrid


@pytest.fixture
def interpolator():
    return IDWInterpolator(power=2.0, resolution_deg=0.001, grid_padding_deg=0.001)


def make_nodes():
    lats   = np.array([-0.955, -0.957, -0.959, -0.953])
    lons   = np.array([100.352, 100.355, 100.351, 100.356])
    values = np.array([350.0, 280.0, 310.0, 420.0])
    return lats, lons, values


# ------------------------------------------------------------------ dasar

def test_interpolation_returns_grid(interpolator):
    lats, lons, values = make_nodes()
    grid = interpolator.interpolate(lats, lons, values, timestamp_label="test")
    assert isinstance(grid, SpatialGrid)
    assert grid.values.shape == grid.lat_grid.shape == grid.lon_grid.shape


def test_grid_at_node_close_to_node_value(interpolator):
    """Nilai grid di dekat posisi node harus mendekati nilai node tersebut."""
    lats   = np.array([-0.955, -0.960])
    lons   = np.array([100.350, 100.360])
    values = np.array([300.0, 500.0])
    grid = interpolator.interpolate(lats, lons, values)

    # Cari sel grid terdekat dengan node pertama
    dist = np.sqrt((grid.lat_grid - lats[0])**2 + (grid.lon_grid - lons[0])**2)
    idx = np.unravel_index(np.argmin(dist), dist.shape)
    closest_value = grid.values[idx]
    assert abs(closest_value - values[0]) < 50.0, (
        f"Nilai grid dekat node ({closest_value:.1f}) harus mendekati nilai node ({values[0]})"
    )


def test_interpolation_shape_positive(interpolator):
    lats, lons, values = make_nodes()
    grid = interpolator.interpolate(lats, lons, values)
    rows, cols = grid.values.shape
    assert rows > 0 and cols > 0, "Grid harus memiliki setidaknya satu sel"


def test_single_node_raises(interpolator):
    """Interpolasi dengan 1 node harus memunculkan error."""
    with pytest.raises(ValueError, match="minimal 2 node"):
        interpolator.interpolate(
            np.array([-0.955]), np.array([100.352]), np.array([300.0])
        )


def test_two_node_warns(interpolator):
    """2 node harus menghasilkan peringatan ketidakandalan."""
    with pytest.warns(UserWarning, match="tidak dapat diandalkan"):
        grid = interpolator.interpolate(
            np.array([-0.955, -0.960]),
            np.array([100.352, 100.360]),
            np.array([300.0, 400.0]),
        )
    assert grid is not None


# ------------------------------------------------------------------ export

def test_to_csv(interpolator, tmp_path):
    lats, lons, values = make_nodes()
    grid = interpolator.interpolate(lats, lons, values, timestamp_label="unit_test")
    filepath = str(tmp_path / "test_grid.csv")
    IDWInterpolator.to_csv(grid, filepath)
    assert os.path.exists(filepath)
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    assert "lat,lon,ch4_ppm_interpolated" in content
    assert "PERINGATAN" in content, "File harus memuat label peringatan"


def test_to_image_no_matplotlib(interpolator, tmp_path, monkeypatch):
    """to_image harus gracefully melewati jika matplotlib tidak ada."""
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "matplotlib":
            raise ImportError("matplotlib tidak tersedia (mock)")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    lats, lons, values = make_nodes()
    grid = interpolator.interpolate(lats, lons, values)
    filepath = str(tmp_path / "test_map.png")
    with pytest.warns(ImportWarning, match="matplotlib"):
        IDWInterpolator.to_image(grid, filepath)
    # File tidak dibuat karena matplotlib tidak ada – itu perilaku yang benar
    assert not os.path.exists(filepath)
