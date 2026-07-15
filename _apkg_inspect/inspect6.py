import zipfile, json, sqlite3, os, sys, hashlib, struct

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

z = zipfile.ZipFile(r'D:\Coding\sip-blog\SIP-Housing-Basic-Reversed.apkg')
media_data = json.loads(z.read('media'))

# ---- CHECK: What are the unique JPEG images? ----
print("=== UNIQUE JPEGS ===")
hashes = {}
for k, v in media_data.items():
    if v.endswith('.jpg'):
        data = z.read(k)
        h = hashlib.md5(data).hexdigest()
        if h not in hashes:
            hashes[h] = []
        hashes[h].append((k, v, len(data)))

for h, entries in sorted(hashes.items()):
    print(f"\n  Hash: {h[:12]}... ({len(entries)} files, total {sum(e[2] for e in entries)} bytes)")
    for idx, fname, sz in entries[:3]:
        print(f"    - {fname} (idx {idx}, {sz} bytes)")
    if len(entries) > 3:
        print(f"    ... and {len(entries)-3} more")

# ---- CHECK: What do the unique images actually look like? ----
# Extract them for manual inspection
print("\n=== EXTRACTING UNIQUE IMAGES ===")
outdir = r'D:\Coding\sip-blog\_apkg_inspect\unique_imgs'
os.makedirs(outdir, exist_ok=True)
seen_hashes = set()
for k, v in sorted(media_data.items(), key=lambda x: int(x[0])):
    if v.endswith('.jpg'):
        data = z.read(k)
        h = hashlib.md5(data).hexdigest()
        if h not in seen_hashes:
            seen_hashes.add(h)
            # Try to find SOF marker for more detail
            pos = 2
            while pos < len(data) - 1:
                if data[pos] == 0xFF:
                    marker = data[pos+1]
                    if marker in (0xC0, 0xC1, 0xC2):
                        h_val = struct.unpack('>H', data[pos+5:pos+7])[0]
                        w_val = struct.unpack('>H', data[pos+7:pos+9])[0]
                        comp = data[pos+2:pos+5].hex()
                        print(f"  {v}: {w_val}x{h_val}, {len(data)} bytes, SOF at {pos}")
                        break
                    elif marker == 0xD8:
                        pos += 2
                    elif marker == 0xDA:
                        print(f"  {v}: {len(data)} bytes (no SOF before SOS)")
                        break
                    else:
                        if pos + 3 < len(data):
                            length = struct.unpack('>H', data[pos+2:pos+4])[0]
                            pos += 2 + length
                        else:
                            break
                else:
                    pos += 1
            # Save the file
            fpath = os.path.join(outdir, v)
            with open(fpath, 'wb') as f:
                f.write(data)

# ---- CHECK: Files 0-108 (mp3) content deep dive ----
print("\n=== MP3 FILE DEEP DIVE ===")
for idx_str in ['0', '5', '10']:
    fname = media_data[idx_str]
    data = z.read(idx_str)
    print(f"\n  File {idx_str} ({fname}): {len(data)} bytes")
    
    # Show first 64 bytes as hex
    hexdump = ' '.join(f'{b:02X}' for b in data[:64])
    print(f"    First 64 bytes: {hexdump}")
    
    # Find all MPEG sync patterns
    frame_starts = []
    for i in range(len(data) - 1):
        if data[i] == 0xFF and (data[i+1] & 0xE0) == 0xE0:
            frame_starts.append(i)
    
    print(f"    MPEG sync patterns found: {len(frame_starts)}")
    if frame_starts:
        # Check frame rate
        if len(frame_starts) >= 2:
            frame_spacing = frame_starts[1] - frame_starts[0]
            print(f"    Frame spacing: {frame_spacing} bytes")
    
    # Check for ID3
    if data[:3] == b'ID3':
        print(f"    Has ID3v2 header")
    else:
        print(f"    No ID3v2 header")

    # Check content after the zeros - is there actual audio data?
    # Find first non-zero after position 16
    nonzero_pos = 16
    while nonzero_pos < len(data) and data[nonzero_pos] == 0:
        nonzero_pos += 1
    print(f"    First non-zero byte at offset: {nonzero_pos}")
    if nonzero_pos < len(data):
        print(f"    Data at that point: {data[nonzero_pos:nonzero_pos+20].hex()}")
    else:
        print(f"    ALL ZEROS after offset 16!")

# ---- CHECK: The version compatibility ----
print("\n=== ANKI VERSION INFO ===")
conn = sqlite3.connect(r'D:\Coding\sip-blog\_apkg_inspect\collection.anki2')
cur = conn.cursor()
cur.execute("SELECT ver, crt, mod FROM col")
ver, crt, mod = cur.fetchone()
print(f"Collection version: {ver}")
print(f"Created: {crt}")
print(f"Modified: {mod}")

# Check if there are any notes with issues
cur.execute("SELECT COUNT(*) FROM notes")
note_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM cards")
card_count = cur.fetchone()[0]
print(f"Notes: {note_count}, Cards: {card_count}")
print(f"Expected cards (2 templates * 110 notes): {110*2}")

# Check field separator usage - any notes that have escaped separators?
cur.execute("SELECT id, flds FROM notes LIMIT 1")
row = cur.fetchone()
sep_count = row[1].count('\x1f')
print(f"Field separators in first note: {sep_count} (expected 9 for 10 fields)")

cur.close()
conn.close()
z.close()

print("\n=== DONE ===")
print(f"Unique images saved to: {outdir}")
