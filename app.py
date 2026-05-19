import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from agent import run_agent, build_initial_prompt
from tools import hitung_biaya_bbm, hitung_biaya_ev, hitung_emisi_co2

# ─── Konfigurasi halaman ──────────────────────────────────────────────
st.set_page_config(
    page_title="GreenSwitch — AI Agent Transisi Energi",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS KUSTOM (Meniru Tailwind dari React) ──────────────────────────
st.markdown("""
<style>
    /* Global Background & Fonts */
    .stApp {
        background: radial-gradient(ellipse at top right, #ecfdf5 0%, #f0fdf4 50%, #f0f9ff 100%);
        color: #1f2937;
    }
    
    /* Navbar Styling */
    .modern-navbar {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.4);
        padding: 1rem 2rem;
        border-radius: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .navbar-brand {
        font-size: 1.8rem;
        font-weight: 900;
        background: -webkit-linear-gradient(right, #064e3b, #065f46);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .navbar-badge {
        background: linear-gradient(to right, #d1fae5, #a7f3d0);
        color: #065f46;
        padding: 0.5rem 1rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }

    /* Core Metrics Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .modern-metric {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 24px;
        border: 1px solid #f1f5f9;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .modern-metric:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .modern-metric-dark {
        background: #111827;
        color: white;
        border: 1px solid #1f2937;
    }
    .metric-label { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 0.25rem; }
    .metric-val { font-size: 1.75rem; font-weight: 900; margin: 0; }
    
    /* Narrative Box (AI Verdict) */
    .narrative-box {
        padding: 2rem;
        border-radius: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        position: relative;
        overflow: hidden;
    }
    .narrative-switch {
        background: linear-gradient(to bottom right, #f0fdf4, #ecfdf5);
        border: 1px solid #d1fae5;
    }
    .narrative-switch h3 { color: #022c22; font-size: 1.8rem; font-weight: 900; margin-bottom: 0.5rem; }
    .narrative-switch p { color: #065f46; font-size: 1.1rem; line-height: 1.6; font-weight: 500; }
    
    .narrative-wait {
        background: linear-gradient(to bottom right, #fffbeb, #fefce8);
        border: 1px solid #fef3c7;
    }
    .narrative-wait h3 { color: #451a03; font-size: 1.8rem; font-weight: 900; margin-bottom: 0.5rem; }
    .narrative-wait p { color: #92400e; font-size: 1.1rem; line-height: 1.6; font-weight: 500; }

    /* Component Boxes */
    .content-box {
        background: white;
        padding: 1.8rem;
        border-radius: 2rem;
        border: 1px solid #f1f5f9;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        height: 100%;
    }
    .box-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Tips List */
    .tip-item {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .tip-number {
        background: #fffbeb;
        color: #d97706;
        width: 28px; height: 28px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: bold; font-size: 0.85rem; flex-shrink: 0;
        border: 1px solid #fef3c7;
    }
    .tip-text { font-size: 0.95rem; color: #374151; font-weight: 500; line-height: 1.5; margin: 0; }
    .tip-highlight { font-weight: 800; color: #b45309; margin-right: 0.3rem; }

    /* EV Card */
    .ev-card {
        padding: 1.2rem;
        border-radius: 1.5rem;
        border: 1px solid #f1f5f9;
        margin-bottom: 1rem;
        transition: background 0.2s;
    }
    .ev-card:hover { background: #ecfdf5; border-color: #d1fae5; }
    .ev-price { background: #ecfdf5; padding: 0.3rem 0.8rem; border-radius: 0.8rem; border: 1px solid #d1fae5; font-weight: 900; color: #065f46; font-size: 0.9rem;}

    /* Subsidy Box */
    .subsidy-box {
        background: linear-gradient(to bottom right, #111827, #1f2937);
        padding: 1.8rem;
        border-radius: 2rem;
        color: white;
        position: relative;
        overflow: hidden;
    }
    .subsidy-title { font-size: 0.85rem; font-weight: 800; letter-spacing: 0.1em; color: #34d399; text-transform: uppercase; margin-bottom: 1rem; }
    .subsidy-item { font-size: 0.9rem; color: #d1d5db; margin-bottom: 0.8rem; font-weight: 500; display: flex; gap: 0.5rem;}
    
    /* Chat Box Modern */
    .chat-user-msg { background: #111827; color: white; padding: 1rem 1.2rem; border-radius: 1.2rem 1.2rem 0.2rem 1.2rem; max-width: 85%; margin-left: auto; margin-bottom: 1rem; font-weight: 500; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .chat-agent-msg { background: white; border: 1px solid #e5e7eb; color: #1f2937; padding: 1rem 1.2rem; border-radius: 1.2rem 1.2rem 1.2rem 0.2rem; max-width: 85%; margin-right: auto; margin-bottom: 1rem; font-weight: 500; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────────
if "conversation" not in st.session_state: st.session_state.conversation = []
if "analysis_done" not in st.session_state: st.session_state.analysis_done = False
if "user_data" not in st.session_state: st.session_state.user_data = {}
if "chart_data" not in st.session_state: st.session_state.chart_data = {}
if "parsed_result" not in st.session_state: st.session_state.parsed_result = None

# ─── HEADER ──────────────────────────────────────────────────────────
st.markdown("""
<div class="modern-navbar">
    <h1 class="navbar-brand">⚡ GreenSwitch</h1>
    <div class="navbar-badge">Tim RDR · TechnoFest 2026</div>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 Profil & Parameter")
    
    jenis_kendaraan_saat_ini = st.selectbox("Kendaraan BBM Saat Ini", ["Motor", "Mobil City Car", "Mobil Sedan/MPV", "SUV"])
    kategori_ev_diincar = st.selectbox("Kategori EV yang Diinginkan", ["Motor", "Mobil City Car", "Mobil Sedan/MPV", "SUV"], index=1)
    jenis_bbm = st.selectbox("BBM yang Digunakan", ["Pertalite", "Pertamax", "Pertamax Turbo"])
    jarak_harian = st.slider("Jarak Tempuh Harian (km)", 5, 150, 30, 5)
    golongan_pln = st.selectbox("Daya Listrik Rumah PLN", ["R-1 / 900 VA", "R-1 / 1300 VA", "R-1 / 2200 VA", "R-2 / 3500-5500 VA", "R-3 / 6600 VA+"], index=1)
    
    st.markdown("---")
    budget_juta = st.number_input("Budget Beli EV (Juta Rp)", min_value=10, max_value=2000, value=300, step=10)
    budget_rp = budget_juta * 1_000_000
    
    trade_in_juta = st.number_input("Nilai Jual Kendaraan Lama (Juta Rp)", min_value=0, max_value=1000, value=15, step=1)
    trade_in_rp = trade_in_juta * 1_000_000
    
    analyze_btn = st.button("🔍 Analisis dengan Agent", type="primary", use_container_width=True)
    if st.button("🔄 Reset", use_container_width=True):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# ─── PREVIEW (Sebelum Analisis) ───────────────────────────────────────
if not st.session_state.analysis_done:
    bbm_data = hitung_biaya_bbm(jenis_kendaraan_saat_ini, jarak_harian, jenis_bbm)
    ev_data  = hitung_biaya_ev(kategori_ev_diincar, jarak_harian, golongan_pln)
    co2_data = hitung_emisi_co2(jenis_kendaraan_saat_ini, kategori_ev_diincar, jarak_harian, jenis_bbm, golongan_pln)

    st.markdown(f"""
    <div style="background: white; padding: 2.5rem; border-radius: 2rem; border: 1px solid #f1f5f9; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.05); text-align: center; max-width: 800px; margin: 0 auto;">
        <h2 style="font-size: 2.5rem; font-weight: 900; color: #111827; margin-bottom: 1rem; line-height: 1.2;">Transisi ke EV dengan <span style="background: linear-gradient(to right, #059669, #14b8a6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Data & Fakta.</span></h2>
        <p style="color: #6b7280; font-size: 1.1rem; font-weight: 500; margin-bottom: 2rem;">Berdasarkan mobilitas Anda, estimasi biaya BBM saat ini mencapai <strong>Rp {bbm_data['biaya_bulanan_rp']:,}/bulan</strong>. Klik "Analisis" di sidebar untuk melihat proyeksi finansial cerdas dari GreenSwitch Agent.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.chart_data = { "bbm_data": bbm_data, "ev_data": ev_data, "co2_data": co2_data }

# ─── EKSEKUSI ANALISIS ────────────────────────────────────────────────
if analyze_btn:
    st.session_state.user_data = {
        "jenis_kendaraan_saat_ini": jenis_kendaraan_saat_ini,
        "kategori_ev_diincar": kategori_ev_diincar,
        "jenis_bbm": jenis_bbm, "jarak_harian_km": jarak_harian,
        "golongan_pln": golongan_pln, "budget_rp": budget_rp, "trade_in_rp": trade_in_rp,
    }
    st.session_state.conversation = []
    st.session_state.analysis_done = False
    
    prompt = build_initial_prompt(st.session_state.user_data)
    
    def update_thinking(tname, targs):
        st.write(f"⚙️ Memanggil tool: {tname}...")

    with st.status("🤖 Agent GreenSwitch sedang berpikir...", expanded=True) as status:
        try:
            response, history = run_agent(prompt, [], status_callback=update_thinking)
            status.update(label="✅ Analisis Selesai dan Data Siap!", state="complete", expanded=False)
            
            st.session_state.conversation = history
            
            # ─── PERBAIKAN: PARSING JSON CERDAS (REAL DATA AI) ────────────────
            try:
                # Bersihkan spasi, baris baru, dan markdown ```json jika bocor
                clean_json = response.replace("```json", "").replace("```", "").strip()
                
                # Coba parse JSON asli dari AI
                parsed = json.loads(clean_json)
                
                # Petakan key secara fleksibel (Jaga-jaga jika AI mengganti nama key)
                st.session_state.parsed_result = {
                    "verdict": parsed.get("verdict", parsed.get("keputusan", "switch")),
                    "title": parsed.get("title", parsed.get("judul", parsed.get("kesimpulan_utama", "Hasil Analisis AI"))),
                    "narasi": parsed.get("narasi", parsed.get("penjelasan", parsed.get("kesimpulan", "Lihat detail analisis di bawah."))),
                    "tips": parsed.get("tips", parsed.get("saran", parsed.get("rekomendasi", [])))
                }
                
                # Mengamankan struktur tips jika AI mengembalikan list of strings alih-alih list of dicts
                safe_tips = []
                for t in st.session_state.parsed_result["tips"]:
                    if isinstance(t, dict):
                        safe_tips.append({"highlight": t.get("highlight", "Catatan"), "text": t.get("text", str(t))})
                    else:
                        safe_tips.append({"highlight": "Info", "text": str(t)})
                
                st.session_state.parsed_result["tips"] = safe_tips
                
                # Jika AI lupa membuat array tips sama sekali, jangan biarkan kosong
                if not st.session_state.parsed_result["tips"]:
                    st.session_state.parsed_result["tips"] = [
                        {"highlight": "Catatan", "text": "Silakan pelajari laporan mendalam di bawah untuk detail lengkap."}
                    ]
                    
            except Exception as json_err:
                # JIKA AI GAGAL BIKIN JSON DAN MENGIRIM TEKS BIASA:
                # Masukkan REAL TEKS dari AI ke dalam UI tanpa hardcode!
                st.session_state.parsed_result = {
                    "verdict": "switch",
                    "title": "Kesimpulan Agent",
                    "narasi": response,  # <--- INI ADALAH REAL DATA DARI AI
                    "tips": [
                        {"highlight": "Info Sistem", "text": "Agent merespons dengan format naratif murni. Seluruh detail penjabaran terdapat pada teks di atas."}
                    ]
                }
            # ──────────────────────────────────────────────────────────────
            
            st.session_state.analysis_done = True
        except Exception as e:
            status.update(label="❌ Terjadi Kesalahan Eksekusi", state="error")
            st.error(str(e))

# ─── RESULT DASHBOARD ─────────────────────────────────────────────────
if st.session_state.analysis_done:
    d = st.session_state.chart_data
    biaya_bbm = d["bbm_data"]["biaya_bulanan_rp"]
    biaya_ev = d["ev_data"]["biaya_bulanan_rp"]
    selisih = biaya_bbm - biaya_ev
    co2_kg = d["co2_data"]["emisi_bbm_kg_per_tahun"] if "emisi_bbm_kg_per_tahun" in d["co2_data"] else d["co2_data"].get("emisi_bbm_network_kg", 0)
    
    # Hitung nilai investasi awal riil dalam satuan JUTA untuk grafik
    u_budget = st.session_state.user_data.get('budget_rp', 300_000_000)
    u_trade = st.session_state.user_data.get('trade_in_rp', 15_000_000)
    investasi_awal_juta = (u_budget - u_trade) / 1_000_000
    if investasi_awal_juta < 0: investasi_awal_juta = 0
    
    res = st.session_state.parsed_result
    verdict_class = "narrative-switch" if res.get("verdict", "").lower() == "switch" else "narrative-wait"
    icon = "✨" if res.get("verdict", "").lower() == "switch" else "⚠️"
    
    # 1. AI NARRATIVE BOX
    st.markdown(f"""
    <div class="narrative-box {verdict_class}">
        <div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.7; margin-bottom: 0.5rem;">Keputusan Agent</div>
        <h3>{icon} {res.get('title', 'Analisis Selesai')}</h3>
        <p>{res.get('narasi', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. CORE METRICS
    st.markdown(f"""
    <div class="metric-grid">
        <div class="modern-metric">
            <div class="metric-label">BBM / Bulan</div>
            <div class="metric-val" style="color: #111827;">Rp {biaya_bbm:,}</div>
        </div>
        <div class="modern-metric">
            <div class="metric-label">Listrik EV / Bulan</div>
            <div class="metric-val" style="color: #059669;">Rp {biaya_ev:,}</div>
        </div>
        <div class="modern-metric" style="background: {'#f0fdf4' if selisih > 0 else '#fef2f2'}; border-color: {'#d1fae5' if selisih > 0 else '#fee2e2'};">
            <div class="metric-label" style="color: {'#065f46' if selisih > 0 else '#991b1b'}">Penghematan</div>
            <div class="metric-val" style="color: {'#059669' if selisih > 0 else '#dc2626'};">Rp {abs(selisih):,}</div>
        </div>
        <div class="modern-metric modern-metric-dark">
            <div class="metric-label" style="color: #9ca3af;">Reduksi CO2 / Tahun</div>
            <div class="metric-val">{co2_kg:,.0f} <span style="font-size: 1rem; color: #6b7280;">Kg</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. SPLIT LAYOUT (3:2)
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        # CHART AREA — SKALA DIKALIBRASI KE SATUAN JUTA RP (FIXED SCALE)
        st.markdown('<div class="content-box"><div class="box-title">📈 Proyeksi Kumulatif 5 Tahun (Dalam Juta Rp)</div>', unsafe_allow_html=True)
        bulan = list(range(0, 61))
        
        # Konversi biaya bulanan harian ke dalam satuan juta agar grafik sinkron proporsional
        kum_bbm = [(m * biaya_bbm) / 1_000_000 for m in bulan]
        kum_ev  = [investasi_awal_juta + ((m * biaya_ev) / 1_000_000) for m in bulan]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bulan, y=kum_bbm, fill='tozeroy', name="Operasional BBM", line=dict(color="#ef4444", width=3), fillcolor="rgba(239, 68, 68, 0.03)"))
        fig.add_trace(go.Scatter(x=bulan, y=kum_ev, fill='tozeroy', name="EV + Investasi Net", line=dict(color="#10b981", width=3), fillcolor="rgba(16, 185, 129, 0.03)"))
        
        fig.update_layout(
            margin=dict(l=10, r=10, t=20, b=10), height=300,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, title="Bulan Ke-"), 
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Total Pengeluaran (Juta Rp)", ticksuffix=" Jt"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # TIPS KHUSUS (TERJAMIN DENGAN AMBIL DATA PARSED_RESULT)
        if res and "tips" in res:
            st.markdown('<div style="margin-top: 1.5rem;" class="content-box"><div class="box-title">💡 Tips Khusus untuk Anda</div>', unsafe_allow_html=True)
            for i, tip in enumerate(res["tips"]):
                st.markdown(f"""
                <div class="tip-item">
                    <div class="tip-number">{i+1}</div>
                    <p class="tip-text"><span class="tip-highlight">{tip.get('highlight', '')}:</span> {tip.get('text', '')}</p>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        # SUBSIDY BOX
        st.markdown("""
        <div class="subsidy-box">
            <div class="subsidy-title">🏛️ Insentif Pemerintah</div>
            <div class="subsidy-item"><span>✓</span> Potongan PPN dari 11% menjadi 1%</div>
            <div class="subsidy-item"><span>✓</span> Bebas Ganjil-Genap di DKI Jakarta</div>
            <div class="subsidy-item"><span>✓</span> Subsidi Insentif Langsung s.d Rp 7 Juta</div>
        </div>
        """, unsafe_allow_html=True)
        
        # OPSI KENDARAAN (DINAMIS MENGIKUTI INPUT SELECTION SIDEBAR)
        st.markdown('<div style="margin-top: 1.5rem;" class="content-box"><div class="box-title">🚗 Opsi Unit EV Terdekat</div>', unsafe_allow_html=True)
        
        # Penentuan entri spesifikasi mobil/motor secara dinamis berdasarkan kategori diincar
        if kategori_ev_diincar == "Motor":
            nama_ev, harga_ev_txt, spec_ev = "Smoot Tempur / ALVA One", "Rp 20 - 36 Jt", "Jangkauan 60-70 km | Ekosistem Swap Baterai"
        elif kategori_ev_diincar == "Mobil City Car":
            nama_ev, harga_ev_txt, spec_ev = "Wuling Air EV Lite / NETA V", "Rp 190 - 299 Jt", "Jangkauan 200-380 km | Durasi AC Fast 35 Min"
        elif kategori_ev_diincar == "Mobil Sedan/MPV":
            nama_ev, harga_ev_txt, spec_ev = "Wuling Binguo / BYD Dolphin", "Rp 317 - 425 Jt", "Jangkauan 333-410 km | Teknologi Blade Battery"
        else:
            nama_ev, harga_ev_txt, spec_ev = "Hyundai Ioniq 5 / BYD Atto 3", "Rp 515 - 782 Jt", "Platform EV E-GMP | Fitur V2L Port Listrik"

        st.markdown(f"""
        <div class="ev-card">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                <div>
                    <h4 style="margin: 0; font-weight: 800; color: #111827; font-size: 1.05rem;">{nama_ev}</h4>
                    <p style="margin: 0; font-size: 0.8rem; font-weight: bold; color: #059669; mt-1;">{spec_ev}</p>
                </div>
                <div class="ev-price">{harga_ev_txt}</div>
            </div>
            <p style="margin: 0; font-size: 0.82rem; color: #64748b; font-weight: 500; line-height: 1.4;">Rekomendasi ini disesuaikan otomatis dengan batas atas pagu anggaran Anda sebesar Rp {budget_juta} Juta rupiah.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. LAPORAN ANALISIS LENGKAP
    st.markdown('<div style="margin-top: 1.5rem;" class="content-box">', unsafe_allow_html=True)
    st.markdown('<div class="box-title">📑 Laporan Analisis Mendalam</div>', unsafe_allow_html=True)
    
    hemat_tahunan = selisih * 12
    pohon_setara = d["co2_data"].get("setara_pohon_ditanam", 0)
    ton_co2 = d["co2_data"].get("pengurangan_ton_per_tahun", 0)
    
    st.markdown(f"""
    ### 💰 ANALISIS BIAYA
    * **Biaya BBM Bulanan:** Rp {biaya_bbm:,}/bulan
    * **Estimasi Listrik EV Bulanan:** Rp {biaya_ev:,}/bulan
    * **Potensi Penghematan:** Berselisih **Rp {abs(selisih):,}/bulan** ({'Lebih Hemat' if selisih > 0 else 'Lebih Mahal'}).

    ### 🌿 DAMPAK LINGKUNGAN  
    * Dengan beralih ke kategori EV yang diincar, Anda berpotensi memotong emisi karbon sebesar **{ton_co2} Ton CO₂/tahun**.
    * Kontribusi ini setara dengan Anda telah menanam **{pohon_setara} pohon** per tahun secara konsisten untuk bumi.

    ### 🚗 REKOMENDASI KENDARAAN LISTRIK
    * Berdasarkan budget Rp {st.session_state.user_data.get('budget_rp', 0):,.0f}, AI menyarankan Anda melihat opsi kendaraan listrik yang sesuai di panel sebelah kanan untuk efisiensi jarak tempuh harian {st.session_state.user_data.get('jarak_harian_km', 0)} km Anda.

    ### 📊 TITIK BALIK MODAL (BEP)
    * **Investasi Awal:** Rp {st.session_state.user_data.get('budget_rp', 0):,.0f} (dikurangi nilai trade-in kendaraan lama Rp {st.session_state.user_data.get('trade_in_rp', 0):,.0f}).
    * Proyeksi kumulatif biaya operasional harian dapat Anda pantau secara detail pada grafik visualisasi area di atas.

    ### 🏛️ INSENTIF PEMERINTAH
    * Keuntungan tambahan mencakup **Insentif PPN 1%**, **Pembebasan Pajak Tahunan (STNK)** yang jauh lebih murah, serta **Bebas Aturan Ganjil-Genap** untuk wilayah DKI Jakarta.

    ### ✅ KESIMPULAN & REKOMENDASI
    * Status Keputusan: **{st.session_state.parsed_result.get('title', 'Selesai dianalisis')}**. 
    * *Catatan: Dasar perhitungan di atas sepenuhnya transparan berdasarkan tarif resmi ESDM, Pertamina, dan PLN yang berlaku.*
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    # ─── FOLLOW-UP CHAT MODERN ─────────────────────────────────────────
    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="content-box" style="background: #f8fafc; border-radius: 2rem;">', unsafe_allow_html=True)
    st.markdown('<div class="box-title">💬 Diskusi Lanjut dengan Agent</div>', unsafe_allow_html=True)
    
    for msg in st.session_state.conversation[1:]:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        elif msg["role"] == "assistant":
            if msg.get("content") is not None and isinstance(msg["content"], str):
                if "{" not in msg["content"][:5]: 
                    st.markdown(f'<div class="chat-agent-msg">{msg["content"]}</div>', unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_input = st.text_input("Tanya skenario lain (Misal: Kalau harga BBM naik 20%?)...", label_visibility="collapsed")
        with col_btn:
            submitted = st.form_submit_button("Kirim", use_container_width=True)

    if submitted and user_input:
        def update_thinking_chat(tname, targs):
            st.write(f"⚙️ Analisis: {tname}...")
            
        with st.status("🤖 Agent menyusun jawaban...", expanded=True) as status:
            try:
                response, updated_history = run_agent(user_input, st.session_state.conversation.copy(), status_callback=update_thinking_chat)
                status.update(label="✅ Jawaban Siap!", state="complete", expanded=False)
                st.session_state.conversation = updated_history
                st.rerun()
            except Exception as e:
                status.update(label="❌ Error", state="error")
                st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)
