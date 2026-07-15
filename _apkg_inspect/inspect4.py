import zipfile, json, sqlite3, os, sys, struct

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

z = zipfile.ZipFile(r'D:\Coding\sip-blog\SIP-Housing-Basic-Reversed.apkg')

# 1. Extract accommodation.jpg and verify it's a valid JPEG
outdir = r'D:\Coding\sip-blog\_apkg_inspect\media'
os.makedirs(outdir, exist_ok=True)

media_data = json.loads(z.read('media'))

# Extract a JPG
for idx_str, fname in media_data.items():
    if fname == 'accommodation.jpg':
        jpg_data = z.read(idx_str)
        with open(os.path.join(outdir, fname), 'wb') as f:
            f.write(jpg_data)
        print(f"Extracted {fname} ({len(jpg_data)} bytes)")

        # Parse JPEG markers to verify it's complete
        pos = 2  # skip SOI
        markers = []
        while pos < len(jpg_data) - 1:
            if jpg_data[pos] != 0xFF:
                break
            marker = jpg_data[pos+1]
            markers.append(f'0xFF{marker:02X}')
            if marker == 0xD8:  # SOI
                pos += 2
            elif marker == 0xD9:  # EOI
                print(f"  Valid JPEG: {len(markers)} markers, ends with EOI at offset {pos}")
                break
            elif marker == 0xDA:  # SOS (Start of Scan) - rest is image data
                pos += 2
                # Find next marker (skip compressed data)
                while pos < len(jpg_data) - 1:
                    if jpg_data[pos] == 0xFF and jpg_data[pos+1] != 0x00 and jpg_data[pos+1] != 0xFF:
                        break
                    pos += 1
            else:
                if pos + 3 < len(jpg_data):
                    length = struct.unpack('>H', jpg_data[pos+2:pos+4])[0]
                    pos += 2 + length
                else:
                    break
        print(f"  Markers found: {markers}")
        break

# 2. Check collection.anki2 schema version and full structure
conn = sqlite3.connect(r'D:\Coding\sip-blog\_apkg_inspect\collection.anki2')
cur = conn.cursor()

# Get schema info
print("\n=== Collection DB Schema ===")
for row in cur.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name"):
    if row[0]:
        print(row[0][:500])

# Check col table version and other columns
print("\n=== Collection Config ===")
cur.execute("PRAGMA table_info(col)")
cols = cur.fetchall()
print(f"Columns: {[c[1] for c in cols]}")

cur.execute("SELECT * FROM col")
col_row = cur.fetchone()
print(f"\ncol row ({len(col_row)} columns):")
for i, c in enumerate(cols):
    val = str(col_row[i])[:200]
    print(f"  {c[1]}: {val}")

# Check decks
print("\n=== Decks ===")
cur.execute("PRAGMA table_info(decks)")
deck_cols = cur.fetchall()
print(f"Columns: {[c[1] for c in deck_cols]}")

cur.execute("SELECT id, name FROM decks")
for row in cur.fetchall():
    print(f"  Deck: id={row[0]}, name={row[1]}")

# Check the media mapping in the col table (some versions store it there)
if 'media' in [c[1] for c in cols]:
    col_media = json.loads(col_row[cols.index([c for c in cols if c[1] == 'media'][0])])
    print(f"\nCol media has {len(col_media)} entries")

# Check conf column for deck configs
for i, c in enumerate(cols):
    if c[1] == 'conf':
        conf = json.loads(col_row[i])
        print(f"\nDeck configs: {json.dumps(conf, indent=2)[:500]}")

cur.close()
conn.close()

# 3. Check the actual file 0 (first mp3) more thoroughly
print("\n=== File 0 content analysis (accommodation.mp3) ===")
data0 = z.read('0')
print(f"Size: {len(data0)} bytes")
# Look for MPEG frame sync patterns
frame_offsets = []
for i in range(len(data0) - 1):
    if data0[i] == 0xFF and (data0[i+1] & 0xE0) == 0xE0:
        frame_offsets.append(i)
print(f"MPEG sync patterns found: {len(frame_offsets)}")
if frame_offsets:
    print(f"  Offsets: {frame_offsets[:10]}")
    # Show hex at first frame
    off = frame_offsets[0]
    print(f"  Frame at {off}: {data0[off:off+4].hex()}")

# Check for ID3v2 header at start
if data0[:3] == b'ID3':
    print(f"  ID3v2 header found")
else:
    print(f"  No ID3v2 header (starts with: {data0[:20].hex()})")

z.close()
