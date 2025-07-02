import os
import discord
from discord.ext import commands
from docx import Document
import pdfplumber
import pandas as pd
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from keep_alive import keep_alive  # ✅ Tambahan keep_alive agar bot aktif 24/7

# 🔐 API Key OpenAI
client = OpenAI(
    api_key=
    "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"
)

# 🧠 Setup Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 📄 Fungsi baca isi file


def baca_dokumen(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == ".docx":
            doc = Document(filepath)
            return "\n".join(
                [p.text for p in doc.paragraphs if p.text.strip()])
        elif ext == ".pdf":
            text = ""
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(filepath)
            return df.to_string(index=False)
    except Exception as e:
        print(f"[ERROR BACA FILE] {e}")
        return None
    return None


# 🌐 Fungsi ambil isi dari website
def ambil_isi_web(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        isi = soup.get_text(separator="\n", strip=True)
        return isi[:3000]  # batasi agar tidak terlalu panjang
    except Exception as e:
        print(f"[ERROR SCRAPE WEB] {e}")
        return None


# 💬 Fungsi tanya ke OpenAI
def tanya_openai(pertanyaan, isi_dokumen=None, isi_web=None):
    system_prompt = (
        "Kamu adalah asisten digital yang bekerja untuk PT ASDP Indonesia Ferry (Persero), "
        "sebuah BUMN yang bergerak di bidang Angkutan Sungai, Danau, dan Penyeberangan (ASDP). "
        "ASDP menyediakan layanan transportasi penyeberangan antar-pulau di Indonesia "
        "untuk penumpang, kendaraan bermotor, dan logistik. "
        "Tugasmu adalah membantu menjawab pertanyaan seputar operasional ASDP, data BBM, dashboard, pelabuhan, "
        "peraturan terkait seperti Perpres 191 Tahun 2014, dan informasi internal perusahaan. "
        "Jawablah dengan akurat, sopan, dan mudah dimengerti.")

    combined_input = ""
    if isi_dokumen:
        combined_input += f"\n\n📄 Berikut isi dokumen:\n{isi_dokumen}"
    if isi_web:
        combined_input += f"\n\n🌐 Berikut isi halaman web:\n{isi_web}"

    combined_input += f"\n\n❓ Pertanyaan:\n{pertanyaan}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "user",
                "content": combined_input
            }],
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR OPENAI] {type(e).__name__}: {e}")
        return f"⚠️ Error dari OpenAI: {e}"


# ✅ Bot aktif
@bot.event
async def on_ready():
    print(f"✅ BOT AKTIF: {bot.user}")


# ✅ Menanggapi pesan masuk
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg = message.content.lower()

    if any(greet in msg for greet in ["halo", "hi", "hai", "hello"]):
        await message.channel.send(
            "👋 Halo! Aku siap bantu soal BBM, laporan, pelabuhan, atau hal lain seputar ASDP. Tanya aja ya!"
        )

    elif any(thanks in msg
             for thanks in ["makasih", "terima kasih", "thanks", "thx"]):
        await message.channel.send("🤗 Sama-sama! Senang bisa bantu~")

    elif "noonreport" in msg or "noon report" in msg:
        await message.channel.send(
            "📈 Ini link *Noon Report BBM Realtime*:\nhttps://lookerstudio.google.com/reporting/26ce604f-b839-4081-86ef-b7f41933b2fd"
        )

    elif "dashboard" in msg:
        await message.channel.send(
            "📊 Ini link *Dashboard BBM ASDP*:\nhttps://lookerstudio.google.com/reporting/cb0a296e-381f-4887-9f81-34a1ad024e71"
        )

    else:
        try:
            dokumen1_path = os.path.join(
                os.getcwd(),
                "Panduan Berdasarkan Peraturan Presiden Nomor 191 Tahun 2014 .docx"
            )
            dokumen2_path = os.path.join(
                os.getcwd(),
                "Usulan Kebutuhan Kuota BBM Triwulan III PT ASDP (1) (1).pdf")

            isi_dokumen1 = baca_dokumen(dokumen1_path) if os.path.exists(
                dokumen1_path) else ""
            isi_dokumen2 = baca_dokumen(dokumen2_path) if os.path.exists(
                dokumen2_path) else ""

            isi_dokumen = isi_dokumen1 + "\n\n" + isi_dokumen2

            url_asdp = "https://asdp.id/"
            isi_web = ambil_isi_web(url_asdp)

            jawaban = tanya_openai(message.content, isi_dokumen, isi_web)
            await message.channel.send(jawaban[:1900])
        except Exception as e:
            await message.channel.send(f"⚠️ Maaf, terjadi error: {e}")
            print(f"[ERROR DISCORD] {e}")

    await bot.process_commands(message)


# ▶️ Jalankan Bot
keep_alive()  # ✅ Tambahkan ini sebelum run
bot.run(
    "MTM4NTE4ODA0NTA4MjU5MTM1Mw.Gzgfzl.kQFPUcwOoxoILgEdjephqsp5hwsB06lHvzxPU0")
