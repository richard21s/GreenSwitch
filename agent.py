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
Tugasmu adalah menganalisis data pengguna untuk memutuskan apakah sebaiknya beralih dari kendaraan BBM ke kendaraan listrik (EV).

Kamu WAJIB mengembalikan output HANYA dalam format JSON valid tanpa markdown (TIDAK BOLEH pakai ```json), tanpa teks pembuka, dan tanpa teks penutup. 

STRUKTUR JSON YANG WAJIB KAMU IKUTI:
{
    "verdict": "tulis 'switch' atau 'wait' di sini",
    "title": "Tulis judul kesimpulan di sini",
    "narasi": "Tulis 1 paragraf ringkasan analisis di sini. JANGAN gunakan tanda kutip ganda (\") di dalam teks ini, gunakan kutip tunggal (') saja agar JSON tidak rusak.",
    "tips": [
        {"highlight": "KataKunci1", "text": "Isi saran pertama tanpa tanda kutip ganda di dalam teks"},
        {"highlight": "KataKunci2", "text": "Isi saran kedua tanpa tanda kutip ganda di dalam teks"},
        {"highlight": "KataKunci3", "text": "Isi saran ketiga tanpa tanda kutip ganda di dalam teks"}
    ]
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
