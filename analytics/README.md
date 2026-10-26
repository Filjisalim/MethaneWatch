# MethaneWatch Analytics Engine

> **Paket Analisis Data, Koreksi Sensor, Deteksi Anomali, dan Estimasi Potensi Gas Metana**  
> Komponen analitik dari sistem **MethaneWatch** (MAJU:ON University Track 2026-27).  
> *Status:* **Prototipe Awal &bull; Belum diuji di lapangan &bull; Semua nilai parameter adalah asumsi sampai diverifikasi**

---

## 🔬 Ikhtisar Modul

Paket `methanewatch` dirancang untuk memproses aliran data telemetri dari jaringan node sensor LoRa di TPA. Paket ini mencakup tiga pilar utama AI & analitik data:

```
                  ┌──────────────────────────────┐
                  │ Data Mentah Sensor (CSV/DB)  │
                  │   Timestamp, CH4, Temp, RH   │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                 ┌────────────────────────────────┐
                 │  Modul A: methanewatch.correction
                 │  Kompensasi Suhu & Kelembapan  │
                 │  Kalibrasi vs. Sensor Referensi│
                 └───────────────┬────────────────┘
                                 │
                                 ▼
                 ┌────────────────────────────────┐
                 │  Modul B: methanewatch.anomaly │
                 │  Deteksi Lonjakan (Spike)      │
                 │  Deteksi Sensor Macet (Stuck)  │
                 │  Peringatan Alarm Keselamatan  │
                 └───────────────┬────────────────┘
                                 │
                 ┌───────────────┴────────────────┐
                 ▼                                ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│ Modul C1: methanewatch.spatial  │   │ Modul C2: methanewatch.estimation
│ Interpolasi Spasial 2D (IDW)    │   │ Model Peluruhan Orde-1 (LandGEM)│
│ Pemetaan Gradien Konsentrasi    │   │ Estimasi Laju Ekstraksi (Q10-90)│
└─────────────────────────────────┘   └─────────────────────────────────┘
```

---

## 📦 Instalasi

### Prasyarat
- Python 3.11 atau lebih baru
- Virtual environment (direkomendasikan)

### Cara Pasang
```bash
# Dari dalam direktori MethaneWatch/analytics/
pip install -e .

# Atau pasang dengan dependensi visualisasi & dev/test:
pip install -e ".[viz,dev]"
```

---

## 🧪 Menjalankan Pengujian Otomatis

Seluruh modul dilengkapi unit test berbasis `pytest` untuk menjamin keandalan fungsional:

```bash
pytest
```

Untuk melihat cakupan kode (*coverage report*):
```bash
pytest --cov=methanewatch
```

---

## 💡 Contoh Penggunaan Modul

### 1. Menghasilkan Data Simulasi (`sim_data.py`)
Berguna untuk pengujian algoritma tanpa perangkat keras fisik:
```python
from methanewatch.sim_data import generate_dataset

# Skenario: normal, spike, stuck, drift, atau mixed
df = generate_dataset(scenario="mixed", num_nodes=3, days=3)
print(df.head())
```

### 2. Koreksi & Kalibrasi Sensor (`correction.py`)
Mereduksi pengaruh fluktuasi temperatur dan kelembapan tropis pada sensor MQ-4:
```python
from methanewatch.correction import SensorCorrection

model = SensorCorrection()
# Melatih model jika data kalibrasi terhadap sensor referensi tersedia:
# model.fit(raw_ch4, temp, rh, reference_ch4)

ch4_corrected = model.correct(raw_ch4, temp, rh)
```

### 3. Deteksi Anomali Keselamatan (`anomaly.py`)
Mendeteksi lonjakan bahaya, sensor macet (stuck), dan deviasi drift:
```python
from methanewatch.anomaly import AnomalyDetector

detector = AnomalyDetector(z_threshold=3.0, stuck_window=10)
flags = detector.detect_spikes(df["ch4_ppm"])
stuck_flags = detector.detect_stuck(df["ch4_ppm"])
```

### 4. Interpolasi Spasial 2D (`spatial.py`)
Memetakan sebaran konsentrasi metana pada koordinat TPA:
```python
from methanewatch.spatial import SpatialInterpolator

interpolator = SpatialInterpolator(power=2.0)
grid_lats, grid_lons, grid_values = interpolator.interpolate(
    node_lats=[-0.852, -0.854, -0.850, -0.853],
    node_lons=[100.380, 100.382, 100.385, 100.381],
    values=[450.0, 1200.0, 310.0, 890.0],
    resolution=50
)
```

### 5. Estimasi Potensi Gas & Evaluasi Opsi (`estimation.py`)
Menghitung estimasi laju produksi gas metana dengan rentang ketidakpastian:
```python
from methanewatch.estimation import LandfillMethaneEstimator

estimator = LandfillMethaneEstimator()
result = estimator.estimate_potential(
    waste_tonnage_per_year=221555.0,  # [Verifikasi: estimasi 607 ton/hari di TPA Air Dingin]
    waste_age_years=10,
    measured_avg_ch4_ppm=850.0
)

print(result.summary_markdown())
```

---

## 📊 Skrip Generator Laporan

Buat laporan analisis otomatis langsung dari file CSV rekaman sensor:

```bash
python scripts/generate_report.py path/to/sensor_data.csv ringkasan_analisis.md
```

Laporan yang dihasilkan mencakup:
- Statistik deskriptif konsentrasi CH4, suhu, dan kelembapan.
- Ringkasan anomali keselamatan yang teridentifikasi.
- Evaluasi opsi pemanfaatan gas (Flaring vs. Biogas Kompor vs. Pembangkit Listrik).
- Rekomendasi langkah teknis berikutnya.
