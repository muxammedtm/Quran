"""Qur'on matnini yuklash, arabchani normallashtirish va oyatni aniqlash."""
import os
import json
import re
import urllib.request
from rapidfuzz import fuzz, process

# Arabcha harakatlar (tashkil), tatweel va boshqa belgilarni olib tashlash uchun
_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")

_QURAN_URL = "https://api.alquran.cloud/v1/quran/quran-uthmani"


def normalize(text: str) -> str:
    """Arabchani solishtirishga qulay shaklga keltiradi.
    Harakatlarni olib tashlaydi, alef/hamza variantlarini birlashtiradi."""
    text = _DIACRITICS.sub("", text)
    text = re.sub(r"[إأآا]", "ا", text)   # barcha alef variantlari -> ا
    text = text.replace("ى", "ي")
    text = text.replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")
    text = text.replace("ة", "ه")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _download_quran(path: str):
    """quran.json mavjud bo'lmasa, AlQuran Cloud'dan yuklab oladi (bir marta)."""
    print("quran.json topilmadi — yuklab olinmoqda...")
    with urllib.request.urlopen(_QURAN_URL, timeout=60) as r:
        data = json.load(r)
    out = []
    for surah in data["data"]["surahs"]:
        for ayah in surah["ayahs"]:
            out.append({
                "surah": surah["number"],
                "ayah": ayah["numberInSurah"],
                "text": ayah["text"],
            })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"quran.json tayyor: {len(out)} oyat.")
    return out


def load_quran(path: str = "quran.json"):
    """quran.json'ni yuklaydi. Agar fayl yo'q bo'lsa — avtomatik yuklab oladi.
    Format: [{"surah": 1, "ayah": 1, "text": "..."}, ...] (harakatlari bilan)."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = _download_quran(path)
    for a in data:
        a["norm"] = normalize(a["text"])
    return data


def find_ayah(transcript: str, quran: list):
    """Transkripsiyaga eng mos oyatni topadi. (ayah_dict, ishonch_foizi) qaytaradi."""
    norm = normalize(transcript)
    if not norm:
        return None, 0
    choices = [a["norm"] for a in quran]
    best = process.extractOne(norm, choices, scorer=fuzz.token_set_ratio)
    if not best:
        return None, 0
    _, score, idx = best
    return quran[idx], score
