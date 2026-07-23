"""Build Neuroeconomics Basic-Reversed Anki deck with images from Openverse."""
from __future__ import annotations

from pathlib import Path
import html
import json
import re
import time
import zipfile
import sqlite3
import tempfile
import hashlib
from copy import deepcopy
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
MEDIA = ROOT / "media"
IMAGES = MEDIA / "images"
IMAGES.mkdir(parents=True, exist_ok=True)

# term (Vietnamese with English name), short label (for file naming), definition
WORDS = [
    (
        "Kinh tế học tân cổ điển (Neoclassical Economics)",
        "neoclassical_economics",
        'Khởi nguồn từ "Sự giàu có của các quốc gia" (Adam Smith), trường phái này cung cấp <b>các mô hình tiên đề thanh lịch về sự lựa chọn của con người nhưng chỉ dự đoán được thô sơ về hành vi thực tế</b> và dễ dàng bị đưa ra các ví dụ phản bác.',
    ),
    (
        "Khoa học thần kinh nhận thức (Cognitive Neuroscience)",
        "cognitive_neuroscience",
        'Lĩnh vực ra đời những năm 1990, nhằm <b>mô tả phần cứng sinh học thần kinh hỗ trợ hành vi lựa chọn</b>.',
    ),
    (
        "Lý thuyết hữu dụng kỳ vọng (Expected Utility Theory - EU)",
        "expected_utility_theory",
        'Do von Neumann và Morgenstern xây dựng, chứng minh rằng <b>người ra quyết định phải cư xử "như thể" họ có một hàm hữu dụng liên tục</b> và hành động nhằm <b>tối đa hóa tổng hữu dụng đạt được</b>.',
    ),
    (
        "Lý thuyết sở thích bộc lộ (Revealed-preference Theory)",
        "revealed_preference_theory",
        'Phát triển từ nguyên lý lựa chọn hợp lý, cho thấy các lựa chọn có thể được lập mô hình toán học; các nhà kinh tế học hành vi sau này đã <b>chứng minh các điểm hạn chế của nó bằng những ví dụ thực nghiệm</b>.',
    ),
    (
        "Lý thuyết trò chơi (Game Theory)",
        "game_theory",
        'Do von Neumann và Morgenstern đặt nền móng, một vấn đề đặc biệt trong lý thuyết hữu dụng nơi <b>các kết quả được tạo ra bởi sự lựa chọn của nhiều người chơi</b>.',
    ),
    (
        "Nghịch lý Allais (Allais Paradox)",
        "allais_paradox",
        'Các lựa chọn theo cặp do Maurice Allais thiết kế (1953), dẫn đến <b>các mô hình sở thích bộc lộ đáng tin cậy nhưng vi phạm tiên đề "độc lập" trung tâm của lý thuyết hữu dụng kỳ vọng</b>.',
    ),
    (
        "Kinh tế học hành vi (Behavioral Economics)",
        "behavioral_economics",
        'Lĩnh vực do các nhà tâm lý học và kinh tế học lập ra, lập luận rằng <b>bằng chứng và ý tưởng từ tâm lý học có thể cải thiện mô hình hành vi con người</b> kế thừa từ kinh tế học tân cổ điển.',
    ),
    (
        "Lý thuyết triển vọng (Prospect Theory)",
        "prospect_theory",
        'Dạng phi chuẩn tắc của lý thuyết hữu dụng kỳ vọng do Kahneman và Tversky phát triển, <b>tích hợp ý tưởng về sự phụ thuộc vào điểm tham chiếu (reference-dependence)</b> và sự biến đổi phi tuyến tính của xác suất khách quan.',
    ),
    (
        "Suy nghiệm (Heuristics)",
        "heuristics",
        'Các trực giác thống kê định hướng hành vi con người, được cho là <b>cung cấp cơ sở tiềm năng cho lý thuyết lựa chọn trong tương lai</b> và có thể suy ra từ thực nghiệm bằng cách quan sát lựa chọn trong các hoàn cảnh khác nhau.',
    ),
    (
        "Lý thuyết dò tìm tín hiệu (Signal Detection Theory)",
        "signal_detection_theory",
        'Một <b>lý thuyết chuẩn tắc về phân loại tín hiệu</b> được sử dụng rộng rãi trong nghiên cứu nhận thức, đánh dấu sự đổi mới khi liên kết trực tiếp hoạt động tế bào thần kinh với hành vi.',
    ),
    (
        "Sự khớp nối tâm lý trắc học – thần kinh trắc học (Psychometric–neurometric match)",
        "psychometric_neurometric_match",
        'Sự tương quan đột phá giữa <b>hoạt động của tế bào thần kinh (neurometric) và các mẫu lựa chọn ngẫu nhiên (psychometric)</b> ở động vật khi phản ứng với các tín hiệu cảm giác nhiễu.',
    ),
    (
        "Mô hình quá trình kép (Dual-process models)",
        "dual_process_models",
        'Các mô hình trong đó <b>hành vi lựa chọn kém hiệu quả ở con người được xem là kết quả của hai (hoặc nhiều) tác nhân độc lập</b> bị mắc kẹt trong trạng thái cân bằng tồi tệ vì lợi ích riêng của chúng.',
    ),
    (
        "Quy luật tương xứng (Matching law)",
        "matching_law",
        'Hiện tượng do Richard Herrnstein đề xuất, trong đó <b>nhiều lựa chọn phản ánh sự chuẩn hóa liên quan đến giá trị của các lựa chọn thay thế khác</b>.',
    ),
    (
        "Kích thích từ trường xuyên sọ (TMS) và Kích thích dòng điện một chiều xuyên sọ (tDCS)",
        "tms_tdcs",
        'Các phương pháp kích thích não không xâm lấn cho phép <b>thay đổi có chọn lọc quá trình xử lý thần kinh liên quan đến hành vi lựa chọn</b>, cung cấp kiến thức về mối quan hệ nhân quả trong mạng lưới ra quyết định.',
    ),
]

QUERY_OVERRIDES = {
    "neoclassical_economics": "Adam Smith economics",
    "cognitive_neuroscience": "brain neuroscience",
    "expected_utility_theory": "decision theory",
    "revealed_preference_theory": "consumer choice economics",
    "game_theory": "game theory matrix",
    "allais_paradox": "decision paradox",
    "behavioral_economics": "behavioral economics",
    "prospect_theory": "Kahneman Tversky",
    "heuristics": "mental shortcuts",
    "signal_detection_theory": "signal detection",
    "psychometric_neurometric_match": "neuron firing",
    "dual_process_models": "system 1 system 2 thinking",
    "matching_law": "behavioral choice",
    "tms_tdcs": "brain stimulation TMS",
}

CSS = """
.card { font-family: Arial, sans-serif; font-size: 20px; line-height: 1.5;
  text-align: center; color: #1a2332; background: #fafaf9; }
.nightMode .card { color: #e2e8f0; background: #0f172a; }
.card img { display: block; max-width: min(92vw, 400px); max-height: 260px;
  margin: 12px auto; border-radius: 10px; object-fit: cover; }
.term { color: #7c2d12; font-size: 27px; font-weight: 700; }
.term-en { color: #57534e; font-size: 16px; font-weight: 400; }
.def { color: #1e3a5f; font-size: 19px; line-height: 1.55;
  text-align: left; margin: 6px 14px; padding: 8px; border-radius: 8px; }
.meta { color: #6b7280; font-size: 12px; margin-top: 10px; }
"""

TEMPLATE_DECK = ROOT.parent / "datetime" / "SIP-DateTime-Basic-Reversed.apkg"
DECK_ID = 1990003001
MODEL_ID = 1783242369234
DECK_NAME = "Neuroeconomics - Basic and Reversed"
MODEL_NAME = "Neuroeconomics Basic (and reversed)"
OUTPUT = ROOT / "SIP-Neuroeconomics-Basic-Reversed.apkg"


def checksum(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def guid(term: str) -> str:
    return hashlib.sha1(f"neuroeconomics:{term}".encode()).hexdigest()[:10]


def safe_name(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def image_tag(label: str) -> str:
    for ext in (".png", ".jpg", ".jpeg"):
        path = IMAGES / f"{label}{ext}"
        if path.is_file():
            return f'<img src="{path.name}" alt="Neuroeconomics illustration">'
    return ""


def term_name(term: str) -> tuple[str, str]:
    """Split 'Vietnamese (English)' into Vietnamese name and English name."""
    if "(" in term:
        vi = term[: term.index("(")].strip()
        en = term[term.index("(") :].strip().rstrip(")")
        return vi, en
    return term, ""


def front_html(term: str) -> str:
    vi, en = term_name(term)
    parts = [f'<div class="term">{html.escape(vi)}</div>']
    if en:
        parts.append(f'<div class="term-en">{html.escape(en)}</div>')
    parts.append(image_tag(label_for(term)))
    parts.append('<div class="meta">Neuroeconomics</div>')
    return "".join(parts)


def def_html(definition: str) -> str:
    return f'<div class="def">{definition}</div>'


def label_for(term: str) -> str:
    for word in WORDS:
        if word[0] == term:
            return safe_name(word[1])
    return safe_name(term)


def fetch_json(url: str):
    request = Request(url, headers={"User-Agent": "SIP-Neuroeconomics-Anki/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def download(url: str, target: Path):
    request = Request(url, headers={"User-Agent": "SIP-Neuroeconomics-Anki/1.0"})
    with urlopen(request, timeout=60) as response:
        target.write_bytes(response.read())


def download_images():
    for term, label, definition in WORDS:
        label_clean = safe_name(label)
        target = IMAGES / f"{label_clean}.jpg"
        if target.exists() or (IMAGES / f"{label_clean}.png").exists():
            continue
        query = QUERY_OVERRIDES.get(label, label.replace("_", " "))
        api = "https://api.openverse.org/v1/images/?" + urlencode({"q": query, "page_size": 10})
        try:
            results = fetch_json(api).get("results", [])
        except Exception as e:
            print(f"Openverse API error for {label}: {e}")
            results = []
        image = None
        for candidate in results:
            if candidate.get("mature") or not candidate.get("thumbnail"):
                continue
            try:
                download(candidate["thumbnail"], target)
                image = candidate
                break
            except Exception as e:
                print(f"  Skipping unavailable image for {label}: {e}")
        if image:
            print(f"Downloaded image for {label}: {image.get('license')} / {image.get('creator', 'unknown')}")
        else:
            print(f"No Openverse image found for {label}, skipping")


def build():
    now = int(time.time())

    with tempfile.TemporaryDirectory(prefix="neuro_anki_") as temp_dir:
        db_path = Path(temp_dir) / "collection.anki2"
        with zipfile.ZipFile(TEMPLATE_DECK) as source:
            db_path.write_bytes(source.read("collection.anki2"))

        connection = sqlite3.connect(db_path)
        try:
            models_raw, decks_raw = connection.execute("SELECT models, decks FROM col").fetchone()
            old_model = next(iter(json.loads(models_raw).values()))
            model = deepcopy(old_model)
            model.update({
                "id": str(MODEL_ID),
                "did": DECK_ID,
                "name": MODEL_NAME,
                "css": CSS,
                "mod": now,
                "flds": [
                    {"name": "Front", "ord": 0, "font": "Liberation Sans", "media": [], "rtl": False, "size": 20, "sticky": False},
                    {"name": "Back", "ord": 1, "font": "Liberation Sans", "media": [], "rtl": False, "size": 20, "sticky": False},
                ],
                "tmpls": [
                    {"name": "Thuật ngữ → Định nghĩa", "ord": 0, "qfmt": "{{Front}}", "afmt": "{{FrontSide}}<hr id=answer>{{Back}}", "bqfmt": "", "bafmt": ""},
                    {"name": "Định nghĩa → Thuật ngữ", "ord": 1, "qfmt": "{{Back}}", "afmt": "{{FrontSide}}<hr id=answer>{{Front}}", "bqfmt": "", "bafmt": ""},
                ],
            })

            old_decks = json.loads(decks_raw)
            source_deck = next(deck for key, deck in old_decks.items() if key != "1")
            deck = deepcopy(source_deck)
            deck.update({
                "id": DECK_ID,
                "name": DECK_NAME,
                "desc": "14 Neuroeconomics concept notes — Neoclassical Economics to TMS/tDCS.",
                "mod": now,
                "usn": -1,
                "lrnToday": [0, 0], "newToday": [0, 0],
                "revToday": [0, 0], "timeToday": [0, 0],
            })
            decks = {"1": old_decks["1"], str(DECK_ID): deck}

            conf = json.loads(connection.execute("SELECT conf FROM col").fetchone()[0])
            conf.update({"activeDecks": [DECK_ID], "curDeck": DECK_ID,
                         "curModel": str(MODEL_ID), "nextPos": len(WORDS) + 1})

            connection.execute("DELETE FROM cards")
            connection.execute("DELETE FROM notes")
            connection.execute("DELETE FROM revlog")
            connection.execute("DELETE FROM graves")
            connection.execute(
                "UPDATE col SET mod=?, scm=?, conf=?, models=?, decks=?, tags=?",
                (now * 1000, now * 1000, json.dumps(conf),
                 json.dumps({str(MODEL_ID): model}), json.dumps(decks),
                 json.dumps({"neuroeconomics": 0})),
            )

            base_id = now * 1000
            for index, (term, label, definition) in enumerate(WORDS, start=1):
                front = front_html(term)
                back = def_html(definition)
                note_id = base_id + index * 10
                note_tags = " neuroeconomics "
                connection.execute(
                    "INSERT INTO notes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (note_id, guid(term), MODEL_ID, now, -1,
                     note_tags, "\x1f".join([front, back]),
                     front, checksum(front), 0, ""),
                )
                for card_ord in range(2):
                    card_id = note_id + card_ord + 1
                    connection.execute(
                        "INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (card_id, note_id, DECK_ID, card_ord, now, -1,
                         0, 0, index, 0, 0, 0, 0, 0, 0, 0, 0, ""),
                    )
            connection.commit()
        finally:
            connection.close()

        media_files = sorted(
            p for p in IMAGES.rglob("*")
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
        )
        media_map = {str(idx): p.name for idx, p in enumerate(media_files)}

        with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as package:
            package.write(db_path, "collection.anki2")
            package.writestr("media", json.dumps(media_map))
            for idx, path in enumerate(media_files):
                package.write(path, str(idx))

    card_count = len(WORDS) * 2
    print(f"Created {OUTPUT.name}: {len(WORDS)} notes, {card_count} cards, {len(media_files)} images")


if __name__ == "__main__":
    download_images()
    build()
