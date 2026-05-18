# app.py — EnergiCerdas UI (Streamlit)
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from agent import run_agent, build_initial_prompt
from data import HARGA_BBM, KONSUMSI_BBM, TARIF_PLN
from tools import hitung_biaya_bbm, hitung_biaya_ev, hitung_emisi_co2

# ─── Konfigurasi halaman ──────────────────────────────────────────────
st.set_page_config(
    page_title="GreenSwitch — AI Agent Transisi Energi",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS kustom ───────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0f4c35 0%, #1a7a56 50%, #0d3d5c 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
    }
    .main-header h1 { font-size: 2.2rem; margin: 0; }
    .main-header p  { opacity: 0.85; margin: 0.5rem 0 0; }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        text-align: center;
    }
    .metric-card h3 { font-size: 1.5rem; margin: 0; color: #1a7a56; }
    .metric-card p  { font-size: 0.8rem; color: #64748b; margin: 0.25rem 0 0; }
    .chat-user { background: #e8f5e9; border-radius: 10px; padding: 0.8rem 1rem; margin: 0.5rem 0; }
    .chat-agent { background: #f1f5f9; border-radius: 10px; padding: 0.8rem 1rem; margin: 0.5rem 0; border-left: 3px solid #1a7a56; }
    .step-badge {
        display: inline-block;
        background: #1a7a56;
        color: white;
        font-size: 0.75rem;
        padding: 2px 10px;
        border-radius: 20px;
        margin-bottom: 0.5rem;
    }
    .warning-box {
        background: #fff8e1;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────────
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "chart_data" not in st.session_state:
    st.session_state.chart_data = {}

# ─── HEADER ──────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>⚡ EnergiCerdas</h1>
    <p>AI Agent untuk Transisi Kendaraan BBM → Listrik | TechnoFest 2026 · Tim RDR</p>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR: Form Input ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 Profil Kamu")
    st.markdown('<span class="step-badge">LANGKAH 1 — Isi Data</span>', unsafe_allow_html=True)

    jenis_kendaraan = st.selectbox(
        "Jenis Kendaraan",
        ["Motor", "Mobil City Car", "Mobil Sedan/MPV", "SUV"],
        help="Pilih jenis kendaraan BBM yang kamu gunakan saat ini"
    )

    jenis_bbm = st.selectbox(
        "BBM yang Digunakan",
        ["Pertalite", "Pertamax", "Pertamax Turbo"]
    )

    jarak_harian = st.slider(
        "Jarak Tempuh Harian (km)",
        min_value=5, max_value=150, value=30, step=5
    )

    golongan_pln = st.selectbox(
        "Golongan Listrik PLN",
        ["R-1 / 900 VA", "R-1 / 1300 VA", "R-1 / 2200 VA",
         "R-2 / 3500-5500 VA", "R-3 / 6600 VA+"],
        index=1
    )

    kota = st.text_input("Kota Domisili", value="Jakarta")

    st.markdown("---")
    st.markdown("💰 **Budget Beli EV**")
    budget_juta = st.number_input(
        "Budget (juta Rupiah)",
        min_value=20, max_value=2000, value=300, step=10
    )
    budget_rp = budget_juta * 1_000_000

    st.markdown(f"**Rp {budget_rp:,.0f}**")

    st.markdown("---")
    st.markdown("💰 **Nilai Jual Kendaraan Lama (Trade-in)**")
    trade_in_juta = st.number_input(
        "Perkiraan harga jual kendaraan BBM kamu saat ini (Juta Rp). Isi 0 jika tidak dijual.",
        min_value=0, max_value=1000, value=15, step=1
    )
    trade_in_rp = trade_in_juta * 1_000_000
    analyze_btn = st.button("🔍 Analisis Sekarang!", type="primary", use_container_width=True)

    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.conversation  = []
        st.session_state.analysis_done = False
        st.session_state.user_data     = {}
        st.session_state.chart_data    = {}
        st.rerun()

# ─── QUICK PREVIEW (live sebelum analisis) ───────────────────────────
if not st.session_state.analysis_done:
    st.markdown("#### 📊 Preview Cepat")
    bbm_data = hitung_biaya_bbm(jenis_kendaraan, jarak_harian, jenis_bbm)
    ev_data  = hitung_biaya_ev(jenis_kendaraan, jarak_harian, golongan_pln)
    co2_data = hitung_emisi_co2(jenis_kendaraan, jarak_harian, jenis_bbm, golongan_pln)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <h3>Rp {bbm_data['biaya_bulanan_rp']:,}</h3>
            <p>Biaya BBM / bulan</p></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <h3>Rp {ev_data['biaya_bulanan_rp']:,}</h3>
            <p>Estimasi listrik EV / bulan</p></div>""", unsafe_allow_html=True)
    with col3:
        selisih = bbm_data['biaya_bulanan_rp'] - ev_data['biaya_bulanan_rp']
        color = "#1a7a56" if selisih > 0 else "#dc2626"
        st.markdown(f"""<div class="metric-card">
            <h3 style="color:{color}">Rp {abs(selisih):,}</h3>
            <p>{'Potensi hemat' if selisih > 0 else 'Lebih mahal'} / bulan</p></div>""",
            unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card">
            <h3>{co2_data['pengurangan_ton_per_tahun']} ton</h3>
            <p>Potensi hemat CO₂ / tahun</p></div>""", unsafe_allow_html=True)

    # Simpan untuk chart
    st.session_state.chart_data = {
        "bbm_data": bbm_data,
        "ev_data":  ev_data,
        "co2_data": co2_data,
    }

    st.markdown("---")
    st.markdown("""<div class="warning-box">
        👆 Klik <b>Analisis Sekarang!</b> di sidebar untuk mendapat rekomendasi lengkap dari AI Agent.
    </div>""", unsafe_allow_html=True)

# ─── GRAFIK PERBANDINGAN ──────────────────────────────────────────────
def render_charts(bbm_monthly, ev_monthly, harga_ev, co2_data):
    st.markdown("#### 📈 Visualisasi Perbandingan")
    tab1, tab2 = st.tabs(["💰 Biaya Kumulatif", "🌿 Emisi CO₂"])

    with tab1:
        bulan = list(range(0, 61))
        kumulatif_bbm = [m * bbm_monthly for m in bulan]
        kumulatif_ev  = [harga_ev + m * ev_monthly for m in bulan]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bulan, y=kumulatif_bbm, name="BBM (tanpa beli baru)",
                                 line=dict(color="#ef4444", width=2.5)))
        fig.add_trace(go.Scatter(x=bulan, y=kumulatif_ev, name="EV (termasuk harga beli)",
                                 line=dict(color="#1a7a56", width=2.5)))

        # BEP
        bep_idx = next((i for i in bulan if kumulatif_ev[i] <= kumulatif_bbm[i]), None)
        if bep_idx:
            fig.add_vline(x=bep_idx, line_dash="dash", line_color="#f59e0b",
                          annotation_text=f"BEP: Bulan ke-{bep_idx}")

        fig.update_layout(
            title="Perbandingan Biaya Kumulatif 5 Tahun",
            xaxis_title="Bulan", yaxis_title="Total Biaya (Rp)",
            hovermode="x unified", height=350,
            yaxis=dict(tickformat=",.0f"),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        categories = ["Kendaraan BBM", "Kendaraan Listrik (EV)"]
        values     = [co2_data["emisi_bbm_kg_per_tahun"], co2_data["emisi_ev_kg_per_tahun"]]
        colors     = ["#ef4444", "#1a7a56"]

        fig2 = go.Figure(go.Bar(
            x=categories, y=values, marker_color=colors,
            text=[f"{v:,.0f} kg" for v in values], textposition="outside"
        ))
        fig2.update_layout(
            title=f"Emisi CO₂ per Tahun — Hemat {co2_data['pengurangan_ton_per_tahun']} ton/tahun "
                  f"(≈ {co2_data['setara_pohon_ditanam']} pohon)",
            yaxis_title="kg CO₂ per Tahun", height=350,
            plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig2, use_container_width=True)

# ─── EKSEKUSI ANALISIS ────────────────────────────────────────────────
if analyze_btn:
    st.session_state.user_data = {
        "jenis_kendaraan": jenis_kendaraan,
        "jenis_bbm":       jenis_bbm,
        "jarak_harian_km": jarak_harian,
        "golongan_pln":    golongan_pln,
        "kota":            kota,
        "budget_rp":       budget_rp,
        "trade_in_rp":     trade_in_rp,
    }
    st.session_state.conversation  = []
    st.session_state.analysis_done = False

    prompt = build_initial_prompt(st.session_state.user_data)

    with st.spinner("🤖 Agent sedang menganalisis profil kamu..."):
        try:
            response, history = run_agent(prompt, [])
            st.session_state.conversation  = history
            st.session_state.analysis_done = True
        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}\n\nPastikan API key OpenAI sudah diset dengan benar di file .env")

# ─── TAMPILKAN HASIL ANALISIS ─────────────────────────────────────────
if st.session_state.analysis_done:
    # Render charts terlebih dahulu
    if st.session_state.chart_data:
        d = st.session_state.chart_data
        render_charts(
            d["bbm_data"]["biaya_bulanan_rp"],
            d["ev_data"]["biaya_bulanan_rp"],
            budget_rp,
            d["co2_data"],
        )

    st.markdown("---")
    st.markdown("#### 🤖 Analisis & Rekomendasi dari EnergiCerdas Agent")

    # Tampilkan percakapan
    for msg in st.session_state.conversation:
        if msg["role"] == "user":
            with st.expander("📝 Input Profil Kamu", expanded=False):
                st.text(msg["content"])
        elif msg["role"] == "assistant":
            st.markdown(f'<div class="chat-agent">{msg["content"]}</div>',
                        unsafe_allow_html=True)

    # ─── CHAT FOLLOW-UP ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 💬 Tanya Lanjut ke Agent")
    st.markdown("Contoh: *'Kalau harga BBM naik 20% gimana?'* atau *'EV mana yang paling hemat?'*")

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Pertanyaan kamu:", placeholder="Ketik pertanyaan di sini...")
        submitted  = st.form_submit_button("Kirim →", type="primary")

    if submitted and user_input:
        with st.spinner("Agent sedang menjawab..."):
            try:
                response, updated_history = run_agent(
                    user_input, st.session_state.conversation.copy()
                )
                st.session_state.conversation = updated_history
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ─── FOOTER ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#94a3b8;font-size:0.8rem">
    EnergiCerdas · TechnoFest 2026 · Tim RDR · Universitas — AI for Environmental & Social Impact<br>
    Data referensi: PLN, Pertamina, IPCC, Ditjen EBTKE ESDM 2023
</div>
""", unsafe_allow_html=True)