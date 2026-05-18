import json
import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from tools import TOOLS_DEFINITION, execute_tool

api_key_rahasia = st.secrets["OPENROUTER_API_KEY"]
client = OpenAI(
    api_key=api_key_rahasia,
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """Kamu adalah GreenSwitch, AI Agent yang membantu masyarakat Indonesia 
memutuskan apakah dan kapan sebaiknya beralih dari kendaraan BBM ke kendaraan listrik (EV).

Tugasmu:
1. Saat pengguna mengirim profil mereka, LANGSUNG panggil semua tools yang relevan secara berurutan:
   - hitung_biaya_bbm → hitung_biaya_ev → hitung_emisi_co2 → rekomendasi_ev → hitung_bep → get_insentif_ev
2. Setelah semua data terkumpul, berikan analisis lengkap dalam format yang terstruktur dan mudah dipahami.
3. Berikan rekomendasi yang JELAS: apakah sebaiknya beralih sekarang, menunggu, atau tidak perlu.
4. Selalu gunakan Bahasa Indonesia yang ramah dan mudah dimengerti.
5. Sertakan pertimbangan lingkungan (emisi CO₂) DAN finansial dalam rekomendasi.
6. Untuk pertanyaan follow-up, jawab berdasarkan data yang sudah dihitung sebelumnya.

Format output analisis utama:
💰 ANALISIS BIAYA
🌿 DAMPAK LINGKUNGAN  
🚗 REKOMENDASI KENDARAAN LISTRIK
📊 TITIK BALIK MODAL (BEP)
🏛️ INSENTIF PEMERINTAH
✅ KESIMPULAN & REKOMENDASI

Selalu transparan — jelaskan dasar perhitunganmu."""


def run_agent(user_message: str, conversation_history: list) -> tuple[str, list]:
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
            model="openrouter/free",
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
            tool_result = execute_tool(tool_name, tool_args)

            tool_results.append({
                "tool_call_id": tc.id,
                "role":         "tool",
                "name":         tool_name,
                "content":      tool_result,
            })

        messages.extend(tool_results)

    # Fallback jika melebihi iterasi
    return "Maaf, terjadi kesalahan dalam memproses permintaan. Silakan coba lagi.", conversation_history


def build_initial_prompt(data: dict) -> str:
    """Membuat prompt awal dari form input pengguna."""
    return f"""Tolong analisis profil saya dan berikan rekomendasi lengkap apakah saya sebaiknya beralih ke kendaraan listrik:

**Profil Kendaraan & Kebiasaan:**
- Jenis kendaraan: {data['jenis_kendaraan']}
- BBM yang digunakan: {data['jenis_bbm']}
- Jarak tempuh harian: {data['jarak_harian_km']} km
- Kota: {data.get('kota', 'Indonesia')}

**Profil Finansial & Listrik:**
- Golongan PLN: {data['golongan_pln']}
- Harga jual kendaraan lama (Trade-in): Rp {data['trade_in_rp']:,.0f}
- Budget maksimal untuk beli EV: Rp {data['budget_rp']:,.0f}

Berikan analisis lengkap dengan memanggil semua tools yang relevan, lalu berikan rekomendasi yang jelas."""
