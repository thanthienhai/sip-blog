"""
Build exactly like VOCAL-TOEIC: use standard Anki models, HTML-in-field.
Images + audio embedded as IMG/SOUND tags in Front/Back field content.
"""
import genanki, os, sys, time
from gtts import gTTS

OUT = r"D:\Coding\sip-blog"
MDIR = os.path.join(OUT, "media")
ADIR = os.path.join(MDIR, "audio")
os.makedirs(ADIR, exist_ok=True)

WORDS = [
    ["accommodation", "/əˌkɑːməˈdeɪʃn/", "chỗ ở, nơi ở", "The university offers accommodation for first-year students.", "student accommodation, temporary accommodation, provide accommodation", "B1", "university accommodation building"],
    ["dormitory (dorm)", "/ˈdɔːrmətɔːri/", "ký túc xá", "I share a room with three others in the dormitory.", "live in a dormitory, dorm room, dormitory life", "A2", "dorm room with bunk beds"],
    ["student housing", "/ˈstuːdnt ˈhaʊzɪŋ/", "nhà ở cho sinh viên", "Student housing near campus is quite expensive.", "off-campus student housing, apply for student housing", "A2", "student apartment building near campus"],
    ["rental room", "/ˈrentl ruːm/", "phòng cho thuê", "He is looking for a rental room near the university.", "look for a rental room, rental room available", "A2", "room for rent sign on window"],
    ["boarding house", "/ˈbɔːrdɪŋ haʊs/", "nhà trọ", "Many students live in boarding houses around the school.", "boarding house owner, live in a boarding house", "B1", "old house with multiple rooms for rent"],
    ["shared house", "/ʃerd haʊs/", "nhà ở ghép, nhà chung", "We rent a shared house with four bedrooms.", "live in a shared house, shared house rules", "A2", "group of students in a shared living room"],
    ["studio apartment", "/ˈstuːdiəʊ əˈpɑːrtmənt/", "căn hộ studio", "A studio apartment is cheaper but smaller.", "rent a studio apartment, studio apartment layout", "B1", "small studio flat with bed and kitchen in one room"],
    ["apartment", "/əˈpɑːrtmənt/", "căn hộ, chung cư", "She lives in a two-bedroom apartment downtown.", "apartment building, apartment complex, luxury apartment", "A1", "apartment building exterior"],
    ["flat", "/flæt/", "căn hộ (Anh-Anh)", "They just moved into a new flat on the third floor.", "a flat in London, ground floor flat, flat hunting", "A1", "flat in London city area"],
    ["homestay", "/ˈhoʊmsteɪ/", "ở cùng gia đình bản xứ", "Staying in a homestay helps improve your language skills.", "homestay family, homestay program, arrange a homestay", "B1", "family welcoming student into their home"],
    ["tenant", "/ˈtenənt/", "người thuê nhà", "The tenant pays rent on the first of every month.", "tenant rights, new tenant, responsible tenant", "B2", "person signing rental contract"],
    ["landlord", "/ˈlændlɔːrd/", "chủ nhà, chủ trọ", "The landlord comes to collect rent every month.", "contact the landlord, landlord responsibilities", "B1", "man collecting rent from tenant"],
    ["landlady", "/ˈlændleɪdi/", "chủ nhà, chủ trọ (nữ)", "The landlady lives on the ground floor of the building.", "the landlady said, ask the landlady", "B1", "woman showing apartment to renter"],
    ["roommate", "/ˈruːmmeɪt/", "bạn cùng phòng", "My roommate and I split the rent equally.", "find a roommate, get along with roommate", "A2", "two people sharing a bedroom"],
    ["housemate", "/ˈhaʊsmeɪt/", "bạn cùng nhà", "I have three housemates but my own bedroom.", "housemate agreement, get along with housemates", "A2", "people sharing a house in common areas"],
    ["flatmate", "/ˈflætmeɪt/", "bạn cùng căn hộ", "My flatmate is a student from France.", "looking for a flatmate, share with a flatmate", "A2", "students sharing a flat kitchen"],
    ["lease", "/liːs/", "hợp đồng thuê nhà", "I signed a one-year lease for this apartment.", "sign a lease, break a lease, lease expires", "B1", "signed rental contract document"],
    ["tenancy agreement", "/ˈtenənsi əˈɡriːmənt/", "hợp đồng thuê nhà (trang trọng)", "Read the tenancy agreement carefully before signing.", "tenancy agreement template, terms of the tenancy agreement", "B2", "legal rental document with signatures"],
    ["rent (n)", "/rent/", "tiền thuê nhà", "The rent is $500 per month including utilities.", "pay the rent, monthly rent, rent increase", "A1", "money and house keys exchange"],
    ["rent (v)", "/rent/", "thuê, cho thuê", "They rent a small apartment near campus.", "rent out a room, rent from a landlord, for rent", "A1", "for rent sign on a building"],
    ["deposit", "/dɪˈpɑːzɪt/", "tiền đặt cọc", "You need to pay a deposit equal to one month's rent.", "pay a deposit, refundable deposit, deposit required", "B1", "handing over cash as deposit"],
    ["security deposit", "/sɪˈkjʊrəti dɪˈpɑːzɪt/", "tiền đặt cọc đảm bảo", "The security deposit will be returned when you move out.", "get the security deposit back, security deposit refund", "B2", "getting deposit money back after moving out"],
    ["down payment", "/daʊn ˈpeɪmənt/", "tiền trả trước", "He made a down payment of three months' rent.", "make a down payment, save for a down payment", "B2", "large cash payment upfront"],
    ["utilities", "/juːˈtɪlətiz/", "tiền điện nước, tiện ích", "Are utilities included in the monthly rent?", "pay utilities, utilities included, utility bills", "B1", "electricity meter water pipes bills"],
    ["electricity bill", "/ɪˌlekˈtrɪsəti bɪl/", "tiền điện", "The electricity bill is usually higher in summer.", "pay the electricity bill, high electricity bill", "A2", "electricity bill paper or meter"],
    ["water bill", "/ˈwɔːtər bɪl/", "tiền nước", "The water bill is shared among all tenants.", "split the water bill, monthly water bill", "A2", "water tap and bill paper"],
    ["internet bill", "/ˈɪntərnet bɪl/", "tiền mạng", "We split the internet bill four ways.", "pay the internet bill, internet bill included", "A2", "wifi router and bill"],
    ["gas bill", "/ɡæs bɪl/", "tiền ga", "The gas bill covers cooking and heating.", "gas bill payment, unpaid gas bill", "B1", "gas stove gas meter bill"],
    ["maintenance fee", "/ˈmeɪntənəns fiː/", "phí bảo trì", "The landlord is responsible for the maintenance fee.", "monthly maintenance fee, pay maintenance fee", "B2", "repair person fixing something in apartment"],
    ["service charge", "/ˈsɜːrvɪs tʃɑːrdʒ/", "phí dịch vụ", "There is an extra service charge for the cleaning service.", "service charge applies, additional service charge", "B2", "cleaning staff in hallway"],
    ["move in", "/muːv ɪn/", "chuyển vào, dọn vào", "We're planning to move in next weekend.", "move in date, ready to move in, just moved in", "A2", "people carrying boxes into new home"],
    ["move out", "/muːv aʊt/", "chuyển đi, dọn ra", "You must give one month's notice before moving out.", "move out date, plan to move out, move out process", "A2", "people carrying boxes out of house"],
    ["notice period", "/ˈnoʊtɪs ˌpɪriəd/", "thời gian báo trước", "The notice period is one month before leaving.", "one month's notice period, give notice", "B2", "calendar showing one month ahead"],
    ["eviction", "/ɪˈvɪkʃn/", "trục xuất, đuổi khỏi nhà", "He faced eviction for not paying rent for three months.", "face eviction, eviction notice, threat of eviction", "C1", "person being forced to leave with belongings"],
    ["sublet", "/ˈsʌblet/", "cho thuê lại", "It's not allowed to sublet the room without permission.", "sublet a room, sublet agreement, looking to sublet", "C1", "one renter handing keys to another"],
    ["furnished", "/ˈfɜːrnɪʃt/", "có sẵn nội thất", "The apartment is fully furnished with a bed and desk.", "fully furnished, partly furnished, well-furnished", "B1", "furniture in empty room before and after"],
    ["unfurnished", "/ʌnˈfɜːrnɪʃt/", "không có nội thất", "An unfurnished room is cheaper but you need to buy furniture.", "unfurnished apartment, unfurnished room for rent", "B1", "empty room with no furniture"],
    ["fully furnished", "/ˈfʊli ˈfɜːrnɪʃt/", "đầy đủ nội thất", "The room is fully furnished with modern appliances.", "fully furnished apartment, fully furnished and equipped", "B1", "room with all furniture sofa bed table"],
    ["semi-furnished", "/ˈsemi ˈfɜːrnɪʃt/", "nội thất cơ bản", "The semi-furnished unit has a bed and wardrobe only.", "semi-furnished room, semi-furnished rental", "B2", "room with only bed and wardrobe"],
    ["bedroom", "/ˈbedruːm/", "phòng ngủ", "Each tenant has their own bedroom.", "master bedroom, spare bedroom, three-bedroom", "A1", "cozy bedroom with bed and desk"],
    ["living room", "/ˈlɪvɪŋ ruːm/", "phòng khách", "The living room has a sofa and a TV.", "living room furniture, spacious living room", "A1", "living room with sofa and TV"],
    ["kitchen", "/ˈkɪtʃɪn/", "nhà bếp, phòng bếp", "The kitchen is shared among all housemates.", "shared kitchen, kitchen appliances, kitchen cabinet", "A1", "shared kitchen with stove and fridge"],
    ["bathroom", "/ˈbæθruːm/", "phòng tắm, nhà vệ sinh", "Is the bathroom private or shared?", "shared bathroom, private bathroom", "A1", "clean bathroom with shower and toilet"],
    ["shared bathroom", "/ʃerd ˈbæθruːm/", "nhà vệ sinh chung", "The dorm has shared bathrooms on each floor.", "use a shared bathroom, shared bathroom facilities", "A2", "bathroom used by multiple people"],
    ["ensuite bathroom", "/ɒnˈswiːt ˈbæθruːm/", "phòng tắm riêng trong phòng", "The master bedroom has an ensuite bathroom.", "room with ensuite, ensuite bathroom included", "B2", "bedroom connected to private bathroom"],
    ["balcony", "/ˈbælkəni/", "ban công", "The room has a nice balcony overlooking the street.", "private balcony, balcony view, step out onto the balcony", "A2", "small balcony with chairs and plant"],
    ["basement", "/ˈbeɪsmənt/", "tầng hầm", "The washing machine is in the basement.", "basement apartment, basement floor, damp basement", "B1", "underground room with washing machines"],
    ["attic", "/ˈætɪk/", "tầng áp mái, gác xép", "They converted the attic into a small bedroom.", "attic room, attic conversion, attic space", "B2", "small room under the roof with slanted ceiling"],
    ["ground floor", "/ˌɡraʊnd ˈflɔːr/", "tầng trệt", "The landlady lives on the ground floor.", "on the ground floor, ground floor flat", "A2", "building entrance at street level"],
    ["corridor", "/ˈkɔːrɪdɔːr/", "hành lang", "The corridor leads to all the rooms on this floor.", "long corridor, narrow corridor, along the corridor", "B1", "long hallway with many doors"],
    ["staircase", "/ˈsterkeɪs/", "cầu thang", "The staircase is narrow but well-lit.", "spiral staircase, wooden staircase, climb the staircase", "A2", "stairs inside a building"],
    ["living area", "/ˈlɪvɪŋ ˈeriə/", "không gian sinh hoạt chung", "The living area is spacious and bright.", "open living area, shared living area, common living area", "B1", "open plan living and dining space"],
    ["wardrobe", "/ˈwɔːrdroʊb/", "tủ quần áo", "There's a built-in wardrobe in my room.", "built-in wardrobe, walk-in wardrobe, wardrobe space", "A2", "built in wooden wardrobe with clothes"],
    ["closet", "/ˈklɑːzɪt/", "tủ âm tường", "You'll have plenty of storage in the walk-in closet.", "storage closet, walk-in closet, closet space", "B1", "walk-in closet with shelves and hangers"],
    ["drawer", "/drɔːr/", "ngăn kéo", "I keep my documents in the top drawer.", "top drawer, bottom drawer, chest of drawers", "A2", "open drawer with folded clothes inside"],
    ["bed", "/bed/", "giường", "The room comes with a single bed.", "single bed, double bed, make the bed", "A1", "single bed with white sheets"],
    ["mattress", "/ˈmætrəs/", "nệm, đệm", "You should buy a new mattress for better sleep.", "firm mattress, soft mattress, memory foam mattress", "A2", "new mattress on bed frame"],
    ["desk", "/desk/", "bàn học, bàn làm việc", "I need a large desk for my computer and books.", "study desk, wooden desk, desk lamp, at my desk", "A1", "wooden study desk with laptop"],
    ["chair", "/tʃer/", "ghế", "The room has a desk and a chair.", "desk chair, office chair, comfortable chair", "A1", "simple wooden chair"],
    ["bookshelf", "/ˈbʊkʃelf/", "kệ sách", "My bookshelf is full of textbooks.", "wooden bookshelf, built-in bookshelf, organize bookshelf", "A2", "bookshelf filled with textbooks"],
    ["lamp", "/læmp/", "đèn bàn, đèn ngủ", "I bought a reading lamp for late-night studying.", "desk lamp, table lamp, floor lamp, turn on the lamp", "A2", "desk lamp shining on a book"],
    ["curtain", "/ˈkɜːrtn/", "rèm cửa", "The curtains block out the sunlight in the morning.", "draw the curtains, blackout curtains, curtain rod", "A2", "curtains covering a window"],
    ["heater", "/ˈhiːtər/", "máy sưởi", "The room has a small heater for winter.", "portable heater, electric heater, turn on the heater", "A2", "portable electric heater in room"],
    ["air conditioner", "/ˈer kənˌdɪʃənər/", "điều hòa, máy lạnh", "The air conditioner is essential in the summer.", "turn on the air conditioner, air conditioner remote", "A2", "wall mounted air conditioner unit"],
    ["fan", "/fæn/", "quạt", "A ceiling fan keeps the room cool.", "ceiling fan, electric fan, standing fan", "A1", "ceiling fan spinning in a room"],
    ["water heater", "/ˈwɔːtər ˈhiːtər/", "bình nóng lạnh", "The water heater is not working properly.", "turn on the water heater, water heater broken", "B1", "water heater tank in bathroom"],
    ["microwave", "/ˈmaɪkrəweɪv/", "lò vi sóng", "We share a microwave in the kitchen.", "microwave oven, heat in the microwave, microwave safe", "A2", "microwave oven in kitchen"],
    ["fridge", "/frɪdʒ/", "tủ lạnh", "There's a mini-fridge in my room.", "mini-fridge, fridge freezer, put in the fridge", "A2", "refrigerator full of food"],
    ["stove", "/stoʊv/", "bếp nấu", "The kitchen has an electric stove.", "electric stove, gas stove, stove top", "A2", "electric stove with pots on top"],
    ["oven", "/ˈʌvən/", "lò nướng", "The oven hasn't been cleaned in months.", "electric oven, preheat the oven, oven tray", "A2", "kitchen oven with food inside"],
    ["kettle", "/ˈketl/", "ấm đun nước", "I use an electric kettle to make tea.", "electric kettle, boil the kettle, fill the kettle", "A2", "electric kettle with steam"],
    ["rice cooker", "/raɪs ˈkʊkər/", "nồi cơm điện", "Every student needs a rice cooker!", "electric rice cooker, cook rice in a rice cooker", "B1", "rice cooker steaming on kitchen counter"],
    ["washing machine", "/ˈwɑːʃɪŋ məˌʃiːn/", "máy giặt", "The washing machine is coin-operated.", "load the washing machine, washing machine cycle", "A2", "washing machine with clothes inside"],
    ["vacuum cleaner", "/ˈvækjuːm ˈkliːnər/", "máy hút bụi", "We take turns using the vacuum cleaner.", "use the vacuum cleaner, cordless vacuum cleaner", "A2", "vacuum cleaner on floor"],
    ["WiFi", "/ˈwaɪfaɪ/", "mạng WiFi, internet", "High-speed WiFi is included in the rent.", "connect to WiFi, WiFi password, WiFi signal, free WiFi", "A1", "wifi router with blinking lights"],
    ["parking space", "/ˈpɑːrkɪŋ speɪs/", "chỗ đỗ xe", "Is there a parking space for my motorbike?", "find a parking space, designated parking space", "A2", "empty parking spot with white lines"],
    ["bike rack", "/baɪk ræk/", "chỗ để xe đạp", "The dorm has a bike rack outside.", "lock your bike at the rack, covered bike rack", "B1", "bicycle rack with several bikes locked"],
    ["gym", "/dʒɪm/", "phòng tập gym", "The building has a small gym for residents.", "on-site gym, gym facilities, gym access", "A2", "small gym with treadmill and weights"],
    ["laundry room", "/ˈlɔːndri ruːm/", "phòng giặt đồ", "The laundry room is on the basement floor.", "use the laundry room, laundry room hours", "B1", "room with washing machines and dryers"],
    ["study room", "/ˈstʌdi ruːm/", "phòng tự học", "The dorm has a quiet study room.", "24-hour study room, group study room, reserve a study room", "A2", "quiet room with desks and lamps"],
    ["common room", "/ˈkɑːmən ruːm/", "phòng sinh hoạt chung", "Students hang out in the common room after class.", "dorm common room, common room activities", "B1", "lounge area with sofas and TV"],
    ["garden", "/ˈɡɑːrdn/", "sân vườn", "The shared house has a nice garden.", "front garden, back garden, garden maintenance", "A1", "house with a green garden in front"],
    ["rooftop", "/ˈruːftɑːp/", "sân thượng", "There's a rooftop where you can see the whole city.", "rooftop terrace, rooftop access, rooftop view", "B1", "building rooftop with a view of the city"],
    ["parking lot", "/ˈpɑːrkɪŋ lɑːt/", "bãi đỗ xe", "The parking lot is behind the building.", "underground parking lot, parking lot entrance", "A2", "large outdoor car parking area"],
    ["security guard", "/sɪˈkjʊrəti ɡɑːrd/", "bảo vệ", "A security guard watches the entrance at night.", "security guard on duty, building security guard", "B1", "security guard standing at building entrance"],
    ["CCTV", "/ˌsiː siː tiː ˈviː/", "camera an ninh", "The building has CCTV cameras for safety.", "CCTV footage, CCTV system, under CCTV surveillance", "B1", "security camera mounted on wall or ceiling"],
    ["fire alarm", "/ˈfaɪər əˌlɑːrm/", "chuông báo cháy", "Don't ignore the fire alarm during drills.", "fire alarm went off, test the fire alarm", "B1", "red fire alarm on wall"],
    ["fire extinguisher", "/ˈfaɪər ɪkˌstɪŋɡwɪʃər/", "bình chữa cháy", "Each floor has a fire extinguisher.", "use a fire extinguisher, check the fire extinguisher", "B2", "red fire extinguisher mounted on wall"],
    ["smoke detector", "/ˈsmoʊk dɪˌtektər/", "thiết bị báo khói", "The smoke detector went off when I burned the toast.", "smoke detector battery, install a smoke detector", "B1", "white smoke detector on ceiling"],
    ["lock", "/lɑːk/", "ổ khóa, khóa (cửa)", "Make sure to lock the door when you leave.", "door lock, lock the door, change the lock", "A1", "door lock with a key inserted"],
    ["key", "/kiː/", "chìa khóa", "I lost my room key and had to pay for a replacement.", "room key, spare key, lose the key", "A1", "single metal key on a key ring"],
    ["key card", "/kiː kɑːrd/", "thẻ khóa", "You need a key card to enter the building.", "swipe the key card, key card access, lost key card", "A2", "plastic key card being swiped"],
    ["buzzer", "/ˈbʌzər/", "chuông cửa", "Press the buzzer and someone will let you in.", "door buzzer, ring the buzzer, buzzer entry system", "B2", "door buzzer intercom panel on wall"],
    ["intercom", "/ˈɪntərkɑːm/", "hệ thống liên lạc nội bộ", "The intercom connects each apartment to the main entrance.", "intercom system, answer the intercom, video intercom", "B2", "wall mounted intercom handset"],
    ["elevator", "/ˈelɪveɪtər/", "thang máy", "The elevator is out of service again.", "take the elevator, elevator button, elevator broken", "A2", "elevator doors opening in a building"],
    ["fuse box", "/ˈfjuːz bɑːks/", "hộp cầu chì", "Check the fuse box if the power goes out.", "trip the fuse box, check the fuse box, main fuse box", "C1", "electrical fuse box with switches"],
    ["damp", "/dæmp/", "ẩm ướt", "The room gets damp in the rainy season.", "damp room, feel damp, damp patch, damp problem", "B1", "damp wall with water stains"],
    ["mold", "/moʊld/", "nấm mốc", "Tell the landlord if you see mold on the wall.", "black mold, mold problem, mold on the wall, mold removal", "B2", "black mold growing on a wall"],
    ["leak", "/liːk/", "rò rỉ", "There's a leak in the bathroom ceiling.", "water leak, gas leak, fix a leak", "B1", "water dripping from ceiling pipe"],
    ["clog", "/klɑːɡ/", "tắc nghẽn", "The sink is clogged with food scraps.", "clogged sink, clogged toilet, clogged drain", "B2", "sink full of water not draining"],
    ["pest", "/pest/", "sâu bọ, côn trùng", "We found cockroaches in the kitchen.", "pest control, pest problem, household pests", "B1", "cockroach or insect in kitchen"],
    ["rodent", "/ˈroʊdnt/", "động vật gặm nhấm", "There's a rodent problem in the basement.", "rodent infestation, rodent control, rodent problem", "C1", "mouse or rat in a room corner"],
    ["neighbor", "/ˈneɪbər/", "hàng xóm", "The neighbors are friendly but noisy sometimes.", "next-door neighbor, noisy neighbor, get along with neighbors", "A1", "people talking over a fence between houses"],
    ["noise", "/nɔɪz/", "tiếng ồn", "There's too much noise from the street at night.", "make noise, noise complaint, noise level, traffic noise", "A1", "person covering ears from loud sound"],
    ["quiet hours", "/ˈkwaɪət aʊərz/", "giờ yên lặng", "Quiet hours are from 10 PM to 7 AM.", "observe quiet hours, during quiet hours, quiet hours policy", "B2", "clock showing night time 10pm to 7am"],
    ["guest policy", "/ɡest ˈpɑːləsi/", "chính sách khách đến thăm", "Guests are allowed but cannot stay overnight.", "guest policy rules, follow the guest policy", "B1", "sign listing visitor rules"],
    ["curfew", "/ˈkɜːrfjuː/", "giờ giới nghiêm", "The dormitory has a curfew at midnight.", "impose a curfew, break the curfew, curfew time", "B2", "clock showing midnight with locked door"],
    ["inspection", "/ɪnˈspekʃn/", "kiểm tra phòng", "The landlord does a monthly inspection.", "room inspection, regular inspection, pass the inspection", "B2", "landlord checking a room with clipboard"],
    ["renovation", "/ˌrenəˈveɪʃn/", "sửa chữa, cải tạo", "The building is under renovation.", "under renovation, major renovation, renovation work", "B2", "construction workers renovating a room"],
    ["repair", "/rɪˈper/", "sửa chữa (nhỏ)", "Call the landlord if anything needs repair.", "need repair, repair work, emergency repair", "B1", "handyman fixing a broken faucet"],
]

# Helpers
def safe_name(word):
    return word.split(" (")[0].replace("/", "-").replace(" ", "_").lower()

def ensure_audio(word):
    fname = f"{safe_name(word)}.mp3"
    path = os.path.join(ADIR, fname)
    if os.path.exists(path):
        return fname
    try:
        clean = word.split(" (")[0].strip()
        gTTS(text=clean, lang="en", slow=False).save(path)
        return fname
    except:
        return None

def collect_media():
    files = []
    for d in [ADIR]:
        if os.path.isdir(d):
            for f in os.listdir(d):
                files.append(os.path.join(d, f))
    return files

# --- EXACT models from VOCAL-TOEIC ---

# Same CSS as reference
CSS = """
.card {
    font-family: arial;
    font-size: 20px;
    line-height: 1.5;
    text-align: center;
    color: black;
    background-color: white;
}
.cloze {
    font-weight: bold;
    color: blue;
}
.nightMode .cloze {
    color: lightblue;
}
"""

# Basic (and reversed) - for Vocab deck
MODEL_REV = genanki.Model(
    1783242364234,
    "Basic (and reversed card)",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[
        {"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}"},
        {"name": "Card 2", "qfmt": "{{Back}}", "afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Front}}"},
    ],
    css=CSS,
)

# Basic (type in the answer) - for Sentence Mining
MODEL_TYPE = genanki.Model(
    1783242364236,
    "Basic (type in the answer)",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{
        "name": "Card 1",
        "qfmt": "{{Front}}\n\n{{type:Back}}",
        "afmt": "{{Front}}\n\n<hr id=answer>\n\n{{type:Back}}",
    }],
    css=CSS,
)

# Basic - for Comprehensive
MODEL_BASIC = genanki.Model(
    1783242364233,
    "Basic",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{
        "name": "Card 1",
        "qfmt": "{{Front}}",
        "afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}",
    }],
    css=CSS,
)


# ============================================================
# Phase 1: Generate audio
# ============================================================
print("=" * 50)
print("PHASE 1: Audio")
print("=" * 50)

audio = {}

for i, w in enumerate(WORDS):
    word, ipa, meaning, example, colloc, level, hint = w
    sn = safe_name(word)
    af = ensure_audio(word)
    audio[sn] = af
    a_s = "OK" if af else "FAIL"
    print(f"  [{i+1:3d}/{len(WORDS)}] {word:30s} audio={a_s}")
    sys.stdout.flush()

# ============================================================
# Phase 2: Build field HTML
# ============================================================
print()
print("=" * 50)
print("PHASE 2: Building .apkg")
print("=" * 50)

media = collect_media()

def atag(af): return f"[sound:{af}]" if af else ""

# Vocab: Brief front (word+image+audio), detailed back
def front_vocab(word, ipa, level, af):
    parts = []
    parts.append(f'<b style="font-size:28px;">{word}</b>')
    parts.append(f'<br><span style="color:#666;">{ipa}</span>')
    if af:
        parts.append(atag(af))
    parts.append(f'<br><small style="color:#888;">[{level}]</small>')
    return "\n".join(parts)

def back_vocab(word, ipa, meaning, example, colloc, level, af):
    parts = []
    parts.append(f'<b style="font-size:24px;">{word}</b>')
    if af:
        parts.append(atag(af))
    parts.append(f'<br><span style="color:#666;">{ipa}</span>')
    parts.append(f'<br><b style="font-size:22px;color:#e65100;">{meaning}</b>')
    parts.append(f'<br><i style="color:#444;">{example}</i>')
    if colloc:
        parts.append(f'<br><small style="color:#5c6bc0;">Collocations: {colloc}</small>')
    parts.append(f'<br><small style="color:#888;">[{level}]</small>')
    return "\n".join(parts)

# Sentence Mining front
def front_sentence(example, word, level, af):
    clean = word.split(" (")[0].strip()
    cloze = example.replace(clean, "{{c1::" + clean + "}}", 1)
    parts = []
    if af:
        parts.append(atag(af))
    parts.append(f'<p style="color:#999;font-size:13px;">Fill in the missing word</p>')
    parts.append(cloze)
    parts.append(f'<small style="color:#888;">[{level}]</small>')
    return "\n".join(parts)

def back_sentence(word, meaning):
    clean = word.split(" (")[0].strip()
    return f'<b style="font-size:22px;color:#e65100;">{clean}</b><br><span style="color:#666;">{meaning}</span>'


# Deck 1: Vocab (Basic and reversed)
deck1 = genanki.Deck(1990000001, "Student Housing - Basic and Reversed")
for w in WORDS:
    word, ipa, meaning, example, colloc, level, hint = w
    sn = safe_name(word)
    af = audio.get(sn)
    f = front_vocab(word, ipa, level, af)
    b = back_vocab(word, ipa, meaning, example, colloc, level, af)
    deck1.add_note(genanki.Note(model=MODEL_REV, fields=[f, b], tags=[level]))

p1 = os.path.join(OUT, "SIP-Housing-Basic-Reversed.apkg")
genanki.Package(deck1, media_files=media).write_to_file(p1)
print(f"  [1/3] {os.path.basename(p1)} ({len(deck1.notes)}n x 2)")

# Deck 2: Sentence Mining (Type in the answer)  
deck2 = genanki.Deck(1990000002, "Student Housing - Sentence Mining")
for w in WORDS:
    word, ipa, meaning, example, colloc, level, hint = w
    sn = safe_name(word)
    af = audio.get(sn)
    f = front_sentence(example, word, level, af)
    b = back_sentence(word, meaning)
    deck2.add_note(genanki.Note(model=MODEL_TYPE, fields=[f, b], tags=[level]))

p2 = os.path.join(OUT, "SIP-Housing-Sentence-Mining.apkg")
genanki.Package(deck2, media_files=media).write_to_file(p2)
print(f"  [2/3] {os.path.basename(p2)} ({len(deck2.notes)} type-in)")

# Deck 3: Comprehensive (Basic)
deck3 = genanki.Deck(1990000003, "Student Housing - Comprehensive")
for w in WORDS:
    word, ipa, meaning, example, colloc, level, hint = w
    sn = safe_name(word)
    af = audio.get(sn)
    f = front_vocab(word, ipa, level, af)
    b = back_vocab(word, ipa, meaning, example, colloc, level, af)
    deck3.add_note(genanki.Note(model=MODEL_BASIC, fields=[f, b], tags=[level]))

p3 = os.path.join(OUT, "SIP-Housing-Comprehensive.apkg")
genanki.Package(deck3, media_files=media).write_to_file(p3)
print(f"  [3/3] {os.path.basename(p3)} ({len(deck3.notes)} cards)")

a_ok = sum(1 for v in audio.values() if v)
print(f"\nDone: audio={a_ok}/{len(WORDS)}")
