import zipfile, json, hashlib, struct, os, sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

z = zipfile.ZipFile(r'D:\Coding\sip-blog\SIP-Housing-Basic-Reversed.apkg')

# ---- CHECK: ZIP integrity ----
print("=== ZIP INTEGRITY CHECK ===")
bad_crc = []
for info in z.infolist():
    if info.filename.isdigit():
        data = z.read(info.filename)
        actual_crc = z.crc32(data) & 0xFFFFFFFF
        if actual_crc != info.CRC:
            bad_crc.append((info.filename, info.CRC, actual_crc))
            print(f"  CRC MISMATCH for file {info.filename}: stored={info.CRC:08X}, actual={actual_crc:08X}")

if not bad_crc:
    print("All CRC checksums valid.")
else:
    print(f"TOTAL CRC ERRORS: {len(bad_crc)}")

# ---- CHECK: Test extracting JSON data properly ----
print("\n=== MEDIA JSON ===\n")
# Read and parse carefully
raw_media = z.read('media')
print(f"Media file size: {len(raw_media)} bytes")
print(f"First 200 chars: {raw_media[:200].decode('utf-8', errors='replace')}")

media_data = json.loads(raw_media)

# Check for any key that's not a digit
non_digit_keys = [k for k in media_data if not isinstance(k, str) or not k.isdigit()]
print(f"Non-integer keys: {non_digit_keys}")

# Check for duplicate filenames
from collections import Counter
fname_counts = Counter(media_data.values())
dups = {k: v for k, v in fname_counts.items() if v > 1}
if dups:
    print(f"Duplicate filenames: {dups}")
else:
    print("No duplicate filenames in mapping.")

# ---- CHECK: collection.anki2 integrity ----
print("\n=== COLLECTION DB DUMP ===")
import sqlite3
conn = sqlite3.connect(r'D:\Coding\sip-blog\_apkg_inspect\collection.anki2')

# Quick integrity check
cur = conn.cursor()
cur.execute("PRAGMA integrity_check")
result = cur.fetchone()[0]
print(f"DB integrity: {result}")

# Check schema version
cur.execute("SELECT ver FROM col")
ver = cur.fetchone()[0]
print(f"Schema version: {ver}")

# Dump the first card to see nid, ord, etc
cur.execute("SELECT * FROM cards LIMIT 1")
card = cur.fetchone()
card_cols = [d[1] for d in cur.execute("PRAGMA table_info(cards)").fetchall()]
for c, v in zip(card_cols, card):
    print(f"  cards.{c}: {v}")

# ---- CHECK: Render ALL notes to see if any have unexpected Image field values ----
cur.execute("SELECT flds FROM notes")
print("\n=== ALL IMAGE FIELD VALUES ===")
image_vals = {}
for row in cur.fetchall():
    fields = row[0].split('\x1f')
    if len(fields) >= 9:
        img = fields[8]
        image_vals[img] = image_vals.get(img, 0) + 1

for img, count in sorted(image_vals.items()):
    print(f"  '{img}' -> {count} note(s)")

# Check if any image value doesn't end with .jpg
bad_img = [v for v in image_vals if not v.endswith('.jpg')]
if bad_img:
    print(f"WARNING: Non-jpg image references: {bad_img}")

# ---- CHECK: Is there a _media or media JSON column in col table? ----
col_cols = [d[1] for d in cur.execute("PRAGMA table_info(col)").fetchall()]
print(f"\n=== COL TABLE COLUMNS ===")
print(f"  {col_cols}")

# The 'models' column
cur.execute("SELECT models FROM col")
models_json = cur.fetchone()[0]
models = json.loads(models_json)

# Check if model has 'req' field (required fields per template)
for mid, model in models.items():
    for tmpl in model.get('tmpls', []):
        tmpl_name = tmpl.get('name', 'unknown')
        req = tmpl.get('req', None)
        print(f"\n  Template '{tmpl_name}' req: {req}")

cur.close()
conn.close()
z.close()
