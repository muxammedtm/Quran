"""Audioni Deepgram bilan matnga aylantirish (arab tilini qo'llaydi).
Deepgram kaliti environment'da DEEPGRAM_API_KEY sifatida bo'lishi kerak.
Qo'shimcha kutubxona shart emas — faqat standart Python.
"""
import os
import json
import urllib.request

_DG_KEY = os.environ["DEEPGRAM_API_KEY"]
_URL = "https://api.deepgram.com/v1/listen?model=nova-3&language=ar&punctuate=false"


def transcribe(audio_path: str) -> str:
    """Audio faylni (Telegram voice = ogg) arabcha matnga aylantiradi."""
    with open(audio_path, "rb") as f:
        audio = f.read()
    req = urllib.request.Request(
        _URL,
        data=audio,
        method="POST",
        headers={
            "Authorization": f"Token {_DG_KEY}",
            "Content-Type": "audio/ogg",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    return (
        data["results"]["channels"][0]["alternatives"][0]["transcript"] or ""
    ).strip()
