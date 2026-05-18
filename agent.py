import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
from tools import TOOLS_DEFINITION, execute_tool


api_key_rahasia = st.secrets["OPENROUTER_API_KEY"]
client = OpenAI(
    api_key=api_key_rahasia,
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """Kamu adalah GreenSwitch, AI Agent cerdas tingkat lanjut.
Tugasmu adalah menganalisis data pengguna untuk memutuskan apakah dan kapan sebaiknya mereka beralih dari kendaraan BBM ke kendaraan listrik (EV).

ATURAN EKSEKUSI:
1. Panggil tools secara berurutan: hitung_biaya_bbm → hitung_biaya_ev → hitung_emisi_co2 → rekomendasi_ev → hitung_bep → get_insentif_ev.
2. JIKA budget pengguna sangat besar TETAPI daya listrik PLN mereka sangat kecil (misal 900 VA atau 1300 VA), sarankan MENUNDA (verdict: "wait") dan sarankan upgrade daya PLN.
3. JIKA penghematan bulanan sangat kecil dan budget tidak cukup untuk EV, sarankan MENUNDA.
4. JIKA penghematan besar dan budget cukup, sarankan BERALIH (verdict: "switch").

ATURAN OUTPUT (WAJIB JSON):
Kamu WAJIB mengembalikan output HANYA dalam format JSON yang valid persis seperti struktur di bawah ini:

{
    "verdict": "switch", 
    "title": "Waktu Terbaik Beralih ke EV",
    "narasi": "Satu paragraf ringkasan singkat (Executive Summary).",
    "tips": [
        {"highlight": "Pastikan", "text": "rumah Anda memiliki grounding yang baik."}
    ],
    "analisis_lengkap": "Di sini, tuliskan analisis komprehensifmu menggunakan format Markdown. WAJIB mencakup struktur berikut: \n\n### 💰 ANALISIS BIAYA\n...\n### 🌿 DAMPAK LINGKUNGAN\n...\n### 🚗 REKOMENDASI KENDARAAN LISTRIK\n...\n### 📊 TITIK BALIK MODAL (BEP)\n...\n### 🏛️ INSENTIF PEMERINTAH\n...\n### ✅ KESIMPULAN & REKOMENDASI\n..."
}"""


def run_agent(user_message: str, conversation_history: list, status_callback=None) -> tuple[str, list]:
    """
    Menjalankan agent dengan conversation history.
    Returns: (respons_teks, history_terbaru)
    """
    # Tambah pesan user ke history
    conversation_history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    # Loop agentic: agent bisa panggil tools berkali-kali
    MAX_ITERATIONS = 10
    for i in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model="openrouter/free",   # hemat biaya, performa bagus
            messages=messages,
            tools=TOOLS_DEFINITION,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        # Jika tidak ada tool call → agent selesai, kembalikan respons
        if not msg.tool_calls:
            final_text = msg.content
            conversation_history.append({"role": "assistant", "content": final_text})
            return final_text, conversation_history

        # Proses semua tool calls yang diminta agent
        messages.append(msg)

        tool_results = []
        for tc in msg.tool_calls:
            tool_name   = tc.function.name
            tool_args   = json.loads(tc.function.arguments)

            if status_callback:
                status_callback(tool_name, tool_args)

            tool_result = execute_tool(tool_name, tool_args)

            tool_results.append({
                "tool_call_id": tc.id,
                "role":         "tool",
                "name":         tool_name,
                "content":      str(tool_result),
            })

        messages.extend(tool_results)

    # Fallback jika melebihi iterasi
    return "Maaf, terjadi kesalahan dalam memproses permintaan. Silakan coba lagi.", conversation_history


def build_initial_prompt(data: dict) -> str:
    """Membuat prompt awal dari form input pengguna."""
    return f"""Tolong analisis profil saya dan berikan rekomendasi lengkap apakah saya sebaiknya beralih ke kendaraan listrik:

**Profil Kendaraan & Kebiasaan:**
- Kendaraan BBM saat ini: {data['jenis_kendaraan_saat_ini']}
- Kategori EV yang ingin dibeli: {data['kategori_ev_diincar']}
- BBM yang digunakan: {data['jenis_bbm']}
- Jarak tempuh harian: {data['jarak_harian_km']} km
- Kota: {data.get('kota', 'Indonesia')}

**Profil Finansial & Listrik:**
- Golongan PLN: {data['golongan_pln']}
- Harga jual kendaraan lama (Trade-in): Rp {data['trade_in_rp']:,.0f}
- Budget maksimal untuk beli EV: Rp {data['budget_rp']:,.0f}

AI Agent harus memanggil fungsi `hitung_biaya_bbm` dengan parameter kendaraan saat ini, dan memanggil fungsi `hitung_biaya_ev` serta `rekomendasi_ev` menggunakan parameter kategori EV yang diincar.
Berikan analisis lengkap dengan memanggil semua tools yang relevan, lalu berikan rekomendasi yang jelas."""
