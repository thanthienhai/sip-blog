"""Build three dependency-free Anki decks for Family & Relationships.

The repository already contains Date & Time decks made with genanki.  To keep
this topic reproducible on machines without third-party Python packages, this
builder reuses their empty Anki schema and writes notes with Python's standard
library only.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import html
import json
import re
import sqlite3
import tempfile
import time
import zipfile


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
MEDIA = ROOT / "media"
IMAGES = MEDIA / "images"
AUDIO = MEDIA / "audio"

# term, IPA, Vietnamese meaning, example, useful language, CEFR, topic
WORDS = [
    ("family", "/ˈfæməli/", "gia đình", "Family is very important to her.", "a close family; start a family; family life", "A1", "immediate_family"),
    ("parent", "/ˈperənt/", "cha hoặc mẹ; phụ huynh", "Every parent wants their child to feel safe.", "single parent; strict parent; parent and child", "A1", "immediate_family"),
    ("mother", "/ˈmʌðər/", "mẹ", "My mother taught me how to cook.", "working mother; mother and daughter", "A1", "immediate_family"),
    ("father", "/ˈfɑːðər/", "cha, bố", "Her father works from home.", "proud father; father and son", "A1", "immediate_family"),
    ("son", "/sʌn/", "con trai", "Their son has just started school.", "youngest son; only son", "A1", "immediate_family"),
    ("daughter", "/ˈdɔːtər/", "con gái", "Our daughter loves reading stories.", "eldest daughter; teenage daughter", "A1", "immediate_family"),
    ("child", "/tʃaɪld/", "đứa trẻ; con", "The child is playing with her grandparents.", "only child; raise a child; child development", "A1", "immediate_family"),
    ("sibling", "/ˈsɪblɪŋ/", "anh, chị hoặc em ruột", "I have one sibling, an older sister.", "younger sibling; sibling rivalry; sibling relationship", "B1", "immediate_family"),
    ("brother", "/ˈbrʌðər/", "anh hoặc em trai", "My brother and I share a room.", "older brother; little brother; twin brother", "A1", "immediate_family"),
    ("sister", "/ˈsɪstər/", "chị hoặc em gái", "His sister lives in another city.", "elder sister; baby sister; twin sister", "A1", "immediate_family"),
    ("husband", "/ˈhʌzbənd/", "chồng", "Her husband usually prepares dinner.", "loving husband; future husband", "A1", "immediate_family"),
    ("wife", "/waɪf/", "vợ", "He met his wife at university.", "former wife; husband and wife", "A1", "immediate_family"),
    ("spouse", "/spaʊs/", "vợ hoặc chồng; bạn đời hợp pháp", "You may bring your spouse to the event.", "surviving spouse; spouse visa", "B2", "immediate_family"),
    ("couple", "/ˈkʌpəl/", "cặp đôi; vợ chồng", "The couple celebrated ten years together.", "married couple; young couple; happy couple", "A2", "immediate_family"),
    ("only child", "/ˌoʊnli ˈtʃaɪld/", "con một", "As an only child, Mia spent a lot of time with adults.", "be an only child", "A2", "immediate_family"),
    ("twins", "/twɪnz/", "cặp song sinh", "The twins look alike but have different personalities.", "identical twins; twin brothers; twin sisters", "A2", "immediate_family"),
    ("nuclear family", "/ˌnuːkliər ˈfæməli/", "gia đình hạt nhân", "A nuclear family usually consists of parents and children.", "live in a nuclear family", "B2", "immediate_family"),
    ("single-parent family", "/ˌsɪŋɡəl ˈperənt ˈfæməli/", "gia đình đơn thân", "She grew up in a single-parent family.", "support a single-parent family", "B2", "immediate_family"),

    ("relative", "/ˈrelətɪv/", "họ hàng", "We visit every relative during the holiday.", "close relative; distant relative; blood relative", "A2", "extended_family"),
    ("grandparent", "/ˈɡrænperənt/", "ông hoặc bà", "A grandparent can share valuable family stories.", "live with a grandparent; proud grandparent", "A2", "extended_family"),
    ("grandfather", "/ˈɡrænfɑːðər/", "ông", "My grandfather taught me to ride a bicycle.", "maternal grandfather; paternal grandfather", "A1", "extended_family"),
    ("grandmother", "/ˈɡrænmʌðər/", "bà", "Her grandmother makes wonderful soup.", "maternal grandmother; paternal grandmother", "A1", "extended_family"),
    ("grandchild", "/ˈɡræntʃaɪld/", "cháu (của ông bà)", "Their first grandchild was born in May.", "youngest grandchild; first grandchild", "B1", "extended_family"),
    ("grandson", "/ˈɡrænsʌn/", "cháu trai (của ông bà)", "The proud grandfather showed us a photo of his grandson.", "young grandson; eldest grandson", "A2", "extended_family"),
    ("granddaughter", "/ˈɡrændɔːtər/", "cháu gái (của ông bà)", "My granddaughter calls me every weekend.", "young granddaughter; eldest granddaughter", "A2", "extended_family"),
    ("uncle", "/ˈʌŋkəl/", "chú, bác hoặc cậu", "My uncle lives near the coast.", "favorite uncle; uncle and aunt", "A1", "extended_family"),
    ("aunt", "/ænt/", "cô, dì hoặc bác gái", "Her aunt gave her some useful advice.", "great-aunt; uncle and aunt", "A1", "extended_family"),
    ("cousin", "/ˈkʌzən/", "anh, chị hoặc em họ", "I often play football with my cousin.", "first cousin; distant cousin", "A1", "extended_family"),
    ("nephew", "/ˈnefjuː/", "cháu trai (con của anh chị em)", "My nephew is learning to walk.", "young nephew; niece and nephew", "B1", "extended_family"),
    ("niece", "/niːs/", "cháu gái (con của anh chị em)", "His niece wants to become a doctor.", "favorite niece; niece and nephew", "B1", "extended_family"),
    ("in-laws", "/ˈɪn lɔːz/", "gia đình bên vợ hoặc chồng", "We are spending the weekend with my in-laws.", "meet the in-laws; get along with the in-laws", "B2", "extended_family"),
    ("mother-in-law", "/ˈmʌðər ɪn lɔː/", "mẹ vợ hoặc mẹ chồng", "My mother-in-law taught me her family recipe.", "future mother-in-law", "B1", "extended_family"),
    ("father-in-law", "/ˈfɑːðər ɪn lɔː/", "bố vợ hoặc bố chồng", "Her father-in-law helped repair the door.", "future father-in-law", "B1", "extended_family"),
    ("family tree", "/ˈfæməli triː/", "cây gia phả", "We made a family tree for our history project.", "draw a family tree; trace a family tree", "B1", "extended_family"),
    ("generation", "/ˌdʒenəˈreɪʃn/", "thế hệ", "Three generations live in the same house.", "younger generation; older generation; future generations", "B1", "extended_family"),

    ("childhood", "/ˈtʃaɪldhʊd/", "thời thơ ấu", "She had a happy childhood in the countryside.", "early childhood; childhood memory; during childhood", "B1", "life_events"),
    ("adolescence", "/ˌædəˈlesəns/", "tuổi vị thành niên", "Adolescence can be a period of rapid change.", "during adolescence; early adolescence", "B2", "life_events"),
    ("adulthood", "/əˈdʌlthʊd/", "tuổi trưởng thành", "Friendships often change during adulthood.", "early adulthood; reach adulthood", "B2", "life_events"),
    ("get married", "/ɡet ˈmærid/", "kết hôn", "They plan to get married next spring.", "get married to someone; decide to get married", "A2", "life_events"),
    ("wedding", "/ˈwedɪŋ/", "đám cưới", "Their wedding was small and joyful.", "wedding ceremony; wedding reception; attend a wedding", "A2", "life_events"),
    ("marriage", "/ˈmærɪdʒ/", "hôn nhân", "A strong marriage requires honest communication.", "happy marriage; marriage certificate; save a marriage", "B1", "life_events"),
    ("newlywed", "/ˈnuːliwed/", "người mới kết hôn", "A newlywed couple moved into the apartment next door.", "newlywed couple; young newlywed", "B2", "life_events"),
    ("pregnancy", "/ˈpreɡnənsi/", "thai kỳ; sự mang thai", "She stayed active throughout her pregnancy.", "healthy pregnancy; during pregnancy", "B2", "life_events"),
    ("give birth", "/ɡɪv bɜːrθ/", "sinh con", "She will give birth in early September.", "give birth to a baby", "B1", "life_events"),
    ("raise a child", "/reɪz ə tʃaɪld/", "nuôi dạy một đứa trẻ", "It takes patience to raise a child.", "raise a child alone; help raise a child", "B1", "life_events"),
    ("adopt", "/əˈdɑːpt/", "nhận nuôi", "The couple decided to adopt a child.", "adopt a baby; legally adopt", "B2", "life_events"),
    ("divorce", "/dɪˈvɔːrs/", "ly hôn; sự ly hôn", "They chose to divorce after years of conflict.", "get a divorce; file for divorce", "B2", "life_events"),
    ("separated", "/ˈsepəreɪtɪd/", "ly thân; sống riêng", "His parents are separated but remain supportive.", "legally separated; recently separated", "B2", "life_events"),
    ("widowed", "/ˈwɪdoʊd/", "góa vợ hoặc góa chồng", "She was widowed at a young age.", "recently widowed; widowed parent", "C1", "life_events"),

    ("relationship", "/rɪˈleɪʃnʃɪp/", "mối quan hệ", "Their relationship is based on trust.", "close relationship; build a relationship; long-distance relationship", "A2", "social_relationships"),
    ("friendship", "/ˈfrendʃɪp/", "tình bạn", "Their friendship began at primary school.", "close friendship; lasting friendship; form a friendship", "B1", "social_relationships"),
    ("best friend", "/ˌbest ˈfrend/", "bạn thân nhất", "My best friend always listens without judging.", "childhood best friend; become best friends", "A1", "social_relationships"),
    ("classmate", "/ˈklæsmeɪt/", "bạn cùng lớp", "A classmate invited me to join the study group.", "former classmate; new classmate", "A2", "social_relationships"),
    ("colleague", "/ˈkɑːliːɡ/", "đồng nghiệp", "I sometimes have lunch with a colleague from work.", "former colleague; close colleague", "B1", "social_relationships"),
    ("acquaintance", "/əˈkweɪntəns/", "người quen", "He is an acquaintance rather than a close friend.", "casual acquaintance; mutual acquaintance", "B2", "social_relationships"),
    ("neighbor", "/ˈneɪbər/", "hàng xóm", "Our neighbor checks on the house when we travel.", "next-door neighbor; friendly neighbor", "A2", "social_relationships"),
    ("partner", "/ˈpɑːrtnər/", "bạn đời; người yêu; đối tác", "A supportive partner respects your goals.", "long-term partner; romantic partner", "A2", "social_relationships"),
    ("date", "/deɪt/", "buổi hẹn hò; người hẹn hò", "They went on a date at a quiet café.", "go on a date; first date; arrange a date", "A2", "social_relationships"),
    ("fall in love", "/fɔːl ɪn lʌv/", "phải lòng; yêu", "They began to fall in love during the trip.", "fall in love with someone", "B1", "social_relationships"),
    ("get along", "/ɡet əˈlɔːŋ/", "hòa thuận", "The two brothers get along very well.", "get along with someone; get along well", "B1", "social_relationships"),
    ("have in common", "/hæv ɪn ˈkɑːmən/", "có điểm chung", "What do you two have in common?", "have a lot in common; have little in common", "B1", "social_relationships"),
    ("close to", "/kloʊs tuː/", "thân thiết với", "She is very close to her older sister.", "remain close to; feel close to", "A2", "social_relationships"),
    ("trust", "/trʌst/", "tin tưởng; lòng tin", "Children need adults they can trust.", "build trust; earn trust; trust someone completely", "B1", "social_relationships"),
    ("respect", "/rɪˈspekt/", "tôn trọng; sự tôn trọng", "Good friends respect each other's boundaries.", "mutual respect; show respect; earn respect", "B1", "social_relationships"),

    ("upbringing", "/ˈʌpbrɪŋɪŋ/", "sự nuôi dạy; nền nếp giáo dục", "His upbringing taught him to value kindness.", "strict upbringing; family upbringing", "B2", "parenting"),
    ("parenting", "/ˈperəntɪŋ/", "việc nuôi dạy con", "Parenting can be both demanding and rewarding.", "parenting style; parenting skills; positive parenting", "B2", "parenting"),
    ("guardian", "/ˈɡɑːrdiən/", "người giám hộ", "A legal guardian signed the school form.", "legal guardian; appointed guardian", "B2", "parenting"),
    ("take care of", "/teɪk ker əv/", "chăm sóc", "Grandparents often take care of the children after school.", "take good care of; help take care of", "A2", "parenting"),
    ("look after", "/lʊk ˈæftər/", "trông nom; chăm sóc", "Can you look after my son this afternoon?", "look after a child; look after one another", "A2", "parenting"),
    ("support", "/səˈpɔːrt/", "ủng hộ; hỗ trợ", "Families should support one another in difficult times.", "emotional support; financial support; support a decision", "A2", "parenting"),
    ("protect", "/prəˈtekt/", "bảo vệ", "Parents try to protect their children from danger.", "protect someone from harm; fiercely protect", "A2", "parenting"),
    ("discipline", "/ˈdɪsəplɪn/", "kỷ luật; uốn nắn", "Good discipline teaches children about consequences.", "positive discipline; strict discipline", "B2", "parenting"),
    ("set boundaries", "/set ˈbaʊndəriz/", "đặt ra giới hạn", "Healthy families set boundaries and communicate them clearly.", "set clear boundaries; learn to set boundaries", "B2", "parenting"),
    ("role model", "/ˈroʊl mɑːdəl/", "tấm gương", "Her aunt is a strong role model for her.", "positive role model; serve as a role model", "B1", "parenting"),
    ("household chores", "/ˈhaʊshoʊld tʃɔːrz/", "việc nhà", "Everyone shares the household chores in our family.", "do household chores; divide household chores", "B1", "parenting"),
    ("quality time", "/ˈkwɑːləti taɪm/", "thời gian ý nghĩa bên nhau", "We spend quality time together every Sunday.", "spend quality time with; family quality time", "B1", "parenting"),

    ("argument", "/ˈɑːrɡjumənt/", "cuộc tranh cãi", "They had an argument about money.", "have an argument; heated argument; avoid an argument", "B1", "conflict_resolution"),
    ("disagreement", "/ˌdɪsəˈɡriːmənt/", "sự bất đồng", "A small disagreement should not end a friendship.", "serious disagreement; resolve a disagreement", "B2", "conflict_resolution"),
    ("misunderstanding", "/ˌmɪsʌndərˈstændɪŋ/", "sự hiểu lầm", "The problem began with a simple misunderstanding.", "clear up a misunderstanding; avoid misunderstanding", "B2", "conflict_resolution"),
    ("conflict", "/ˈkɑːnflɪkt/", "xung đột; mâu thuẫn", "Open communication can prevent conflict.", "family conflict; resolve conflict; source of conflict", "B2", "conflict_resolution"),
    ("criticize", "/ˈkrɪtəsaɪz/", "chỉ trích", "Try not to criticize your partner in public.", "openly criticize; unfairly criticize", "B2", "conflict_resolution"),
    ("blame", "/bleɪm/", "đổ lỗi; trách", "It is easy to blame others when we feel hurt.", "blame someone for; take the blame", "B1", "conflict_resolution"),
    ("disappoint", "/ˌdɪsəˈpɔɪnt/", "làm thất vọng", "I did not want to disappoint my parents.", "deeply disappoint; be afraid to disappoint", "B1", "conflict_resolution"),
    ("betray", "/bɪˈtreɪ/", "phản bội", "Sharing that secret would betray her trust.", "betray someone's trust; feel betrayed", "B2", "conflict_resolution"),
    ("break up", "/breɪk ʌp/", "chia tay", "They decided to break up but remain friends.", "break up with someone; painful break-up", "B1", "conflict_resolution"),
    ("make up", "/meɪk ʌp/", "làm hòa", "The sisters usually make up quickly after an argument.", "make up with someone; kiss and make up", "B1", "conflict_resolution"),
    ("apologize", "/əˈpɑːlədʒaɪz/", "xin lỗi", "You should apologize when you hurt someone.", "apologize to someone; sincerely apologize", "B1", "conflict_resolution"),
    ("forgive", "/fərˈɡɪv/", "tha thứ", "It may take time to forgive a serious mistake.", "forgive someone for; forgive and forget", "B1", "conflict_resolution"),
    ("compromise", "/ˈkɑːmprəmaɪz/", "thỏa hiệp; sự thỏa hiệp", "Both sides must compromise to find a solution.", "reach a compromise; be willing to compromise", "B2", "conflict_resolution"),
    ("reconcile", "/ˈrekənsaɪl/", "hòa giải; làm lành", "The old friends hope to reconcile after years apart.", "reconcile with someone; attempt to reconcile", "C1", "conflict_resolution"),

    ("affection", "/əˈfekʃn/", "tình cảm trìu mến", "The family showed affection through small acts of kindness.", "show affection; deep affection; physical affection", "B2", "values_emotions"),
    ("love", "/lʌv/", "tình yêu; yêu thương", "Children need both love and guidance.", "unconditional love; true love; show love", "A1", "values_emotions"),
    ("bond", "/bɑːnd/", "mối gắn kết", "Traveling together strengthened their bond.", "strong bond; family bond; form a bond", "B2", "values_emotions"),
    ("loyalty", "/ˈlɔɪəlti/", "lòng trung thành", "Loyalty is important in a lasting friendship.", "show loyalty; family loyalty; earn loyalty", "B2", "values_emotions"),
    ("honesty", "/ˈɑːnəsti/", "sự trung thực", "Honesty helps couples solve problems early.", "complete honesty; value honesty", "B2", "values_emotions"),
    ("empathy", "/ˈempəθi/", "sự đồng cảm", "Empathy helps us understand another person's feelings.", "show empathy; develop empathy; lack empathy", "C1", "values_emotions"),
    ("responsibility", "/rɪˌspɑːnsəˈbɪləti/", "trách nhiệm", "Caring for a child is a major responsibility.", "take responsibility; shared responsibility", "B1", "values_emotions"),
    ("independence", "/ˌɪndɪˈpendəns/", "sự độc lập", "Teenagers gradually seek more independence.", "gain independence; financial independence", "B2", "values_emotions"),
    ("generation gap", "/ˌdʒenəˈreɪʃn ɡæp/", "khoảng cách thế hệ", "Listening with curiosity can reduce the generation gap.", "bridge the generation gap; widen the generation gap", "B2", "values_emotions"),
    ("family tradition", "/ˈfæməli trəˌdɪʃn/", "truyền thống gia đình", "Cooking together is an important family tradition.", "continue a family tradition; old family tradition", "B1", "values_emotions"),
]


TOPIC_LABELS = {
    "immediate_family": "Gia đình gần gũi",
    "extended_family": "Họ hàng & gia phả",
    "life_events": "Các giai đoạn & sự kiện",
    "social_relationships": "Quan hệ xã hội",
    "parenting": "Nuôi dạy & chăm sóc",
    "conflict_resolution": "Xung đột & hòa giải",
    "values_emotions": "Giá trị & cảm xúc",
}

CSS = """
.card { font-family: Arial, sans-serif; font-size: 20px; line-height: 1.5;
  text-align: center; color: #243044; background: #fffaf7; }
.nightMode .card { color: #edf2f7; background: #172033; }
.card img { display: block; max-width: min(92vw, 360px); max-height: 260px;
  margin: 10px auto; border-radius: 10px; object-fit: cover; }
.term { color: #9f2d55; font-size: 29px; font-weight: 700; }
.ipa { color: #68758a; }
.meaning { color: #c0522b; font-size: 22px; font-weight: 700; }
.example { margin: 12px 0 7px; font-style: italic; }
.useful { color: #5368ad; font-size: 14px; }
.meta { color: #7a8495; font-size: 12px; }
.topic { display: inline-block; margin: 8px 0; padding: 3px 9px;
  border-radius: 12px; color: #8c3455; background: #f8dfe8; font-size: 12px; }
.nightMode .topic { color: #ffd7e7; background: #663148; }
"""


VARIANTS = {
    "basic": {
        "template": REPO / "datetime" / "SIP-DateTime-Basic-Reversed.apkg",
        "output": ROOT / "SIP-Family-Relationships-Basic-Reversed.apkg",
        "deck_id": 1990002001,
        "model_id": 1783242366234,
        "deck_name": "English Family & Relationships - Basic and Reversed",
        "model_name": "Family & Relationships Basic (and reversed)",
        "cards": 2,
    },
    "sentence": {
        "template": REPO / "datetime" / "SIP-DateTime-Sentence-Mining.apkg",
        "output": ROOT / "SIP-Family-Relationships-Sentence-Mining.apkg",
        "deck_id": 1990002002,
        "model_id": 1783242366236,
        "deck_name": "English Family & Relationships - Sentence Mining",
        "model_name": "Family & Relationships Type in the answer",
        "cards": 1,
    },
    "comprehensive": {
        "template": REPO / "datetime" / "SIP-DateTime-Comprehensive.apkg",
        "output": ROOT / "SIP-Family-Relationships-Comprehensive.apkg",
        "deck_id": 1990002003,
        "model_id": 1783242366233,
        "deck_name": "English Family & Relationships - Comprehensive",
        "model_name": "Family & Relationships Comprehensive",
        "cards": 1,
    },
}


def checksum(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def guid(term: str, variant: str) -> str:
    return hashlib.sha1(f"family-relationships:{variant}:{term}".encode()).hexdigest()[:10]


def safe_name(term: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", term.lower()).strip("_")


def image_name(term: str) -> str:
    for extension in (".png", ".jpg", ".jpeg"):
        path = IMAGES / f"{safe_name(term)}{extension}"
        if path.is_file():
            return path.name
    raise FileNotFoundError(f"Missing image for {term!r}")


def audio_name(term: str) -> str:
    path = AUDIO / f"{safe_name(term)}.mp3"
    if not path.is_file() or path.stat().st_size < 500:
        raise FileNotFoundError(f"Missing audio for {term!r}")
    return path.name


def image_tag(term: str) -> str:
    return f'<img src="{image_name(term)}" alt="Family and relationships illustration">'


def audio_tag(term: str) -> str:
    return f"[sound:{audio_name(term)}]"


def term_front(term: str, ipa: str, level: str, topic: str) -> str:
    return (
        f'<div class="term">{html.escape(term)}</div>'
        f'<div class="ipa">{html.escape(ipa)}</div>'
        f'{audio_tag(term)}{image_tag(term)}'
        f'<div class="topic">{html.escape(TOPIC_LABELS[topic])}</div>'
        f'<div class="meta">[{level}]</div>'
    )


def meaning_front(term: str, meaning: str, level: str, topic: str) -> str:
    return (
        f'<div class="meaning">{html.escape(meaning)}</div>'
        f'{image_tag(term)}'
        f'<div class="topic">{html.escape(TOPIC_LABELS[topic])}</div>'
        f'<div class="meta">[{level}]</div>'
    )


def detail_back(term: str, ipa: str, meaning: str, example: str, useful: str,
                level: str, topic: str) -> str:
    return (
        f'<div class="term" style="font-size:25px">{html.escape(term)}</div>'
        f'<div class="ipa">{html.escape(ipa)}</div>'
        f'{audio_tag(term)}'
        f'<div class="meaning">{html.escape(meaning)}</div>'
        f'<div class="example">{html.escape(example)}</div>'
        f'<div class="useful">Useful: {html.escape(useful)}</div>'
        f'<div class="topic">{html.escape(TOPIC_LABELS[topic])}</div>'
        f'<div class="meta">[{level}]</div>'
    )


def sentence_front(term: str, example: str, meaning: str, level: str,
                   topic: str) -> str:
    blanked, count = re.subn(re.escape(term), "_____", example, count=1,
                             flags=re.IGNORECASE)
    if count != 1:
        raise ValueError(f"Example does not contain target {term!r}: {example}")
    return (
        f'{image_tag(term)}'
        '<div class="meta">Complete the missing word or phrase</div>'
        f'<div class="example" style="font-style:normal">{html.escape(blanked)}</div>'
        f'<div class="meaning">{html.escape(meaning)}</div>'
        f'<div class="topic">{html.escape(TOPIC_LABELS[topic])}</div>'
        f'<div class="meta">[{level}]</div>'
    )


def fields_for(variant: str, word: tuple[str, ...]) -> tuple[str, ...]:
    term, ipa, meaning, example, useful, level, topic = word
    if variant == "basic":
        return term_front(term, ipa, level, topic), meaning_front(term, meaning, level, topic)
    if variant == "sentence":
        return sentence_front(term, example, meaning, level, topic), term, audio_tag(term)
    return term_front(term, ipa, level, topic), detail_back(*word)


def configure_collection(db_path: Path, variant: str, now: int) -> None:
    spec = VARIANTS[variant]
    connection = sqlite3.connect(db_path)
    try:
        models_raw, decks_raw = connection.execute("SELECT models, decks FROM col").fetchone()
        old_model = next(iter(json.loads(models_raw).values()))
        model = deepcopy(old_model)
        model.update({
            "id": str(spec["model_id"]),
            "did": spec["deck_id"],
            "name": spec["model_name"],
            "css": CSS,
            "mod": now,
        })
        if variant == "sentence":
            model["flds"] = [
                {"name": name, "ord": order, "font": "Liberation Sans", "media": [], "rtl": False, "size": 20, "sticky": False}
                for order, name in enumerate(("Front", "Back", "Audio"))
            ]
            model["tmpls"][0]["afmt"] = "{{Front}}<hr id=answer>{{type:Back}}<br>{{Audio}}"

        old_decks = json.loads(decks_raw)
        source_deck = next(deck for key, deck in old_decks.items() if key != "1")
        deck = deepcopy(source_deck)
        deck.update({
            "id": spec["deck_id"],
            "name": spec["deck_name"],
            "desc": "100 essential Family & Relationships vocabulary notes (A1-C1).",
            "mod": now,
            "usn": -1,
            "lrnToday": [0, 0], "newToday": [0, 0],
            "revToday": [0, 0], "timeToday": [0, 0],
        })
        decks = {"1": old_decks["1"], str(spec["deck_id"]): deck}

        conf = json.loads(connection.execute("SELECT conf FROM col").fetchone()[0])
        conf.update({"activeDecks": [spec["deck_id"]], "curDeck": spec["deck_id"],
                     "curModel": str(spec["model_id"]), "nextPos": len(WORDS) + 1})
        tags = {level: 0 for level in ("A1", "A2", "B1", "B2", "C1")}
        tags.update({topic: 0 for topic in TOPIC_LABELS})

        connection.execute("DELETE FROM cards")
        connection.execute("DELETE FROM notes")
        connection.execute("DELETE FROM revlog")
        connection.execute("DELETE FROM graves")
        connection.execute(
            "UPDATE col SET mod=?, scm=?, conf=?, models=?, decks=?, tags=?",
            (now * 1000, now * 1000, json.dumps(conf),
             json.dumps({str(spec["model_id"]): model}), json.dumps(decks),
             json.dumps(tags)),
        )

        base_id = now * 1000
        for index, word in enumerate(WORDS, start=1):
            term, _ipa, _meaning, _example, _useful, level, topic = word
            fields = fields_for(variant, word)
            front = fields[0]
            note_id = base_id + index * 10
            note_tags = f" {level} {topic} family_relationships "
            connection.execute(
                "INSERT INTO notes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (note_id, guid(term, variant), spec["model_id"], now, -1,
                 note_tags, "\x1f".join(fields), front, checksum(front), 0, ""),
            )
            for card_ord in range(spec["cards"]):
                card_id = note_id + card_ord + 1
                connection.execute(
                    "INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (card_id, note_id, spec["deck_id"], card_ord, now, -1,
                     0, 0, index, 0, 0, 0, 0, 0, 0, 0, 0, ""),
                )
        connection.commit()
    finally:
        connection.close()


def build_variant(variant: str, now: int) -> None:
    spec = VARIANTS[variant]
    with tempfile.TemporaryDirectory(prefix="family_anki_") as temp_dir:
        db_path = Path(temp_dir) / "collection.anki2"
        with zipfile.ZipFile(spec["template"]) as source:
            db_path.write_bytes(source.read("collection.anki2"))
        configure_collection(db_path, variant, now)
        media_files = sorted(path for path in MEDIA.rglob("*") if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".mp3"})
        media_map = {str(index): path.name for index, path in enumerate(media_files)}
        with zipfile.ZipFile(spec["output"], "w", zipfile.ZIP_DEFLATED) as package:
            package.write(db_path, "collection.anki2")
            package.writestr("media", json.dumps(media_map))
            for index, path in enumerate(media_files):
                package.write(path, str(index))
    card_count = len(WORDS) * spec["cards"]
    print(f"Created {spec['output'].name}: {len(WORDS)} notes, {card_count} cards")


def audit_package(variant: str) -> None:
    """Fail loudly if a generated package is incomplete or internally invalid."""
    spec = VARIANTS[variant]
    expected_cards = len(WORDS) * spec["cards"]
    with tempfile.TemporaryDirectory(prefix="family_anki_audit_") as temp_dir:
        db_path = Path(temp_dir) / "collection.anki2"
        with zipfile.ZipFile(spec["output"]) as package:
            media_map = json.loads(package.read("media"))
            if len(media_map) != len(WORDS) * 2:
                raise ValueError(f"Wrong media count in {spec['output'].name}")
            if set(package.namelist()) != {"collection.anki2", "media", *media_map.keys()}:
                raise ValueError(f"Missing media files in {spec['output'].name}")
            db_path.write_bytes(package.read("collection.anki2"))

        connection = sqlite3.connect(db_path)
        try:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError(f"SQLite integrity check failed for {spec['output'].name}")
            note_count = connection.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            card_count = connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
            if (note_count, card_count) != (len(WORDS), expected_cards):
                raise ValueError(
                    f"Wrong counts in {spec['output'].name}: "
                    f"{note_count} notes, {card_count} cards"
                )
            orphan_cards = connection.execute(
                "SELECT COUNT(*) FROM cards LEFT JOIN notes ON notes.id=cards.nid "
                "WHERE notes.id IS NULL"
            ).fetchone()[0]
            if orphan_cards:
                raise ValueError(f"Found {orphan_cards} orphan cards")

            models_raw, decks_raw = connection.execute(
                "SELECT models, decks FROM col"
            ).fetchone()
            models, decks = json.loads(models_raw), json.loads(decks_raw)
            if set(models) != {str(spec["model_id"])}:
                raise ValueError(f"Wrong model ID in {spec['output'].name}")
            if str(spec["deck_id"]) not in decks:
                raise ValueError(f"Missing deck ID in {spec['output'].name}")
            model = models[str(spec["model_id"])]
            if model["did"] != spec["deck_id"] or model["name"] != spec["model_name"]:
                raise ValueError(f"Model metadata mismatch in {spec['output'].name}")

            rows = connection.execute(
                "SELECT notes.flds, notes.tags, cards.due "
                "FROM notes JOIN cards ON cards.nid=notes.id "
                "WHERE cards.ord=0 ORDER BY cards.due"
            ).fetchall()
            for index, (row, word) in enumerate(zip(rows, WORDS, strict=True), start=1):
                flds, tags, due = row
                if due != index:
                    raise ValueError(f"Non-sequential card order at note {index}")
                fields = flds.split("\x1f")
                expected_fields = fields_for(variant, word)
                if len(fields) != len(expected_fields) or tuple(fields) != expected_fields:
                    raise ValueError(f"Field mismatch for {word[0]!r} in {variant}")
                required_tags = {word[5], word[6], "family_relationships"}
                if not required_tags.issubset(tags.split()):
                    raise ValueError(f"Missing tags for {word[0]!r} in {variant}")
                for filename in (image_name(word[0]), audio_name(word[0])):
                    if filename not in media_map.values():
                        raise ValueError(f"Unpackaged media for {word[0]!r}: {filename}")

            dirty_cards = connection.execute(
                "SELECT COUNT(*) FROM cards WHERE type != 0 OR queue != 0 "
                "OR ivl != 0 OR reps != 0 OR lapses != 0"
            ).fetchone()[0]
            if dirty_cards:
                raise ValueError(f"Package contains {dirty_cards} scheduled cards")
        finally:
            connection.close()
    print(f"Verified {spec['output'].name}: database, fields, tags and scheduling OK")


def validate_data() -> None:
    if len(WORDS) != 100:
        raise ValueError(f"Expected 100 vocabulary items, found {len(WORDS)}")
    terms = [word[0].casefold() for word in WORDS]
    duplicates = sorted({term for term in terms if terms.count(term) > 1})
    if duplicates:
        raise ValueError(f"Duplicate terms: {', '.join(duplicates)}")
    unknown_topics = {word[6] for word in WORDS} - TOPIC_LABELS.keys()
    if unknown_topics:
        raise ValueError(f"Unknown topics: {', '.join(sorted(unknown_topics))}")
    valid_levels = {"A1", "A2", "B1", "B2", "C1"}
    for word in WORDS:
        term, ipa, meaning, example, useful, level, topic = word
        if not all(value.strip() for value in word):
            raise ValueError(f"Empty field in vocabulary item: {term!r}")
        if level not in valid_levels:
            raise ValueError(f"Invalid CEFR level for {term!r}: {level}")
        if not (ipa.startswith("/") and ipa.endswith("/")):
            raise ValueError(f"Invalid IPA delimiters for {term!r}: {ipa}")
        if len(re.findall(re.escape(term), example, flags=re.IGNORECASE)) != 1:
            raise ValueError(f"Example must contain {term!r} exactly once: {example}")
        if example[-1] not in ".?!":
            raise ValueError(f"Example needs final punctuation for {term!r}")
        sentence_front(word[0], word[3], word[2], word[5], word[6])


def build() -> None:
    validate_data()
    now = int(time.time())
    for variant in VARIANTS:
        build_variant(variant, now)
        audit_package(variant)


if __name__ == "__main__":
    build()
