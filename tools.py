# tools.py — Fungsi kalkulasi yang dipanggil AI Agent
import json
from data import (
    HARGA_BBM, KONSUMSI_BBM, TARIF_PLN, KONSUMSI_EV,
    EMISI_BBM_PER_LITER, EMISI_PLN_PER_KWH,
    DATABASE_EV, INSENTIF_EV
)

# ─────────────────────────────────────────────
# TOOL 1: Hitung biaya BBM per bulan
# ─────────────────────────────────────────────
def hitung_biaya_bbm(jenis_kendaraan: str, jarak_harian_km: float, jenis_bbm: str) -> dict:
    """Menghitung biaya BBM per bulan berdasarkan kendaraan dan jarak harian."""
    konsumsi = KONSUMSI_BBM.get(jenis_kendaraan)
    harga    = HARGA_BBM.get(jenis_bbm)

    if not konsumsi or not harga:
        return {"error": f"Data tidak ditemukan untuk {jenis_kendaraan} / {jenis_bbm}"}

    jarak_bulanan   = jarak_harian_km * 30
    liter_per_bulan = (jarak_bulanan / 100) * konsumsi
    biaya_bulanan   = liter_per_bulan * harga
    biaya_tahunan   = biaya_bulanan * 12

    return {
        "jenis_kendaraan":   jenis_kendaraan,
        "jenis_bbm":         jenis_bbm,
        "jarak_harian_km":   jarak_harian_km,
        "jarak_bulanan_km":  jarak_bulanan,
        "konsumsi_liter_per_100km": konsumsi,
        "liter_per_bulan":   round(liter_per_bulan, 2),
        "harga_per_liter":   harga,
        "biaya_bulanan_rp":  round(biaya_bulanan),
        "biaya_tahunan_rp":  round(biaya_tahunan),
    }


# ─────────────────────────────────────────────
# TOOL 2: Hitung biaya listrik EV per bulan
# ─────────────────────────────────────────────
def hitung_biaya_ev(jenis_kendaraan: str, jarak_harian_km: float, golongan_pln: str) -> dict:
    """Menghitung estimasi biaya listrik jika menggunakan EV."""
    tarif  = TARIF_PLN.get(golongan_pln)
    konsumsi = KONSUMSI_EV.get(jenis_kendaraan)

    if not tarif or not konsumsi:
        return {"error": f"Data tidak ditemukan untuk {jenis_kendaraan} / {golongan_pln}"}

    jarak_bulanan    = jarak_harian_km * 30
    kwh_per_bulan    = jarak_bulanan * konsumsi
    biaya_bulanan    = kwh_per_bulan * tarif
    biaya_tahunan    = biaya_bulanan * 12

    return {
        "jenis_kendaraan":   jenis_kendaraan,
        "golongan_pln":      golongan_pln,
        "tarif_per_kwh":     tarif,
        "jarak_bulanan_km":  jarak_bulanan,
        "kwh_per_bulan":     round(kwh_per_bulan, 2),
        "biaya_bulanan_rp":  round(biaya_bulanan),
        "biaya_tahunan_rp":  round(biaya_tahunan),
    }


# ─────────────────────────────────────────────
# TOOL 3: Hitung emisi CO₂ perbandingan
# ─────────────────────────────────────────────
def hitung_emisi_co2(jenis_kendaraan: str, jarak_harian_km: float,
                     jenis_bbm: str, golongan_pln: str) -> dict:
    """Membandingkan emisi CO₂ antara kendaraan BBM dan EV."""
    konsumsi_bbm = KONSUMSI_BBM.get(jenis_kendaraan)
    konsumsi_ev  = KONSUMSI_EV.get(jenis_kendaraan)

    if not konsumsi_bbm or not konsumsi_ev:
        return {"error": "Data kendaraan tidak ditemukan"}

    jarak_tahunan = jarak_harian_km * 365

    # Emisi BBM
    liter_per_tahun = (jarak_tahunan / 100) * konsumsi_bbm
    emisi_bbm_kg    = liter_per_tahun * EMISI_BBM_PER_LITER

    # Emisi EV (dari grid PLN)
    kwh_per_tahun   = jarak_tahunan * konsumsi_ev
    emisi_ev_kg     = kwh_per_tahun * EMISI_PLN_PER_KWH

    pengurangan_kg  = emisi_bbm_kg - emisi_ev_kg
    persen_hemat    = (pengurangan_kg / emisi_bbm_kg) * 100

    return {
        "jarak_tahunan_km":      jarak_tahunan,
        "emisi_bbm_kg_per_tahun":  round(emisi_bbm_kg, 1),
        "emisi_ev_kg_per_tahun":   round(emisi_ev_kg, 1),
        "pengurangan_kg_per_tahun": round(pengurangan_kg, 1),
        "pengurangan_ton_per_tahun": round(pengurangan_kg / 1000, 2),
        "persen_pengurangan":    round(persen_hemat, 1),
        "setara_pohon_ditanam":  round(pengurangan_kg / 21),  # 1 pohon ~21 kg CO₂/tahun
    }


# ─────────────────────────────────────────────
# TOOL 4: Rekomendasi EV berdasarkan budget & kategori
# ─────────────────────────────────────────────
def rekomendasi_ev(jenis_kendaraan: str, budget_rp: float,
                   jarak_harian_km: float, golongan_pln: str) -> dict:
    """Mencari EV yang sesuai budget, kategori, dan kebutuhan harian pengguna."""
    tarif = TARIF_PLN.get(golongan_pln, 1444)

    # Filter berdasarkan kategori dan budget
    kandidat = [
        ev for ev in DATABASE_EV
        if ev["kategori"] == jenis_kendaraan and ev["harga"] <= budget_rp
    ]

    if not kandidat:
        # Jika tidak ada yang sesuai budget, tampilkan 3 termurah di kategori itu
        kandidat = sorted(
            [ev for ev in DATABASE_EV if ev["kategori"] == jenis_kendaraan],
            key=lambda x: x["harga"]
        )[:3]
        note = "Tidak ada EV yang sesuai budget. Berikut opsi terdekat:"
    else:
        kandidat = sorted(kandidat, key=lambda x: x["harga"])[:3]
        note = "EV yang sesuai budget dan kebutuhan kamu:"

    # Hitung biaya operasional per bulan untuk tiap kandidat
    hasil = []
    for ev in kandidat:
        kwh_per_bulan   = jarak_harian_km * 30 * ev["kwh_per_km"]
        biaya_bln       = round(kwh_per_bulan * tarif)
        cukup_range     = ev["range_km"] >= jarak_harian_km
        hasil.append({
            "nama":             ev["nama"],
            "harga_rp":         ev["harga"],
            "range_km":         ev["range_km"],
            "biaya_listrik_per_bulan": biaya_bln,
            "cukup_untuk_jarak_harian": cukup_range,
            "catatan":          ev["catatan"],
        })

    return {"note": note, "rekomendasi": hasil}


# ─────────────────────────────────────────────
# TOOL 5: Hitung Break-even Point (BEP)
# ─────────────────────────────────────────────
def hitung_bep(harga_ev_rp: float, biaya_bbm_per_bulan: float,
               biaya_ev_per_bulan: float, harga_jual_kendaraan_lama_rp: float = 0) -> dict:
    """Menghitung BEP dengan standar akuntansi (Trade-in & Depresiasi Baterai)."""
    
    # 1. Investasi Riil (Capital Expenditure setelah jual kendaraan lama)
    investasi_riil = harga_ev_rp - harga_jual_kendaraan_lama_rp
    if investasi_riil < 0: 
        investasi_riil = 0 # Kasus jika EV yang dibeli lebih murah dari kendaraan lama yang dijual

    # 2. Dana Cadangan Baterai (Sinking Fund)
    # Asumsi baterai adalah 40% dari harga EV, dan umur baterai 8 tahun (96 bulan)
    harga_baterai = harga_ev_rp * 0.40
    depresiasi_baterai_bulanan = harga_baterai / 96

    # 3. Selisih Operasional Bulanan Bersih
    penghematan_operasional = biaya_bbm_per_bulan - biaya_ev_per_bulan
    penghematan_bersih = penghematan_operasional - depresiasi_baterai_bulanan

    if penghematan_bersih <= 0:
        return {
            "bep_bulan": None,
            "pesan": "Biaya operasional EV (ditambah tabungan ganti baterai) ternyata tidak lebih hemat dari BBM.",
            "hemat_kotor_per_bulan_rp": round(penghematan_operasional),
            "hemat_bersih_per_bulan_rp": round(penghematan_bersih),
        }

    # 4. Kalkulasi BEP Akhir
    bep_bulan   = investasi_riil / penghematan_bersih
    bep_tahun   = bep_bulan / 12
    hemat_5thn  = (penghematan_bersih * 60) - investasi_riil

    return {
        "harga_ev_rp": round(harga_ev_rp),
        "harga_jual_kendaraan_lama_rp": round(harga_jual_kendaraan_lama_rp),
        "investasi_riil_rp": round(investasi_riil),
        "tabungan_baterai_per_bulan_rp": round(depresiasi_baterai_bulanan),
        "hemat_bersih_per_bulan_rp": round(penghematan_bersih),
        "bep_bulan": round(bep_bulan, 1),
        "bep_tahun": round(bep_tahun, 1),
        "net_hemat_5_tahun_rp": round(hemat_5thn),
        "catatan_finansial": "Kalkulasi ini telah memasukkan nilai trade-in kendaraan lama dan biaya penyusutan baterai untuk tahun ke-8."
    }


# ─────────────────────────────────────────────
# TOOL 6: Info insentif pemerintah
# ─────────────────────────────────────────────
def get_insentif_ev() -> dict:
    """Mengembalikan daftar insentif pemerintah untuk kendaraan listrik di Indonesia."""
    return {"insentif": INSENTIF_EV}


# ─────────────────────────────────────────────
# DEFINISI TOOLS untuk OpenAI Function Calling
# ─────────────────────────────────────────────
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "hitung_biaya_bbm",
            "description": "Menghitung biaya bahan bakar minyak (BBM) per bulan dan per tahun berdasarkan jenis kendaraan, jarak harian, dan jenis BBM yang digunakan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jenis_kendaraan": {
                        "type": "string",
                        "enum": ["Motor", "Mobil City Car", "Mobil Sedan/MPV", "SUV"],
                        "description": "Jenis kendaraan yang digunakan"
                    },
                    "jarak_harian_km": {
                        "type": "number",
                        "description": "Jarak tempuh rata-rata per hari dalam kilometer"
                    },
                    "jenis_bbm": {
                        "type": "string",
                        "enum": ["Pertalite", "Pertamax", "Pertamax Turbo"],
                        "description": "Jenis BBM yang digunakan"
                    }
                },
                "required": ["jenis_kendaraan", "jarak_harian_km", "jenis_bbm"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hitung_biaya_ev",
            "description": "Menghitung estimasi biaya listrik per bulan jika pengguna beralih ke kendaraan listrik (EV).",
            "parameters": {
                "type": "object",
                "properties": {
                    "jenis_kendaraan": {
                        "type": "string",
                        "enum": ["Motor", "Mobil City Car", "Mobil Sedan/MPV", "SUV"],
                    },
                    "jarak_harian_km": {"type": "number"},
                    "golongan_pln": {
                        "type": "string",
                        "enum": ["R-1 / 900 VA", "R-1 / 1300 VA", "R-1 / 2200 VA",
                                 "R-2 / 3500-5500 VA", "R-3 / 6600 VA+"],
                        "description": "Golongan tarif listrik PLN rumah tangga"
                    }
                },
                "required": ["jenis_kendaraan", "jarak_harian_km", "golongan_pln"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hitung_emisi_co2",
            "description": "Membandingkan emisi karbon CO₂ antara menggunakan kendaraan BBM vs kendaraan listrik.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jenis_kendaraan": {
                        "type": "string",
                        "enum": ["Motor", "Mobil City Car", "Mobil Sedan/MPV", "SUV"]
                    },
                    "jarak_harian_km": {"type": "number"},
                    "jenis_bbm":       {"type": "string"},
                    "golongan_pln":    {"type": "string"}
                },
                "required": ["jenis_kendaraan", "jarak_harian_km", "jenis_bbm", "golongan_pln"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rekomendasi_ev",
            "description": "Mencari dan merekomendasikan model kendaraan listrik yang sesuai dengan budget, kategori kendaraan, dan kebutuhan harian pengguna.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jenis_kendaraan": {
                        "type": "string",
                        "enum": ["Motor", "Mobil City Car", "Mobil Sedan/MPV", "SUV"]
                    },
                    "budget_rp":        {"type": "number", "description": "Budget maksimal dalam Rupiah"},
                    "jarak_harian_km":  {"type": "number"},
                    "golongan_pln":     {"type": "string"}
                },
                "required": ["jenis_kendaraan", "budget_rp", "jarak_harian_km", "golongan_pln"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hitung_bep",
            "description": "Menghitung Break-even Point (titik balik modal) dengan memperhitungkan nilai jual kendaraan lama (trade-in) dan biaya depresiasi baterai.",
            "parameters": {
                "type": "object",
                "properties": {
                    "harga_ev_rp":            {"type": "number"},
                    "biaya_bbm_per_bulan":    {"type": "number"},
                    "biaya_ev_per_bulan":     {"type": "number"},
                    "harga_jual_kendaraan_lama_rp": {
                        "type": "number", 
                        "description": "Harga jual kendaraan BBM lama pengguna. Jika tidak diketahui, asumsikan 0."
                    }
                },
                "required": ["harga_ev_rp", "biaya_bbm_per_bulan", "biaya_ev_per_bulan", "harga_jual_kendaraan_lama_rp"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_insentif_ev",
            "description": "Mengambil daftar insentif dan subsidi pemerintah Indonesia untuk pembelian kendaraan listrik.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
]

# ─── Dispatcher: panggil fungsi berdasarkan nama ──────────────────────
def execute_tool(tool_name: str, tool_args: dict) -> str:
    """Menjalankan tool yang diminta agent dan mengembalikan hasilnya sebagai string JSON."""
    fn_map = {
        "hitung_biaya_bbm":  hitung_biaya_bbm,
        "hitung_biaya_ev":   hitung_biaya_ev,
        "hitung_emisi_co2":  hitung_emisi_co2,
        "rekomendasi_ev":    rekomendasi_ev,
        "hitung_bep":        hitung_bep,
        "get_insentif_ev":   get_insentif_ev,
    }
    fn = fn_map.get(tool_name)
    if fn:
        result = fn(**tool_args)
    else:
        result = {"error": f"Tool '{tool_name}' tidak ditemukan."}
    return json.dumps(result, ensure_ascii=False)