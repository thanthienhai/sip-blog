"""Download open-licensed thumbnail images for Family & Relationships cards.

Sources and licence details are written to media/image_attributions.json.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / "media" / "images"
ATTRIBUTIONS = ROOT / "media" / "image_attributions.json"

QUERY_OVERRIDES = {
    "childhood": "children playing", "adolescence": "teenager", "adulthood": "young adult",
    "get married": "wedding couple", "newlywed": "wedding couple", "pregnancy": "pregnant woman",
    "give birth": "newborn baby", "raise a child": "parenting", "adopt": "adoption family",
    "separated": "couple apart", "widowed": "elderly widow", "relationship": "friends together",
    "friendship": "friends together", "best friend": "friends together", "classmate": "students classroom",
    "colleague": "coworkers", "acquaintance": "people talking", "partner": "couple together",
    "date": "couple restaurant", "fall in love": "romantic couple", "get along": "friends laughing",
    "have in common": "friends hobbies", "close to": "family hug", "trust": "trust handshake",
    "respect": "respectful conversation", "upbringing": "parenting", "parenting": "parenting",
    "guardian": "adult child", "take care of": "child care", "look after": "child care",
    "support": "supportive family", "protect": "parent protecting child", "discipline": "parent child",
    "set boundaries": "family conversation", "role model": "mentor child", "household chores": "family cleaning",
    "quality time": "family activity", "argument": "arguing couple", "disagreement": "conversation disagreement",
    "misunderstanding": "confused conversation", "conflict": "family conflict", "criticize": "argument conversation",
    "blame": "argument conversation", "disappoint": "sad person", "betray": "sad friendship",
    "break up": "couple apart", "make up": "friends hugging", "apologize": "apology", "forgive": "forgiveness",
    "compromise": "negotiation", "reconcile": "friends hugging", "affection": "family hug",
    "love": "family love", "bond": "family hug", "loyalty": "friends together", "honesty": "honest conversation",
    "empathy": "comforting friend", "responsibility": "parent child", "independence": "young adult",
    "generation gap": "grandparent teenager", "family tradition": "family dinner",
}

REUSED_IMAGES = {
    "bond": "affection", "loyalty": "friendship", "honesty": "trust",
    "empathy": "support", "responsibility": "parenting", "independence": "adulthood",
    "generation_gap": "generation", "family_tradition": "quality_time",
}


def load_words():
    path = ROOT / "build_family_relationships_anki.py"
    spec = importlib.util.spec_from_file_location("family_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.WORDS


def safe_name(term: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", term.lower()).strip("_")


def fetch_json(url: str):
    request = Request(url, headers={"User-Agent": "SIP-Family-Anki/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def download(url: str, target: Path):
    request = Request(url, headers={"User-Agent": "SIP-Family-Anki/1.0"})
    with urlopen(request, timeout=60) as response:
        target.write_bytes(response.read())


def main():
    IMAGES.mkdir(parents=True, exist_ok=True)
    attributions = json.loads(ATTRIBUTIONS.read_text()) if ATTRIBUTIONS.exists() else {}
    for word in load_words():
        term = word[0]
        target = IMAGES / f"{safe_name(term)}.jpg"
        if (IMAGES / f"{safe_name(term)}.png").exists() or target.exists():
            continue
        query = QUERY_OVERRIDES.get(term, term)
        api = "https://api.openverse.org/v1/images/?" + urlencode({"q": query, "page_size": 10})
        results = fetch_json(api).get("results", [])
        image = None
        for candidate in results:
            if candidate.get("mature") or not candidate.get("thumbnail"):
                continue
            try:
                download(candidate["thumbnail"], target)
                image = candidate
                break
            except Exception as error:
                print(f"Skipping unavailable image for {term}: {error}")
        if image is None:
            raise RuntimeError(f"No downloadable Openverse image found for {term!r}")
        attributions[safe_name(term)] = {
            "term": term, "query": query, "title": image.get("title"),
            "creator": image.get("creator"), "license": image.get("license"),
            "license_url": image.get("license_url"), "source_url": image.get("foreign_landing_url"),
            "attribution": image.get("attribution"),
        }
        ATTRIBUTIONS.write_text(json.dumps(attributions, ensure_ascii=False, indent=2) + "\n")
        print(f"Downloaded {term}: {image.get('license')} / {image.get('creator')}")
    for target, source in REUSED_IMAGES.items():
        if target not in attributions and source in attributions:
            attributions[target] = {
                **attributions[source], "term": target.replace("_", " "),
                "reused_from": source,
            }
    ATTRIBUTIONS.write_text(json.dumps(attributions, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
