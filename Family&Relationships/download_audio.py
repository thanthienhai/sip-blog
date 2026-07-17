"""Download English pronunciation MP3 files for each vocabulary entry."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "media" / "audio"


def safe_name(term: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", term.lower()).strip("_")


def words():
    path = ROOT / "build_family_relationships_anki.py"
    spec = importlib.util.spec_from_file_location("family_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [word[0] for word in module.WORDS]


def main():
    AUDIO.mkdir(parents=True, exist_ok=True)
    for term in words():
        target = AUDIO / f"{safe_name(term)}.mp3"
        if target.exists() and target.stat().st_size > 500:
            continue
        url = "https://translate.google.com/translate_tts?" + urlencode(
            {"ie": "UTF-8", "q": term, "tl": "en", "client": "tw-ob"}
        )
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        for attempt in range(3):
            try:
                with urlopen(request, timeout=60) as response:
                    data = response.read()
                if len(data) < 500 or not (data.startswith(b"ID3") or data.startswith(b"\xff")):
                    raise RuntimeError("invalid MP3 response")
                target.write_bytes(data)
                print(f"Downloaded {term}")
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)


if __name__ == "__main__":
    main()
