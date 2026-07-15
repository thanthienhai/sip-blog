import zipfile, json, sqlite3, os, sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

z = zipfile.ZipFile(r'D:\Coding\sip-blog\SIP-Housing-Basic-Reversed.apkg')

os.makedirs(r'D:\Coding\sip-blog\_apkg_inspect', exist_ok=True)

conn = sqlite3.connect(r'D:\Coding\sip-blog\_apkg_inspect\collection.anki2')
cur = conn.cursor()

# Get the model and its fields
cur.execute("SELECT models FROM col")
models = json.loads(cur.fetchone()[0])

mid = list(models.keys())[0]
model = models[mid]
field_names = [f['name'] for f in model['flds']]
print(f"Field names: {field_names}")

# Check notes - get first 5 notes with their Image field
cur.execute("SELECT flds, sfld, tags FROM notes LIMIT 5")
notes = cur.fetchall()

for i, note in enumerate(notes):
    flds = note[0]
    fields = flds.split('\x1f')
    print(f"\n--- Note {i} ---")
    for j, name in enumerate(field_names):
        val = fields[j] if j < len(fields) else ''
        if name == 'Image':
            print(f"  {name}: '{val}' (len={len(val)})")
        elif name == 'Audio':
            print(f"  {name}: '{val}' (len={len(val)})")
        else:
            v = val[:60].encode('ascii', errors='replace').decode('ascii')
            print(f"  {name}: '{v}'")

# Count how many notes have non-empty Image field
cur.execute("SELECT COUNT(*) FROM notes")
total = cur.fetchone()[0]
print(f"\n\nTotal notes: {total}")

cur.execute("SELECT COUNT(*) FROM notes WHERE flds LIKE '%\x1f%'")
print(f"Notes with separators: {cur.fetchone()[0]}")

# Check Image field specifically
empty_image = 0
with_image = 0
sample_images = []

cur.execute("SELECT flds FROM notes")
for row in cur.fetchall():
    fields = row[0].split('\x1f')
    if len(fields) >= 9:
        img = fields[8]  # Image is field index 8
        if img.strip():
            with_image += 1
            if len(sample_images) < 10:
                sample_images.append(img)
        else:
            empty_image += 1

print(f"\nNotes with Image populated: {with_image}")
print(f"Notes with empty Image: {empty_image}")
print(f"\nSample image values:")
for img in sample_images:
    print(f"  '{img}'")

cur.close()
conn.close()
