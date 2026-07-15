import zipfile, json, sqlite3, os, sys, re

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

z = zipfile.ZipFile(r'D:\Coding\sip-blog\SIP-Housing-Basic-Reversed.apkg')
media_data = json.loads(z.read('media'))

# 1. Check if ALL filenames in notes have matching entries in media mapping
conn = sqlite3.connect(r'D:\Coding\sip-blog\_apkg_inspect\collection.anki2')
cur = conn.cursor()

cur.execute("SELECT flds FROM notes")
all_refs = set()  # all filenames referenced
for row in cur.fetchall():
    fields = row[0].split('\x1f')
    if len(fields) >= 9:
        img = fields[8].strip()
        if img:
            all_refs.add(img)
        aud = fields[7].strip() if len(fields) > 7 else ''
        if aud:
            m = re.match(r'\[sound:(.+?)\]', aud)
            if m:
                all_refs.add(m.group(1))

# Create reverse mapping: filename -> index
rev_map = {}
for k, v in media_data.items():
    rev_map[v] = int(k)

print("=== Consistency check ===")
missing_from_media = []
for ref in sorted(all_refs):
    if ref not in rev_map:
        missing_from_media.append(ref)

if missing_from_media:
    print(f"MISSING from media mapping: {missing_from_media}")
else:
    print(f"All {len(all_refs)} referenced files found in media mapping.")

# 2. Check if media mapped files actually exist in zip
zip_names = set(z.namelist())
missing_from_zip = []
for ref in sorted(all_refs):
    idx = rev_map.get(ref)
    if idx is not None and str(idx) not in zip_names:
        missing_from_zip.append(ref)

if missing_from_zip:
    print(f"MISSING from zip: {missing_from_zip}")
else:
    print(f"All referenced files found in zip.")

# 3. Verify byte content of media files matches expectations
print("\n=== File format verification ===")
errors = []
for ref in sorted(all_refs):
    idx = rev_map.get(ref)
    if idx is None:
        continue
    data = z.read(str(idx))
    if ref.endswith('.jpg'):
        if data[:2] != b'\xff\xd8':
            errors.append(f"  BAD JPG: {ref} (idx {idx}) starts with {data[:4].hex()}")
    elif ref.endswith('.mp3'):
        if data[:3] != b'ID3' and data[:2] != b'\xff\xfb' and data[:2] != b'\xff\xfa' and data[:2] != b'\xff\xf3' and data[:2] != b'\xff\xf2':
            errors.append(f"  UNUSUAL MP3: {ref} (idx {idx}) starts with {data[:4].hex()}, size={len(data)}")

if errors:
    for e in errors:
        print(e)
else:
    print("All files have correct headers for their type.")

# 4. Simulate template rendering
print("\n=== Template rendering test ===")
cur.execute("SELECT flds FROM notes LIMIT 1")
flds = cur.fetchone()[0].split('\x1f')

cur.execute("SELECT models FROM col")
models = json.loads(cur.fetchone()[0])
mid = list(models.keys())[0]
model = models[mid]

# Build field dict
field_names = [f['name'] for f in model['flds']]
fields = {}
for i, name in enumerate(field_names):
    fields[name] = flds[i] if i < len(flds) else ''

print("\nFields for first note:")
for k, v in fields.items():
    print(f"  {k} = '{v}'")

# Simple Anki template rendering for qfmt of first template
qfmt = model['tmpls'][0]['qfmt']

# First handle conditionals
def render_anki_template(tmpl, fields):
    # Handle {{#Field}}...{{/Field}} conditionals
    def replace_conditional(match):
        field = match.group(1)
        content = match.group(2)
        if fields.get(field, '').strip():
            return content
        return ''
    
    tmpl = re.sub(r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}', replace_conditional, tmpl, flags=re.DOTALL)
    
    # Handle {{^Field}}...{{/Field}} inverse conditionals
    def replace_inverse_conditional(match):
        field = match.group(1)
        content = match.group(2)
        if not fields.get(field, '').strip():
            return content
        return ''
    
    tmpl = re.sub(r'\{\{\^(\w+)\}\}(.*?)\{\{/\1\}\}', replace_inverse_conditional, tmpl, flags=re.DOTALL)
    
    # Handle {{Field}} replacements
    def replace_field(match):
        field = match.group(1)
        return fields.get(field, '')
    
    tmpl = re.sub(r'\{\{(\w+)\}\}', replace_field, tmpl)
    
    return tmpl

print("\n--- Rendered QFMT (Template 0) ---")
rendered = render_anki_template(qfmt, fields)
print(rendered)

# Also render with a note that has image but empty audio
print("\n--- Rendered AFMT (Template 0) ---")
afmt = model['tmpls'][0]['afmt']
rendered = render_anki_template(afmt, fields)
print(rendered)

cur.close()
conn.close()
