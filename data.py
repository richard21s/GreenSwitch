# Sumber: PLN, Pertamina, ESDM, data pasar EV Indonesia 2026

# ─── HARGA BBM (Rp/liter) ────────────────────────────────────────────
HARGA_BBM = {
    "Pertalite":      10_000,
    "Pertamax":       13_900,
    "Pertamax Turbo": 14_900,
}

# ─── KONSUMSI BBM (liter/100 km) ─────────────────────────────────────
KONSUMSI_BBM = {
    "Motor":           3.5,
    "Mobil City Car":  8.0,
    "Mobil Sedan/MPV": 11.0,
    "SUV":             14.0,
}

# ─── TARIF LISTRIK PLN (Rp/kWh) ──────────────────────────────────────
# Sumber: Permen ESDM No. 3/2020, berlaku 2024-2026
TARIF_PLN = {
    "R-1 / 900 VA":    1_352,
    "R-1 / 1300 VA":   1_444,
    "R-1 / 2200 VA":   1_444,
    "R-2 / 3500-5500 VA": 1_699,
    "R-3 / 6600 VA+":  1_699,
}

# ─── KONSUMSI LISTRIK EV (kWh/km) ────────────────────────────────────
KONSUMSI_EV = {
    "Motor":           0.020,
    "Mobil City Car":  0.150,
    "Mobil Sedan/MPV": 0.180,
    "SUV":             0.220,
}

# ─── FAKTOR EMISI CO₂ ────────────────────────────────────────────────
# Bensin: 2.31 kg CO₂/liter (IPCC)
# Grid PLN Indonesia: 0.709 kg CO₂/kWh (Ditjen EBTKE ESDM 2023)
EMISI_BBM_PER_LITER   = 2.31   # kg CO₂
EMISI_PLN_PER_KWH     = 0.709  # kg CO₂

# ─── DATABASE EV INDONESIA 2026 ───────────────────────────────────────
# Format: nama, harga (Rp), range (km), kategori, konsumsi (kWh/km)
DATABASE_EV = [
    {
        "nama":      "Wuling Air ev Standard Range",
        "harga":     243_800_000,
        "range_km":  200,
        "kategori":  "Mobil City Car",
        "kwh_per_km": 0.130,
        "catatan":   "Ideal untuk dalam kota, harga paling terjangkau",
    },
    {
        "nama":      "NETA V",
        "harga":     299_000_000,
        "range_km":  380,
        "kategori":  "Mobil City Car",
        "kwh_per_km": 0.140,
        "catatan":   "Range lebih jauh, cocok kota + pinggiran",
    },
    {
        "nama":      "BYD Dolphin",
        "harga":     399_000_000,
        "range_km":  340,
        "kategori":  "Mobil City Car",
        "kwh_per_km": 0.132,
        "catatan":   "Teknologi blade battery, efisien & aman",
    },
    {
        "nama":      "Chery Omoda E5",
        "harga":     449_000_000,
        "range_km":  430,
        "kategori":  "SUV",
        "kwh_per_km": 0.142,
        "catatan":   "SUV terjangkau dengan range kompetitif",
    },
    {
        "nama":      "BYD Seal",
        "harga":     599_000_000,
        "range_km":  570,
        "kategori":  "Mobil Sedan/MPV",
        "kwh_per_km": 0.148,
        "catatan":   "Performa tinggi, range terbaik di kelasnya",
    },
    {
        "nama":      "Honda e:N1",
        "harga":     595_000_000,
        "range_km":  253,
        "kategori":  "SUV",
        "kwh_per_km": 0.195,
        "catatan":   "Brand Jepang terpercaya, cocok keluarga",
    },
    {
        "nama":      "BYD Atto 3",
        "harga":     649_000_000,
        "range_km":  480,
        "kategori":  "SUV",
        "kwh_per_km": 0.126,
        "catatan":   "SUV premium, paling efisien di segmennya",
    },
    {
        "nama":      "Hyundai Ioniq 5",
        "harga":     899_000_000,
        "range_km":  450,
        "kategori":  "SUV",
        "kwh_per_km": 0.172,
        "catatan":   "Flagship, fast charging 800V, build quality premium",
    },
    # Motor listrik
    {
        "nama":      "Gesits G1",
        "harga":     28_000_000,
        "range_km":  100,
        "kategori":  "Motor",
        "kwh_per_km": 0.020,
        "catatan":   "Motor listrik nasional, harga terjangkau",
    },
    {
        "nama":      "Alva One",
        "harga":     34_900_000,
        "range_km":  130,
        "kategori":  "Motor",
        "kwh_per_km": 0.019,
        "catatan":   "Desain modern, range lebih jauh",
    },
    {
        "nama":      "Honda EM1 e:",
        "harga":     40_000_000,
        "range_km":  41,
        "kategori":  "Motor",
        "kwh_per_km": 0.018,
        "catatan":   "Brand terpercaya, swap battery",
    },
]

# ─── INSENTIF PEMERINTAH EV ───────────────────────────────────────────
INSENTIF_EV = [
    "PPnBM 0% untuk kendaraan listrik (hemat 15% dari harga)",
    "Subsidi motor listrik Rp 7 juta (konversi) / Rp 7 juta (baru) dari Kemenkeu",
    "Subsidi PPN 10% untuk mobil listrik buatan dalam negeri (TKDN ≥ 40%)",
    "Tarif listrik khusus pengisian EV rumahan PLN: Rp 1.650/kWh (off-peak)",
    "Bebas ganjil-genap di Jakarta untuk kendaraan listrik berplat biru",
]
