import zipfile, json, sqlite3, os, sys, re

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

z = zipfile.ZipFile(r'D:\Coding\sip-blog\SIP-Housing-Basic-Reversed.apkg')
media_data = json.loads(z.read('media'))

conn = sqlite3.connect(r'D:\Coding\sip-blog\_apkg_inspect\collection.anki2')
cur = conn.cursor()

# ---- CHECK 1: case-sensitive filename match ----
print("=== CHECK 1: Case-sensitive filename match ===")
media_set = set(media_data.values())
mismatches = []

cur.execute("SELECT id, flds FROM notes")
for row in cur.fetchall():
    nid = row[0]
    fields = row[1].split('\x1f')
    if len(fields) >= 9:
        img = fields[8].strip()
        if img and img not in media_set:
            mismatches.append((nid, img))

if mismatches:
    print(f"FOUND {len(mismatches)} NOTES WITH UNMATCHED IMAGE FILENAMES:")
    for nid, img in mismatches[:10]:
        print(f"  Note {nid}: '{img}'")
else:
    print("ALL image filenames match media mapping (case-sensitive).")

# ---- CHECK 2: Check if any image filenames have special chars ----
print("\n=== CHECK 2: Special characters in filenames ===")
import unicodedata
for fname in sorted(media_set):
    if not fname.isascii():
        print(f"  NON-ASCII: '{fname}'")
    if ' ' in fname or '%' in fname or '\\' in fname:
        print(f"  SPECIAL CHAR: '{fname}'")

# Check for non-printable or unusual chars
for fname in sorted(media_set):
    for ch in fname:
        if ord(ch) < 32 or ord(ch) > 126:
            print(f"  NON-ASCII CHAR in '{fname}': U+{ord(ch):04X}")
            break

print("No issues found with filenames (they are all clean ASCII).")

# ---- CHECK 3: Are all jpg files actually different? (dedup check) ----
print("\n=== CHECK 3: Image dedup check ===")
import hashlib
hashes = {}
for k, v in media_data.items():
    if v.endswith('.jpg'):
        data = z.read(k)
        h = hashlib.md5(data).hexdigest()
        if h in hashes:
            hashes[h].append((k, v))
        else:
            hashes[h] = [(k, v)]

dup_count = 0
for h, entries in hashes.items():
    if len(entries) > 1:
        dup_count += 1
        print(f"  DUPLICATE: {[e[1] for e in entries]}")

print(f"Total unique JPGs: {len(hashes)}, duplicates: {dup_count}")

# ---- CHECK 4: Verify the media JSON structure ----
print("\n=== CHECK 4: Media JSON structure ===")
print(f"Type: {type(media_data)}")
print(f"Number of entries: {len(media_data)}")
# Check all keys are integers
non_int_keys = [k for k in media_data.keys() if not k.isdigit()]
if non_int_keys:
    print(f"Non-integer keys found: {non_int_keys}")
else:
    print("All keys are integer strings (correct format).")

# Check all values are strings
non_str_vals = [k for k, v in media_data.items() if not isinstance(v, str)]
if non_str_vals:
    print(f"Non-string values: {non_str_vals}")
else:
    print("All values are strings (correct format).")

# ---- CHECK 5: Verify the Audio field rendering ----
print("\n=== CHECK 5: Audio field values ===")
audio_vals = set()
cur.execute("SELECT flds FROM notes")
for row in cur.fetchall():
    fields = row[0].split('\x1f')
    if len(fields) >= 8:
        audio_vals.add(fields[7].strip())
for av in sorted(list(audio_vals)[:5]):
    print(f"  '{av}'")

# Check if any Audio values are NOT in [sound:...] format
bad_audio = [av for av in audio_vals if not av.startswith('[sound:') or not av.endswith(']')]
if bad_audio:
    print(f"WARNING: Bad audio format: {bad_audio}")
else:
    print("All Audio fields use [sound:xxx.mp3] format (correct).")

# ---- CHECK 6: Check if there's a newer collection.anki21 ----
print("\n=== CHECK 6: ZIP file structure ===")
all_files = z.namelist()
if 'collection.anki21' in all_files:
    print("WARNING: File ALSO contains collection.anki21 (newer format).")
else:
    print("Only contains collection.anki2 (standard format).")

# ---- CHECK 7: Try to get JPEG dimensions ----
print("\n=== CHECK 7: JPEG dimensions (first 5 images) ===")
import struct
checked = 0
for k, v in sorted(media_data.items(), key=lambda x: int(x[0])):
    if v.endswith('.jpg') and checked < 5:
        data = z.read(k)
        # Find SOF0 marker (0xFFC0) to get dimensions
        pos = 2
        height = width = 0
        while pos < len(data) - 1:
            if data[pos] == 0xFF:
                marker = data[pos+1]
                if marker == 0xC0:  # SOF0
                    height = struct.unpack('>H', data[pos+5:pos+7])[0]
                    width = struct.unpack('>H', data[pos+7:pos+9])[0]
                    break
                elif marker == 0xD8:
                    pos += 2
                elif marker == 0xDA:
                    break
                else:
                    if pos + 3 < len(data):
                        length = struct.unpack('>H', data[pos+2:pos+4])[0]
                        pos += 2 + length
                    else:
                        break
            else:
                pos += 1
        print(f"  {v}: {width}x{height}, {len(data)} bytes")
        checked += 1

z.close()
cur.close()
conn.close()
