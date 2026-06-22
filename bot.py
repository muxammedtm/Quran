"""Telegram bot: tilovat audiosini qabul qilib, oyatni aniqlaydi va xatolarni ko'rsatadi.
Yengil versiya: bulutli STT API (ffmpeg/PyTorch kerak emas)."""
import asyncio
import os
import tempfile

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from transcribe import transcribe
from quran_data import load_quran, find_ayah
from diff import compare, accuracy

BOT_TOKEN = os.environ["BOT_TOKEN"]          # @BotFather'dan
MATCH_THRESHOLD = 55                          # oyat aniqlash uchun minimal ishonch foizi

quran = load_quran("quran.json")
bot = Bot(BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(m: Message):
    await m.answer(
        "Assalomu alaykum! \U0001F4D6\n"
        "Qur'on tilovatingizni ovozli xabar (voice) qilib yuboring.\n"
        "Men qaysi oyat ekanini aniqlab, qaysi so'z yoki harfda xato "
        "borligini aytaman."
    )


def build_report(ayah, score, exp, rec, issues) -> str:
    acc = accuracy(exp, issues)
    lines = [
        f"\U0001F4CD Oyat: <b>{ayah['surah']}:{ayah['ayah']}</b>  (moslik {score:.0f}%)",
        f"\u2705 Aniqlik: <b>{acc}%</b>",
        f"\n\U0001F4DC To'g'ri matn:\n{ayah['text']}",
    ]
    if not issues:
        lines.append("\n\U0001F389 Xato topilmadi, barakallоh!")
        return "\n".join(lines)

    lines.append("\n\u26A0\uFE0F Topilgan xatolar:")
    for it in issues:
        if it["type"] == "skipped":
            lines.append(f"\u2022 Tashlab ketilgan so'z: <b>{it['expected']}</b>")
        elif it["type"] == "added":
            lines.append(f"\u2022 Ortiqcha so'z: <b>{it['recited']}</b>")
        elif it["type"] == "wrong":
            detail = ""
            for L in it.get("letters", []):
                if L["op"] == "replace":
                    detail += f" «{L['expected']}»→«{L['recited']}»"
                elif L["op"] == "delete":
                    detail += f" tushgan harf:«{L['expected']}»"
                elif L["op"] == "insert":
                    detail += f" qo'shilgan harf:«{L['recited']}»"
            lines.append(
                f"\u2022 Noto'g'ri: <b>{it['recited']}</b> "
                f"(to'g'risi: <b>{it['expected']}</b>){detail}"
            )
    return "\n".join(lines)


@dp.message(F.voice | F.audio)
async def handle_audio(m: Message):
    await m.answer("Qabul qilindi, tahlil qilinmoqda... \u23F3")
    file_id = m.voice.file_id if m.voice else m.audio.file_id
    tg_file = await bot.get_file(file_id)

    # Telegram voice = .ogg (opus). Groq/OpenAI Whisper buni to'g'ridan qabul qiladi.
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "voice.ogg")
        await bot.download_file(tg_file.file_path, src)
        text = transcribe(src)

    if not text:
        await m.answer("Ovozni aniqlay olmadim. Tinchroq joyda qayta urinib ko'ring. \U0001F64F")
        return

    ayah, score = find_ayah(text, quran)
    if not ayah or score < MATCH_THRESHOLD:
        await m.answer(
            "Qaysi oyat ekanini aniq topa olmadim.\n"
            f"Eshitganim: {text}\n"
            "Iltimos, sekinroq va aniqroq o'qib qayta yuboring."
        )
        return

    exp, rec, issues = compare(ayah["text"], text)
    await m.answer(build_report(ayah, score, exp, rec, issues), parse_mode="HTML")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
