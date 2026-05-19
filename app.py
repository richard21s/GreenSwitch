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
        background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); 
        border: 1px solid rgba(255, 255, 255, 0.4); padding: 1rem 2rem; 
        border-radius: 24px; display: flex; justify-content: space-between; 
        align-items: center; margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
    }
    .navbar-brand { font-size: 1.8rem; font-weight: 900; background: -webkit-linear-gradient(right, #064e3b, #065f46); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
    .navbar-badge { background: linear-gradient(to right, #d1fae5, #a7f3d0); color: #065f46; padding: 0.5rem 1rem; border-radius: 999px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; border: 1px solid rgba(16, 185, 129, 0.2); }

    /* Core Metrics Cards */
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
    .modern-metric { background: #ffffff; padding: 1.5rem; border-radius: 24px; border: 1px solid #f1f5f9; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); transition: transform 0.2s, box-shadow 0.2s; }
    .modern-metric:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
    .modern-metric-dark { background: #111827; color: white; border: 1px solid #1f2937; }
    .metric-label { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 0.25rem; }
    .metric-val { font-size: 1.75rem; font-weight: 900; margin: 0; }
    
    /* Narrative Box (AI Verdict) */
    .narrative-box { padding: 2rem; border-radius: 2rem; margin-bottom: 1.5rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); position: relative; overflow: hidden; }
    .narrative-switch { background: linear-gradient(to bottom right, #f0fdf4, #ecfdf5); border: 1px solid #d1fae5; }
    .narrative-switch h3 { color: #022c22; font-size: 1.8rem; font-weight: 900; margin-bottom: 0.5rem; }
    .narrative-switch p { color: #065f46; font-size: 1.1rem; line-height: 1.6; font-weight: 500; margin: 0; }
    
    .narrative-wait { background: linear-gradient(to bottom right, #fffbeb, #fefce8); border: 1px solid #fef3c7; }
    .narrative-wait h3 { color: #451a03; font-size: 1.8rem; font-weight: 900; margin-bottom: 0.5rem; }
    .narrative-wait p { color: #92400e; font-size: 1.1rem; line-height: 1.6; font-weight: 500; margin: 0; }

    /* Component Boxes */
    .content-box { background: white; padding: 1.8rem; border-radius: 2rem; border: 1px solid #f1f5f9; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); height: 100%; }
    .box-title { font-size: 1.25rem; font-weight: 800; color: #111827; margin-bottom: 1.2rem; display: flex; align-items: center; gap: 0.5rem; }
    
    /* Tips List */
    .tip-item { display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 1rem; }
    .tip-number { background: #fffbeb; color: #d97706; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem; flex-shrink: 0; border: 1px solid #fef3c7; }
    .tip-text { font-size: 0.95rem; color: #374151; font-weight: 500; line-height: 1.5; margin: 0; }
    .tip-highlight { font-weight: 800; color: #b45309; margin-right: 0.3rem; }

    /* EV Card */
    .ev-card { padding: 1.2rem; border-radius: 1.5rem; border: 1px solid #f1f5f9; margin-bottom: 1rem; transition: background 0.2s; background: #ffffff; }
    .ev-card:hover { background: #ecfdf5; border-color: #d1fae5; }
    .ev-price { background: #ecfdf5; padding: 0.3rem 0.8rem; border-radius: 0.8rem; border: 1px solid #d1fae5; font-weight: 900; color: #065f46; font-size: 0.9rem;}

    /* Subsidy Box */
    .subsidy-box { background: linear-gradient(to bottom right, #111827, #1f2937); padding: 1.8rem; border-radius: 2rem; color: white; position: relative; overflow: hidden; margin-bottom: 1.5rem; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); }
    .subsidy-title { font-size: 0.85rem; font-weight: 800; letter-spacing: 0.1em; color: #34d399; text-transform: uppercase; margin-bottom: 1rem; }
    .subsidy-item { font-size: 0.9rem; color: #d1d5db; margin-bottom: 0.8rem; font-weight: 500; display: flex; gap: 0.5rem;}
    
    /* Chat Box Modern */
    .chat-user-msg { background: #111827; color: white; padding: 1rem 1.2rem; border-radius: 1.2rem 1.2rem 0.2rem 1.2rem; max-width: 85%; margin-left: auto; margin-bottom: 1rem; font-weight: 500; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .chat-agent-msg { background: white; border: 1px solid #e5e7eb; color: #1f2937; padding: 1rem 1.2rem; border-radius: 1.2rem 1.2rem 1.2rem 0.2rem; max-width: 85%; margin-right: auto; margin-bottom: 1rem; font-weight: 500; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05); line-height: 1.6;}

    /* ─── CHAT UI INTEGRATION ─── */
    .chat-container { background: white; padding: 1.8rem; border-radius: 2rem 2rem 0 0; border: 1px solid #f1f5f9; border-bottom: none; }
    
    /* Mengunci Form Streamlit ke Kotak Chat History di Atasnya */
    [data-testid="stForm"] { 
        background: white; 
        border-radius: 0 0 2rem 2rem; 
        border: 1px solid #f1f5f9; 
        border-top: 1px dashed #e2e8f0; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
        padding: 1.5rem 1.8rem; 
        margin-top: -1.3rem; 
        z-index: 10;
        position: relative;
    }
            
    /* ─── ANIMASI GEMINI THINKING (LOADING PILL) ─── */
    @keyframes spin-slow { 100% { transform: rotate(360deg); } }
    @keyframes shine { to { background-position: 200% center; } }
    
    .gemini-pill {
        display: inline-flex; align-items: center; gap: 12px; 
        padding: 12px 24px; background: #ffffff; 
        border-radius: 999px; border: 1px solid #d1fae5; 
        box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.15); 
        margin-bottom: 2rem; margin-left: auto; margin-right: auto;
    }
    .gemini-icon {
        font-size: 1.4rem; 
        animation: spin-slow 3s linear infinite; 
        display: inline-block;
    }
    .gemini-text {
        font-size: 1.05rem; font-weight: 800; 
        background: linear-gradient(90deg, #059669, #34d399, #059669);
        background-size: 200% auto; color: transparent;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shine 2s linear infinite;
        white-space: nowrap;
    }
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

# ─── PREVIEW (Halaman Awal Sebelum Analisis) ──────────────────────────
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


# ─── EKSEKUSI ANALISIS UTAMA DENGAN GEMINI THINKING ───────────────────
if analyze_btn:
    st.session_state.user_data = {
        "jenis_kendaraan_saat_ini": jenis_kendaraan_saat_ini, 
        "kategori_ev_diincar": kategori_ev_diincar,
        "jenis_bbm": jenis_bbm, 
        "jarak_harian_km": jarak_harian,
        "golongan_pln": golongan_pln, 
        "budget_rp": budget_rp, 
        "trade_in_rp": trade_in_rp,
    }
    
    st.session_state.conversation = []
    st.session_state.analysis_done = False
    prompt = build_initial_prompt(st.session_state.user_data)
    
    # Kamus Teks untuk Animasi Loading
    UI_TOOL_NAMES = {
        "startup": "Menghubungkan ke otak AI GreenSwitch...",
        "hitung_biaya_bbm": "Menghitung pengeluaran BBM bulanan...",
        "hitung_biaya_ev": "Mengkalkulasi tarif charging listrik EV...",
        "hitung_emisi_co2": "Menghitung dampak pengurangan emisi karbon...",
        "rekomendasi_ev": "Menelusuri database EV yang sesuai budget...",
        "hitung_bep": "Menyusun proyeksi finansial Break-Even Point...",
        "get_insentif_ev": "Mengecek regulasi subsidi pemerintah...",
        "cari_info_web": "Mencari informasi real-time di internet..."
    }
    
    # Tempat Kosong untuk Animasi Loading Gemini
    think_placeholder = st.empty()
    
    def update_thinking(tname, targs):
        pesan_ui = UI_TOOL_NAMES.get(tname, f"Memproses: {tname}...")
        # Cetak Pil Gemini ke layar
        think_placeholder.markdown(f"""
        <div style="display: flex; justify-content: center; width: 100%;">
            <div class="gemini-pill">
                <span class="gemini-icon">✨</span>
                <span class="gemini-text">{pesan_ui}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    try:
        # Jalankan animasi awal
        update_thinking("startup", {})
        
        # Eksekusi Agen AI
        response, history = run_agent(prompt, [], status_callback=update_thinking)
        
        # Sembunyikan Animasi saat selesai
        think_placeholder.empty() 
        
        st.session_state.conversation = history
        
        # Parsing JSON dari AI
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)
            
            raw_verdict = parsed.get("verdict", parsed.get("keputusan", "switch")).lower()
            raw_title = parsed.get("title", parsed.get("judul", parsed.get("kesimpulan_utama", "Hasil Analisis AI")))
            
            # Filter Judul Cerdas Anti-Datar
            if raw_verdict == "wait" and "tunda" not in raw_title.lower():
                final_title = "Tunda Dulu, Kondisi Belum Proporsional"
            elif raw_verdict == "switch" and "waktu terbaik" not in raw_title.lower() and "beralih" not in raw_title.lower():
                final_title = "Rekomendasi: Waktu Terbaik Beralih ke EV"
            else:
                final_title = raw_title
            
            st.session_state.parsed_result = {
                "verdict": raw_verdict, 
                "title": final_title,
                "narasi": parsed.get("narasi", parsed.get("penjelasan", "Lihat detail analisis di bawah.")),
                "tips": parsed.get("tips", parsed.get("saran", []))
            }
            
            # Mengamankan Teks Tips
            safe_tips = []
            for t in st.session_state.parsed_result["tips"]:
                if isinstance(t, dict): 
                    safe_tips.append({"highlight": t.get("highlight", "Catatan"), "text": t.get("text", str(t))})
                else: 
                    safe_tips.append({"highlight": "Info", "text": str(t)})
                    
            st.session_state.parsed_result["tips"] = safe_tips
            
            if not st.session_state.parsed_result["tips"]: 
                st.session_state.parsed_result["tips"] = [{"highlight": "Catatan", "text": "Silakan pelajari laporan mendalam di bawah."}]
                
        except Exception as json_err:
            # PERBAIKAN: Cegah kata "None" muncul di layar
            teks_narasi = str(response) if response and str(response).strip() not in ["", "None"] else "Sistem berhasil melakukan kalkulasi metrik, namun AI sedang sibuk sehingga gagal merangkum teks kesimpulan."
            st.session_state.parsed_result = {
                "verdict": "wait", 
                "title": "Kalkulasi Selesai (Menunggu AI)",
                "narasi": teks_narasi, 
                "tips": [{"highlight": "Saran Lanjutan", "text": "Anda bisa melihat angka detail pada metrik di bawah, atau klik tombol Analisis sekali lagi."}]
            }
            
        st.session_state.analysis_done = True
        
    except Exception as e:
        st.error(f"❌ Terjadi Kesalahan Eksekusi: {str(e)}")


# ─── RESULT DASHBOARD UTAMA ───────────────────────────────────────────
if st.session_state.analysis_done:
    d = st.session_state.chart_data
    biaya_bbm = d["bbm_data"]["biaya_bulanan_rp"]
    biaya_ev = d["ev_data"]["biaya_bulanan_rp"]
    selisih = biaya_bbm - biaya_ev
    co2_kg = d["co2_data"]["emisi_bbm_kg_per_tahun"] if "emisi_bbm_kg_per_tahun" in d["co2_data"] else d["co2_data"].get("emisi_bbm_network_kg", 0)
    
    u_budget = st.session_state.user_data.get('budget_rp', 300_000_000)
    u_trade = st.session_state.user_data.get('trade_in_rp', 15_000_000)
    investasi_awal_juta = (u_budget - u_trade) / 1_000_000
    if investasi_awal_juta < 0: investasi_awal_juta = 0
    
    res = st.session_state.parsed_result
    verdict_class = "narrative-switch" if res.get("verdict", "").lower() == "switch" else "narrative-wait"
    icon = "✨" if res.get("verdict", "").lower() == "switch" else "⚠️"
    
    # NARRATIVE BOX AI
    st.markdown(f"""
    <div class="narrative-box {verdict_class}">
        <div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.7; margin-bottom: 0.5rem;">Keputusan Agent</div>
        <h3>{icon} {res.get('title', 'Analisis Selesai')}</h3>
        <p>{res.get('narasi', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    # 4 KOTAK METRIK UTAMA
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

    # PEMBAGIAN KOLOM KIRI & KANAN
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        # KOTAK GRAFIK (Digabung agar border sempurna)
        st.markdown('<div style="background: #ffffff; padding: 1.8rem 1.8rem 0 1.8rem; border-radius: 2rem 2rem 0 0; border: 1px solid #f1f5f9; border-bottom: none; box-shadow: 0 -2px 5px rgba(0,0,0,0.02);"><div class="box-title" style="margin-bottom: 0;">📈 Proyeksi Kumulatif 5 Tahun (Dalam Juta Rp)</div></div>', unsafe_allow_html=True)
        
        bulan = list(range(0, 61))
        kum_bbm = [(m * biaya_bbm) / 1_000_000 for m in bulan]
        kum_ev  = [investasi_awal_juta + ((m * biaya_ev) / 1_000_000) for m in bulan]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bulan, y=kum_bbm, fill='tozeroy', name="Operasional BBM", line=dict(color="#ef4444", width=3), fillcolor="rgba(239, 68, 68, 0.04)"))
        fig.add_trace(go.Scatter(x=bulan, y=kum_ev, fill='tozeroy', name="EV + Investasi Net", line=dict(color="#10b981", width=3), fillcolor="rgba(16, 185, 129, 0.04)"))
        
        fig.update_layout(
            margin=dict(l=15, r=15, t=10, b=15), height=300,
            paper_bgcolor='rgba(255,255,255,1)', plot_bgcolor='rgba(255,255,255,1)',
            xaxis=dict(showgrid=False, title="Bulan Ke-"), 
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Pengeluaran (Juta Rp)", ticksuffix=" Jt"),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Penutup border grafik bagian bawah
        st.markdown('<div style="background: #ffffff; height: 1.5rem; border-radius: 0 0 2rem 2rem; border: 1px solid #f1f5f9; border-top: none; margin-top: -1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 1.5rem;"></div>', unsafe_allow_html=True)
        
        # KOTAK TIPS KHUSUS (DIJADIKAN 1 BARIS HTML)
        if res and "tips" in res:
            tips_html = '<div class="content-box"><div class="box-title">💡 Tips Khusus untuk Anda</div>'
            for i, tip in enumerate(res["tips"]):
                highlight = tip.get("highlight", "")
                text = tip.get("text", "")
                tips_html += f'<div class="tip-item"><div class="tip-number">{i+1}</div><p class="tip-text"><span class="tip-highlight">{highlight}:</span> {text}</p></div>'
            tips_html += '</div>'
            st.markdown(tips_html, unsafe_allow_html=True)


    with col_right:
        # KOTAK INSENTIF
        st.markdown("""
        <div class="subsidy-box" style="margin-bottom: 1.5rem;">
            <div class="subsidy-title">🏛️ Insentif Pemerintah</div>
            <div class="subsidy-item"><span>✓</span> Potongan PPN dari 11% menjadi 1%</div>
            <div class="subsidy-item"><span>✓</span> Bebas Ganjil-Genap di DKI Jakarta</div>
            <div class="subsidy-item"><span>✓</span> Subsidi Insentif Langsung s.d Rp 7 Juta</div>
        </div>
        """, unsafe_allow_html=True)
        
        # LOGIKA OPSI KENDARAAN DINAMIS
        kat_ev = st.session_state.user_data.get('kategori_ev_diincar', 'Mobil City Car')
        if kat_ev == "Motor":
            nama_ev, harga_ev_txt, spec_ev = "Smoot Tempur / ALVA One", "Rp 20 - 36 Jt", "Jangkauan 60-70 km | Ekosistem Swap Baterai"
        elif kat_ev == "Mobil City Car":
            nama_ev, harga_ev_txt, spec_ev = "Wuling Air EV Lite / NETA V", "Rp 190 - 299 Jt", "Jangkauan 200-380 km | Durasi AC Fast 35 Min"
        elif kat_ev == "Mobil Sedan/MPV":
            nama_ev, harga_ev_txt, spec_ev = "Wuling Binguo / BYD Dolphin", "Rp 317 - 425 Jt", "Jangkauan 333-410 km | Teknologi Blade Battery"
        else:
            nama_ev, harga_ev_txt, spec_ev = "Hyundai Ioniq 5 / BYD Atto 3", "Rp 515 - 782 Jt", "Platform EV E-GMP | Fitur V2L Port Listrik"

        # KOTAK KENDARAAN (Dirangkai utuh dalam 1 Variabel)
        ev_html = f"""
        <div class="content-box">
            <div class="box-title">🚗 Opsi Unit EV Terdekat</div>
            <div class="ev-card">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                    <div>
                        <h4 style="margin: 0; font-weight: 800; color: #111827; font-size: 1.05rem;">{nama_ev}</h4>
                        <p style="margin: 0; font-size: 0.8rem; font-weight: bold; color: #059669; margin-top: 4px;">{spec_ev}</p>
                    </div>
                    <div class="ev-price">{harga_ev_txt}</div>
                </div>
                <p style="margin: 0; font-size: 0.82rem; color: #64748b; font-weight: 500; line-height: 1.4;">Rekomendasi ini disesuaikan otomatis dengan batas atas pagu anggaran Anda sebesar Rp {u_budget / 1_000_000:,.0f} Juta rupiah.</p>
            </div>
        </div>
        """
        st.markdown(ev_html, unsafe_allow_html=True)


    # PERBAIKAN: Laporan Analisis dirakit utuh TANPA jeda baris kosong agar tidak bocor keluar kotak HTML
    hemat_tahunan = selisih * 12
    pohon_setara = d["co2_data"].get("setara_pohon_ditanam", 0)
    ton_co2 = d["co2_data"].get("pengurangan_ton_per_tahun", 0)
    
    laporan_html = f"""<div style="margin-top: 1.5rem;" class="content-box"><div class="box-title">📑 Laporan Analisis Mendalam</div><h4 style="color: #065f46; font-size: 1rem; margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 800;">💰 ANALISIS BIAYA</h4><ul style="color: #374151; font-weight: 500; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;"><li><b>Biaya BBM Bulanan:</b> Rp {biaya_bbm:,}/bulan</li><li><b>Estimasi Listrik EV Bulanan:</b> Rp {biaya_ev:,}/bulan</li><li><b>Potensi Penghematan:</b> Berselisih <b>Rp {abs(selisih):,}/bulan</b> ({'Lebih Hemat' if selisih > 0 else 'Lebih Mahal'}).</li></ul><h4 style="color: #065f46; font-size: 1rem; margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 800;">🌿 DAMPAK LINGKUNGAN</h4><ul style="color: #374151; font-weight: 500; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;"><li>Memotong emisi karbon sebesar <b>{ton_co2} Ton CO₂/tahun</b>.</li><li>Setara dengan menanam <b>{pohon_setara} pohon</b> per tahun.</li></ul><h4 style="color: #065f46; font-size: 1rem; margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 800;">🚗 REKOMENDASI KENDARAAN</h4><ul style="color: #374151; font-weight: 500; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;"><li>Sesuai budget Rp {u_budget / 1_000_000:,.0f} Juta dan jarak harian {st.session_state.user_data.get('jarak_harian_km', 0)} km, sistem memetakan opsi terbaik di panel samping.</li></ul><h4 style="color: #065f46; font-size: 1rem; margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 800;">📊 TITIK BALIK MODAL (BEP)</h4><ul style="color: #374151; font-weight: 500; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;"><li><b>Investasi Bersih:</b> Rp {(u_budget - u_trade) / 1_000_000:,.0f} Juta (setelah potong trade-in).</li><li>Proyeksi perpotongan modal dapat dipantau di grafik area.</li></ul><h4 style="color: #065f46; font-size: 1rem; margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 800;">✅ KESIMPULAN</h4><ul style="color: #374151; font-weight: 500; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0;"><li>Status Keputusan: <b>{res.get('title', 'Selesai dianalisis')}</b>.</li><li><i>Dasar perhitungan menggunakan tarif resmi ESDM, Pertamina, dan PLN yang berlaku.</i></li></ul></div>"""
    st.markdown(laporan_html, unsafe_allow_html=True)


    # KOTAK CHAT LANJUTAN (Dirangkai utuh dalam 1 Variabel)
    chat_html = '<div style="margin-top: 3rem;" class="chat-container"><div class="box-title">💬 Diskusi Lanjut dengan Agent</div>'
    for msg in st.session_state.conversation[1:]:
        if msg["role"] == "user":
            chat_html += f'<div class="chat-user-msg">{msg["content"]}</div>'
        elif msg["role"] == "assistant":
            if msg.get("content") is not None and isinstance(msg["content"], str):
                if "{" not in msg["content"][:5]: 
                    chat_html += f'<div class="chat-agent-msg">{msg["content"]}</div>'
    chat_html += '</div>'
    
    st.markdown(chat_html, unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # FORM INPUT CHAT BARU
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input: 
            user_input = st.text_input("Tanya skenario lain (Misal: Kalau harga BBM naik 20%?)...", label_visibility="collapsed")
        with col_btn: 
            submitted = st.form_submit_button("Kirim", use_container_width=True)


    # EKSEKUSI CHAT DENGAN ANIMASI GEMINI
    if submitted and user_input:
        UI_TOOL_NAMES_CHAT = {
            "startup": "Menyusun skenario lanjutan...",
            "hitung_biaya_bbm": "Menghitung ulang pengeluaran BBM...", 
            "hitung_biaya_ev": "Mengkalkulasi ulang tarif listrik...",
            "hitung_emisi_co2": "Menyesuaikan perhitungan karbon...", 
            "rekomendasi_ev": "Memfilter ulang database EV...",
            "hitung_bep": "Memperbarui proyeksi Break-Even Point...", 
            "get_insentif_ev": "Mengecek regulasi subsidi...",
            "cari_info_web": "Mencari informasi real-time di internet..."
        }
        
        chat_think_placeholder = st.empty()
        
        def update_thinking_chat(tname, targs): 
            pesan_ui = UI_TOOL_NAMES_CHAT.get(tname, f'Memproses: {tname}...')
            chat_think_placeholder.markdown(f"""
            <div style="display: flex; justify-content: center; width: 100%;">
                <div class="gemini-pill">
                    <span class="gemini-icon">✨</span>
                    <span class="gemini-text">{pesan_ui}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        try:
            update_thinking_chat("startup", {})
            response, updated_history = run_agent(user_input, st.session_state.conversation.copy(), status_callback=update_thinking_chat)
            
            chat_think_placeholder.empty() # Hapus animasi saat selesai
            st.session_state.conversation = updated_history
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
