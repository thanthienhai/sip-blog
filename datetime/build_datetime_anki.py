"""Build English Date & Time Anki decks with licensed image and audio media."""
from pathlib import Path
import html
import re

import genanki
from gtts import gTTS

ROOT = Path(__file__).resolve().parent
MEDIA = ROOT / "media"
AUDIO = MEDIA / "audio"
IMAGES = MEDIA / "images"
for directory in (AUDIO, IMAGES):
    directory.mkdir(parents=True, exist_ok=True)

# term, IPA, Vietnamese meaning, example, collocations / notes, CEFR level, image group
WORDS = [
    ("time", "/taɪm/", "thời gian; giờ giấc", "Time passes quickly when you are busy.", "tell the time; spend time; on time", "A1", "clock"),
    ("clock", "/klɑːk/", "đồng hồ", "The clock says it is three o'clock.", "wall clock; alarm clock; set the clock", "A1", "clock"),
    ("watch", "/wɑːtʃ/", "đồng hồ đeo tay", "My watch is five minutes fast.", "wear a watch; check your watch", "A1", "clock"),
    ("hour", "/aʊər/", "giờ", "The lesson lasts for one hour.", "an hour ago; working hours; rush hour", "A1", "clock"),
    ("minute", "/ˈmɪnɪt/", "phút", "Please wait a minute.", "in a minute; last minute; take a minute", "A1", "clock"),
    ("second", "/ˈsekənd/", "giây", "The train left just seconds ago.", "a few seconds; split second", "A1", "clock"),
    ("millisecond", "/ˈmɪlɪsekənd/", "mili giây", "The result was decided in milliseconds.", "within milliseconds", "B2", "clock"),
    ("quarter", "/ˈkwɔːrtər/", "một phần tư; 15 phút", "The meeting starts at a quarter past nine.", "a quarter past; a quarter to", "A2", "clock"),
    ("half", "/hæf/", "một nửa; 30 phút", "It is half past six now.", "half past; half an hour", "A1", "clock"),
    ("o'clock", "/əˈklɑːk/", "đúng giờ", "The movie begins at seven o'clock.", "at two o'clock", "A1", "clock"),
    ("past", "/pæst/", "qua, hơn (giờ)", "It is ten past four.", "ten past; half past", "A2", "clock"),
    ("to", "/tuː/", "kém (giờ)", "It is twenty to eight.", "quarter to; five to", "A2", "clock"),
    ("noon", "/nuːn/", "buổi trưa, 12 giờ trưa", "We will meet at noon.", "at noon; around noon", "A1", "clock"),
    ("midnight", "/ˈmɪdnaɪt/", "nửa đêm, 12 giờ đêm", "The deadline is at midnight.", "at midnight; after midnight", "A2", "night"),
    ("a.m.", "/ˌeɪ ˈem/", "sáng (trước 12 giờ trưa)", "The class begins at 8 a.m.", "in the a.m.; 8 a.m.", "A1", "morning"),
    ("p.m.", "/ˌpiː ˈem/", "chiều/tối (sau 12 giờ trưa)", "The shop closes at 9 p.m.", "in the p.m.; 9 p.m.", "A1", "night"),
    ("morning", "/ˈmɔːrnɪŋ/", "buổi sáng", "I study English every morning.", "this morning; early morning", "A1", "morning"),
    ("afternoon", "/ˌæftərˈnuːn/", "buổi chiều", "We have a meeting this afternoon.", "in the afternoon; late afternoon", "A1", "day"),
    ("evening", "/ˈiːvnɪŋ/", "buổi tối", "She goes for a walk in the evening.", "this evening; early evening", "A1", "night"),
    ("night", "/naɪt/", "đêm", "The streets are quiet at night.", "at night; last night", "A1", "night"),
    ("dawn", "/dɔːn/", "bình minh", "We left the house at dawn.", "at dawn; before dawn", "B2", "morning"),
    ("sunrise", "/ˈsʌnraɪz/", "mặt trời mọc", "The sunrise was beautiful this morning.", "at sunrise; watch the sunrise", "B1", "morning"),
    ("sunset", "/ˈsʌnset/", "hoàng hôn", "We arrived before sunset.", "at sunset; after sunset", "B1", "night"),
    ("today", "/təˈdeɪ/", "hôm nay", "Today is Monday.", "earlier today; today at noon", "A1", "calendar"),
    ("tomorrow", "/təˈmɑːroʊ/", "ngày mai", "I will call you tomorrow.", "tomorrow morning; until tomorrow", "A1", "calendar"),
    ("yesterday", "/ˈjestərdeɪ/", "hôm qua", "Yesterday was very busy.", "yesterday morning; since yesterday", "A1", "calendar"),
    ("the day after tomorrow", "/ðə deɪ ˈæftər təˈmɑːroʊ/", "ngày kia", "The exam is the day after tomorrow.", "leave the day after tomorrow", "A2", "calendar"),
    ("the day before yesterday", "/ðə deɪ bɪˈfɔːr ˈjestərdeɪ/", "hôm kia", "I saw her the day before yesterday.", "arrive the day before yesterday", "A2", "calendar"),
    ("weekday", "/ˈwiːkdeɪ/", "ngày trong tuần", "I take the bus on weekdays.", "every weekday; weekday morning", "A2", "calendar"),
    ("weekend", "/ˌwiːkˈend/", "cuối tuần", "We visit our grandparents at the weekend.", "this weekend; at the weekend", "A1", "calendar"),
    ("Monday", "/ˈmʌndeɪ/", "thứ Hai", "Our course starts on Monday.", "on Monday; Monday morning", "A1", "calendar"),
    ("Tuesday", "/ˈtuːzdeɪ/", "thứ Ba", "The office is closed on Tuesday.", "on Tuesday; next Tuesday", "A1", "calendar"),
    ("Wednesday", "/ˈwenzdeɪ/", "thứ Tư", "Wednesday is the busiest day of my week.", "on Wednesday; every Wednesday", "A1", "calendar"),
    ("Thursday", "/ˈθɜːrzdeɪ/", "thứ Năm", "We have a test on Thursday.", "on Thursday; Thursday afternoon", "A1", "calendar"),
    ("Friday", "/ˈfraɪdeɪ/", "thứ Sáu", "The report is due on Friday.", "on Friday; Friday night", "A1", "calendar"),
    ("Saturday", "/ˈsætərdeɪ/", "thứ Bảy", "I work part-time on Saturday.", "on Saturday; Saturday morning", "A1", "calendar"),
    ("Sunday", "/ˈsʌndeɪ/", "Chủ nhật", "We usually relax on Sunday.", "on Sunday; Sunday evening", "A1", "calendar"),
    ("week", "/wiːk/", "tuần", "The project will take a week.", "next week; last week; once a week", "A1", "calendar"),
    ("fortnight", "/ˈfɔːrtnaɪt/", "hai tuần", "The rent is paid every fortnight.", "in a fortnight; every fortnight", "B1", "calendar"),
    ("month", "/mʌnθ/", "tháng", "February is a short month.", "next month; every month", "A1", "calendar"),
    ("year", "/jɪr/", "năm", "This year has gone by quickly.", "last year; next year; all year", "A1", "calendar"),
    ("decade", "/ˈdekeɪd/", "thập kỷ", "The city changed a lot over the decade.", "for decades; the next decade", "B2", "calendar"),
    ("century", "/ˈsentʃəri/", "thế kỷ", "The building was built in the last century.", "this century; for centuries", "B2", "calendar"),
    ("January", "/ˈdʒænjuˌeri/", "tháng Một", "The new term begins in January.", "in January; January 1st", "A1", "calendar"),
    ("February", "/ˈfebruˌeri/", "tháng Hai", "February has 28 days in most years.", "in February; late February", "A1", "calendar"),
    ("March", "/mɑːrtʃ/", "tháng Ba", "Spring begins in March in many places.", "in March; March 8th", "A1", "calendar"),
    ("April", "/ˈeɪprəl/", "tháng Tư", "It often rains in April.", "in April; early April", "A1", "calendar"),
    ("May", "/meɪ/", "tháng Năm", "The holiday falls in May.", "in May; May Day", "A1", "calendar"),
    ("June", "/dʒuːn/", "tháng Sáu", "School ends in June.", "in June; mid-June", "A1", "calendar"),
    ("July", "/dʒuˈlaɪ/", "tháng Bảy", "We travel in July.", "in July; July 4th", "A1", "calendar"),
    ("August", "/ˈɔːɡəst/", "tháng Tám", "August is usually hot here.", "in August; late August", "A1", "calendar"),
    ("September", "/sepˈtembər/", "tháng Chín", "Classes resume in September.", "in September; September 2nd", "A1", "calendar"),
    ("October", "/ɑːkˈtoʊbər/", "tháng Mười", "The weather cools down in October.", "in October; early October", "A1", "calendar"),
    ("November", "/noʊˈvembər/", "tháng Mười Một", "The event takes place in November.", "in November; late November", "A1", "calendar"),
    ("December", "/dɪˈsembər/", "tháng Mười Hai", "December is the final month of the year.", "in December; December 31st", "A1", "calendar"),
    ("date", "/deɪt/", "ngày, ngày tháng", "What is the date today?", "set a date; due date; today's date", "A1", "calendar"),
    ("calendar", "/ˈkælɪndər/", "lịch", "Please put the appointment on your calendar.", "wall calendar; calendar year", "A1", "calendar"),
    ("leap year", "/ˈliːp jɪr/", "năm nhuận", "A leap year has 366 days.", "leap-year day", "B1", "calendar"),
    ("anniversary", "/ˌænɪˈvɜːrsəri/", "ngày kỷ niệm", "Today is their wedding anniversary.", "celebrate an anniversary; annual anniversary", "B1", "calendar"),
    ("birthday", "/ˈbɜːrθdeɪ/", "sinh nhật", "Her birthday is on the fifth of May.", "happy birthday; birthday party", "A1", "calendar"),
    ("appointment", "/əˈpɔɪntmənt/", "cuộc hẹn", "I have a dentist appointment at 10 a.m.", "make an appointment; keep an appointment", "A2", "calendar"),
    ("schedule", "/ˈskedʒuːl/", "lịch trình", "My schedule is full this week.", "busy schedule; on schedule", "A2", "calendar"),
    ("timetable", "/ˈtaɪmteɪbəl/", "thời khóa biểu; giờ tàu xe", "Check the train timetable before you leave.", "class timetable; train timetable", "A2", "calendar"),
    ("deadline", "/ˈdedlaɪn/", "hạn chót", "The application deadline is Friday.", "meet a deadline; strict deadline", "B1", "clock"),
    ("due date", "/ˈduː deɪt/", "hạn đến hạn", "The bill's due date is the 15th.", "payment due date; due on", "B1", "calendar"),
    ("duration", "/dʊˈreɪʃn/", "khoảng thời gian kéo dài", "The course has a duration of six weeks.", "for the duration; short duration", "B2", "clock"),
    ("period", "/ˈpɪriəd/", "giai đoạn, khoảng thời gian", "It was a difficult period in her life.", "a period of time; time period", "B1", "clock"),
    ("moment", "/ˈmoʊmənt/", "khoảnh khắc", "I will be with you in a moment.", "at the moment; a special moment", "A2", "clock"),
    ("instant", "/ˈɪnstənt/", "ngay lập tức; khoảnh khắc", "The screen changed in an instant.", "in an instant; instant message", "B2", "clock"),
    ("early", "/ˈɜːrli/", "sớm", "We arrived early for the interview.", "get up early; early morning", "A1", "morning"),
    ("late", "/leɪt/", "muộn", "I was late for class.", "be late; stay up late", "A1", "night"),
    ("on time", "/ɑːn taɪm/", "đúng giờ", "The bus arrived on time.", "arrive on time; be on time", "A2", "clock"),
    ("in time", "/ɪn taɪm/", "kịp lúc", "We got to the station in time for the train.", "just in time; in time for", "B1", "clock"),
    ("punctual", "/ˈpʌŋktʃuəl/", "đúng giờ, đúng hẹn", "A punctual student arrives before class starts.", "be punctual; punctual arrival", "B2", "clock"),
    ("delay", "/dɪˈleɪ/", "sự trì hoãn; trì hoãn", "The flight was delayed for two hours.", "long delay; delay a flight", "B1", "clock"),
    ("postpone", "/poʊˈspoʊn/", "hoãn lại", "They postponed the meeting until Friday.", "postpone a meeting; postpone until", "B2", "calendar"),
    ("reschedule", "/ˌriːˈskedʒuːl/", "sắp xếp lại lịch", "Can we reschedule our appointment?", "reschedule a meeting; reschedule for", "B2", "calendar"),
    ("before", "/bɪˈfɔːr/", "trước", "Please finish before noon.", "before class; the day before", "A1", "clock"),
    ("after", "/ˈæftər/", "sau", "We can talk after lunch.", "after work; the day after", "A1", "clock"),
    ("during", "/ˈdʊrɪŋ/", "trong suốt", "Do not use your phone during the exam.", "during the day; during class", "A2", "clock"),
    ("until", "/ənˈtɪl/", "cho đến", "The store is open until 10 p.m.", "until tomorrow; until then", "A2", "clock"),
    ("since", "/sɪns/", "từ khi", "I have lived here since 2020.", "since Monday; ever since", "A2", "calendar"),
    ("for", "/fɔːr/", "trong (khoảng thời gian)", "I have waited for two hours.", "for a week; for a long time", "A1", "clock"),
    ("from ... to ...", "/frəm tuː/", "từ ... đến ...", "The library is open from 8 a.m. to 8 p.m.", "from Monday to Friday", "A2", "clock"),
    ("at", "/æt/", "vào (giờ cụ thể)", "The film starts at 7:30.", "at noon; at night; at 5 p.m.", "A1", "clock"),
    ("on", "/ɑːn/", "vào (thứ/ngày)", "My birthday is on Sunday.", "on Monday; on 12 May", "A1", "calendar"),
    ("in", "/ɪn/", "vào (tháng/năm/buổi)", "We moved here in 2024.", "in July; in the morning; in 2024", "A1", "calendar"),
    ("always", "/ˈɔːlweɪz/", "luôn luôn", "He always arrives early.", "almost always; always on time", "A1", "clock"),
    ("usually", "/ˈjuːʒuəli/", "thường thường", "I usually study after dinner.", "usually do; usually go", "A1", "clock"),
    ("often", "/ˈɔːfən/", "thường xuyên", "We often meet on Fridays.", "quite often; how often", "A1", "calendar"),
    ("sometimes", "/ˈsʌmtaɪmz/", "đôi khi", "She sometimes works at night.", "sometimes called; sometimes do", "A1", "night"),
    ("rarely", "/ˈrerli/", "hiếm khi", "I rarely stay up late.", "rarely seen; rarely go", "B1", "night"),
    ("never", "/ˈnevər/", "không bao giờ", "He is never late for work.", "never before; never again", "A1", "clock"),
    ("daily", "/ˈdeɪli/", "hàng ngày", "Take this medicine daily.", "daily routine; daily basis", "A2", "day"),
    ("weekly", "/ˈwiːkli/", "hàng tuần", "We have a weekly team meeting.", "weekly meeting; weekly schedule", "A2", "calendar"),
    ("monthly", "/ˈmʌnθli/", "hàng tháng", "Rent is paid monthly.", "monthly payment; monthly report", "A2", "calendar"),
    ("yearly", "/ˈjɪrli/", "hàng năm", "The festival is held yearly.", "yearly event; yearly review", "B1", "seasons"),
    ("spring", "/sprɪŋ/", "mùa xuân", "Flowers bloom in spring.", "in spring; early spring", "A1", "seasons"),
    ("summer", "/ˈsʌmər/", "mùa hè", "We travel during the summer.", "in summer; summer holiday", "A1", "seasons"),
    ("autumn (fall)", "/ˈɔːtəm (fɔːl)/", "mùa thu", "The leaves change color in autumn.", "in autumn; late fall", "A1", "seasons"),
    ("winter", "/ˈwɪntər/", "mùa đông", "It gets cold in winter.", "in winter; winter break", "A1", "seasons"),
    ("time zone", "/ˈtaɪm zoʊn/", "múi giờ", "Vietnam is in the ICT time zone.", "different time zone; change time zones", "B1", "clock"),
    ("time difference", "/ˈtaɪm ˌdɪfrəns/", "chênh lệch múi giờ", "There is a twelve-hour time difference.", "time difference between", "B1", "clock"),
    ("Daylight Saving Time", "/ˈdeɪlaɪt ˈseɪvɪŋ taɪm/", "giờ mùa hè", "Daylight Saving Time begins in spring in some countries.", "switch to Daylight Saving Time", "B2", "seasons"),
]

IMAGE_FILES = {
    # Different clock faces make time-telling cards visually distinct.
    "clock": ["clock_0101.svg", "clock_0103.svg", "clock_0104.svg", "clock_0105.svg", "clock_0106.svg", "clock_calendar.jpg"],
    "calendar": ["clock_calendar.jpg", "bracken_clock_calendar.jpg"],
    "morning": ["sunrise.jpg"],
    "day": ["sunrise.jpg", "clock_calendar.jpg"],
    "night": ["bracken_clock_calendar.jpg"],
    "seasons": ["four_seasons.jpg"],
}

CSS = """
.card { font-family: Arial, sans-serif; font-size: 20px; line-height: 1.45; text-align: center; color: #1f2937; background: #fff; }
.nightMode .card { color: #e5e7eb; background: #111827; }
.card img { max-width: 340px; max-height: 190px; margin: 10px auto; border-radius: 4px; }
.cloze { font-weight: bold; color: #2563eb; }
"""

MODEL_REV = genanki.Model(1783242365234, "DateTime Basic (and reversed)", fields=[{"name":"Front"},{"name":"Back"}], templates=[
    {"name":"English to Vietnamese", "qfmt":"{{Front}}", "afmt":"{{FrontSide}}<hr id=answer>{{Back}}"},
    {"name":"Vietnamese to English", "qfmt":"{{Back}}", "afmt":"{{FrontSide}}<hr id=answer>{{Front}}"},
], css=CSS)
MODEL_TYPE = genanki.Model(1783242365236, "DateTime Type in the answer", fields=[{"name":"Front"},{"name":"Back"}], templates=[
    {"name":"Complete the sentence", "qfmt":"{{Front}}<br><br>{{type:Back}}", "afmt":"{{Front}}<hr id=answer>{{type:Back}}"},
], css=CSS)
MODEL_BASIC = genanki.Model(1783242365233, "DateTime Comprehensive", fields=[{"name":"Front"},{"name":"Back"}], templates=[
    {"name":"Card 1", "qfmt":"{{Front}}", "afmt":"{{FrontSide}}<hr id=answer>{{Back}}"},
], css=CSS)

def safe_name(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

def pronunciation_text(term):
    return term.replace("a.m.", "A M").replace("p.m.", "P M").replace("...", " to ").replace("(fall)", "fall")

def ensure_audio(term):
    name = safe_name(term) + ".mp3"
    path = AUDIO / name
    if not path.exists():
        gTTS(text=pronunciation_text(term), lang="en", slow=False).save(str(path))
    return name

def image_tag(group, term):
    names = IMAGE_FILES[group]
    name = names[sum(ord(character) for character in term) % len(names)]
    return f'<img src="{name}" alt="Date and time illustration">'

def audio_tag(name):
    return f"[sound:{name}]"

def vocab_front(term, ipa, level, audio, group):
    return f'<b style="font-size:29px">{html.escape(term)}</b><br><span style="color:#64748b">{ipa}</span><br>{audio_tag(audio)}<br>{image_tag(group, term)}<br><small>[{level}]</small>'

def vocab_back(term, ipa, meaning, example, notes, level, audio, group):
    return f'<b style="font-size:25px">{html.escape(term)}</b><br>{audio_tag(audio)}<br><span style="color:#64748b">{ipa}</span><br>{image_tag(group, term)}<br><b style="font-size:22px;color:#c2410c">{meaning}</b><br><i>{html.escape(example)}</i><br><small style="color:#4f46e5">Useful: {html.escape(notes)}</small><br><small>[{level}]</small>'

def sentence_front(term, example, level, audio, group):
    target = term.replace(" (fall)", "")
    blanked = re.sub(re.escape(target), "_____", example, count=1, flags=re.IGNORECASE)
    return f'{audio_tag(audio)}<br>{image_tag(group, term)}<br><span style="color:#64748b;font-size:14px">Complete the missing word or phrase</span><br>{html.escape(blanked)}<br><small>[{level}]</small>'

def sentence_back(term, meaning):
    # The type-in model compares this field with the learner's input, so it
    # must contain only the target English answer rather than explanatory HTML.
    return term

def all_media():
    return [str(path) for path in sorted(MEDIA.rglob("*")) if path.is_file()]

def build():
    audio = {term: ensure_audio(term) for term, *_ in WORDS}
    missing = [term for term, filename in audio.items() if not (AUDIO / filename).is_file()]
    if missing:
        raise RuntimeError(f"Audio missing for: {', '.join(missing)}")
    media = all_media()
    if len([p for p in media if p.lower().endswith((".jpg", ".jpeg", ".png", ".svg"))]) < 9:
        raise RuntimeError("Expected at least nine downloaded free-license images before packaging.")

    basic_reversed = genanki.Deck(1990001001, "English Date & Time - Basic and Reversed")
    sentence_mining = genanki.Deck(1990001002, "English Date & Time - Sentence Mining")
    comprehensive = genanki.Deck(1990001003, "English Date & Time - Comprehensive")
    for term, ipa, meaning, example, notes, level, group in WORDS:
        a = audio[term]
        front = vocab_front(term, ipa, level, a, group)
        back = vocab_back(term, ipa, meaning, example, notes, level, a, group)
        tag = [level, group, "datetime"]
        basic_reversed.add_note(genanki.Note(model=MODEL_REV, fields=[front, back], tags=tag))
        sentence_mining.add_note(genanki.Note(model=MODEL_TYPE, fields=[sentence_front(term, example, level, a, group), sentence_back(term, meaning)], tags=tag))
        comprehensive.add_note(genanki.Note(model=MODEL_BASIC, fields=[front, back], tags=tag))

    packages = [
        (basic_reversed, ROOT / "SIP-DateTime-Basic-Reversed.apkg"),
        (sentence_mining, ROOT / "SIP-DateTime-Sentence-Mining.apkg"),
        (comprehensive, ROOT / "SIP-DateTime-Comprehensive.apkg"),
    ]
    for deck, output in packages:
        genanki.Package(deck, media_files=media).write_to_file(str(output))
        print(f"Created {output.name}: {len(deck.notes)} notes")
    print(f"Audio complete: {len(audio)}/{len(WORDS)}")

if __name__ == "__main__":
    build()
