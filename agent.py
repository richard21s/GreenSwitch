import json
import os
import streamlit as st
from openai import OpenAI
from tools import TOOLS_DEFINITION, execute_tool

api_key_rahasia = st.secrets["OPENROUTER_API_KEY"]
client = OpenAI(
    api_key=api_key_rahasia,
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """Kamu adalah GreenSwitch, AI Agent cerdas tingkat lanjut.
Tugasmu adalah menganalisis data pengguna untuk memutuskan apakah sebaiknya beralih dari kendaraan BBM ke kendaraan listrik (EV).

ATURAN EKSEKUSI (WAJIB DIIKUTI):
1. Panggil tools secara berurutan: hitung_biaya_bbm → hitung_biaya_ev → hitung_emisi_co2 → rekomendasi_ev → hitung_bep.
2. JIKA budget pengguna sangat besar TETAPI daya listrik PLN kecil, sarankan MENUNDA (verdict: "wait").

STRUKTUR JSON OUTPUT (WAJIB!):
Kamu HANYA boleh mengembalikan output dalam format JSON valid tanpa markdown. JANGAN gunakan tanda kutip ganda (") di dalam nilai teks, gunakan kutip tunggal (') saja agar JSON tidak rusak!

{
    "verdict": "switch",
    "title": "Tulis judul kesimpulan di sini",
    "narasi": "Tulis paragraf ringkasan di sini tanpa kutip ganda.",
    "tips": [
        {"highlight": "KataKunci", "text": "Isi saran tanpa kutip ganda"}
    ]
}"""


def run_agent(user_message: str, conversation_history: list, status_callback=None) -> tuple[str, list]:
    """
    Menjalankan agent dengan conversation history.
    Returns: (respons_teks, history_terbaru)
    """
    conversation_history.append({"role": "user", "content": user_message})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    MAX_ITERATIONS = 10
    for i in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model="openrouter/free", 
            messages=messages,
            tools=TOOLS_DEFINITION,
            tool_choice="auto",
        )

        # ─── PERBAIKAN 1: CEGAH CRASH JIKA API OPENROUTER ERROR / KOSONG ───
        if not hasattr(response, 'choices') or not response.choices:
            raise ValueError("API OpenRouter mengembalikan respons kosong atau sedang sibuk.")
        # ───────────────────────────────────────────────────────────────────

        msg = response.choices[0].message

        # Jika tidak ada tool call → agent selesai, kembalikan respons
        if not msg.tool_calls:
            final_text = msg.content or ""
            conversation_history.append({"role": "assistant", "content": final_text})
            return final_text, conversation_history

        # ─── PERBAIKAN 2: FORMAT MEMORI ASISTEN SESUAI STANDAR STRICT OPENAI ───
        assistant_msg = {
            "role": "assistant",
            "content": msg.content  # Boleh None
        }
        
        if msg.tool_calls:
            assistant_msg["tool_calls"] = []
            for tc in msg.tool_calls:
                assistant_msg["tool_calls"].append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
        
        messages.append(assistant_msg)
        # ───────────────────────────────────────────────────────────────────────

        tool_results = []
        
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            
            try:
                tool_args = json.loads(tc.function.arguments)
            except Exception as e:
                error_msg = f"Format JSON rusak. Panggil tool ini lagi dengan benar."
                tool_results.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "content": json.dumps({"error": error_msg}) # Jangan pakai 'name' di sini
                })
                if status_callback:
                    status_callback(f"{tool_name} (Auto-Fixing Error...)", {})
                continue 

            if status_callback:
                status_callback(tool_name, tool_args)

            tool_result = execute_tool(tool_name, tool_args)

            # ─── PERBAIKAN 3: FORMAT MEMORI TOOL TANPA PARAMETER USANG ───
            tool_results.append({
                "tool_call_id": tc.id,
                "role": "tool",
                "content": str(tool_result),
                # "name": tool_name  <-- Ini yang kemarin bikin OpenRouter ngambek, kita hapus!
            })
            # ─────────────────────────────────────────────────────────────

        messages.extend(tool_results)

    fallback_json = '{"verdict": "wait", "title": "Sistem Sibuk", "narasi": "Batas waktu pemikiran AI telah habis. Silakan klik Analisis Sekarang lagi.", "tips": []}'
    return fallback_json, conversation_history


def build_initial_prompt(data: dict) -> str:
    """Membuat prompt awal dari form input pengguna."""
    return f"""Tolong analisis profil saya:
- Kendaraan BBM saat ini: {data['jenis_kendaraan_saat_ini']}
- Kategori EV yang ingin dibeli: {data['kategori_ev_diincar']}
- BBM yang digunakan: {data['jenis_bbm']}
- Jarak tempuh harian: {data['jarak_harian_km']} km
- Golongan PLN: {data['golongan_pln']}
- Harga jual kendaraan lama: Rp {data['trade_in_rp']:,.0f}
- Budget maksimal beli EV: Rp {data['budget_rp']:,.0f}

Panggil semua tools secara berurutan. Setelah selesai menganalisis, KEMBALIKAN OUTPUT DALAM BENTUK JSON VALID SESUAI SYSTEM PROMPT."""
