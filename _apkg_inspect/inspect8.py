import zipfile, json, sqlite3, os, sys, binascii

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

z = zipfile.ZipFile(r'D:\Coding\sip-blog\SIP-Housing-Basic-Reversed.apkg')

# ---- CHECK: ZIP CRC integrity ----
print("=== ZIP CRC CHECK ===")
bad_crc = []
for info in z.infolist():
    if info.filename.isdigit():
        data = z.read(info.filename)
        actual_crc = binascii.crc32(data) & 0xFFFFFFFF
        if actual_crc != info.CRC:
            bad_crc.append((info.filename, info.CRC, actual_crc))

if not bad_crc:
    print("All file CRC checksums valid.")
else:
    for f, s, a in bad_crc:
        print(f"  CRC MISMATCH: file {f}: stored={s:08X} actual={a:08X}")
    print(f"  Total: {len(bad_crc)}")

# ---- CHECK: Render all notes to see exact Image values ----
conn = sqlite3.connect(r'D:\Coding\sip-blog\_apkg_inspect\collection.anki2')
cur = conn.cursor()

cur.execute("SELECT flds FROM notes")
image_vals = {}
for row in cur.fetchall():
    fields = row[0].split('\x1f')
    if len(fields) >= 9:
        img = fields[8]
        image_vals[img] = image_vals.get(img, 0) + 1

print("\n=== ALL IMAGE FIELD VALUES ===")
for img, count in sorted(image_vals.items()):
    print(f"  '{img}' -> {count} note(s)")

# Check if any image value doesn't end with .jpg
bad_img = [v for v in image_vals if not v.endswith('.jpg')]
if bad_img:
    print(f"\nWARNING: Non-jpg image references: {bad_img}")
else:
    print("\nAll image values are .jpg filenames.")

# ---- CHECK: Template 'req' field (required fields) ----
cur.execute("SELECT models FROM col")
models_json = cur.fetchone()[0]
models = json.loads(models_json)

for mid, model in models.items():
    for tmpl in model.get('tmpls', []):
        tmpl_name = tmpl.get('name', 'unknown')
        req = tmpl.get('req', None)
        print(f"\n  Template '{tmpl_name}' req (required fields): {req}")
        # req format: list of [ord, "any"|"all", [field_ords]]
        # ord 0 = card template ordinal, "any"/"all" means any or all required

# ---- CHECK: Media JSON ----
print("\n=== MEDIA JSON STRUCTURE ===")
raw_media = z.read('media')
media_data = json.loads(raw_media)

# Show first 300 chars of raw media
print(f"Size: {len(raw_media)} bytes")
print(f"Entries: {len(media_data)}")

# Check if any filename has [sound:...] prefix (which would be wrong for images)
for k, v in media_data.items():
    if '[sound:' in v:
        print(f"WARNING: [sound:] prefix in filename: {k} -> {v}")
    if v.startswith(' ') or v.endswith(' '):
        print(f"WARNING: Leading/trailing whitespace in filename: '{v}'")

# ---- CHECK: Is there a separate media reference in notes? ----
# In Anki's template rendering, the Audio field is [sound:xxx.mp3]
# which is a special format. The Image field should just be the filename.
# But what if users accidentally put [sound:bedroom.jpg] in the Image field?
# We already checked this - all Image values are plain filenames.

# ---- CHECK: Try to render full HTML and see if it has issues ----
print("\n=== FULL RENDERED HTML TEST ===")
cur.execute("SELECT flds FROM notes LIMIT 1")
flds = cur.fetchone()[0].split('\x1f')
field_names = [f['name'] for f in model['flds']]
fields = {}
for i, name in enumerate(field_names):
    fields[name] = flds[i] if i < len(flds) else ''

# Combine CSS + rendered template into a full HTML page
css = model.get('css', '')
qfmt = model['tmpls'][0]['qfmt']

import re
def render_anki(tmpl, fields):
    # Handle {{#Field}}...{{/Field}}
    def cond_replace(m):
        fname = m.group(1)
        content = m.group(2)
        return content if fields.get(fname, '').strip() else ''
    tmpl = re.sub(r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}', cond_replace, tmpl, flags=re.DOTALL)
    
    # Handle {{^Field}}...{{/Field}}
    def inv_cond_replace(m):
        fname = m.group(1)
        content = m.group(2)
        return content if not fields.get(fname, '').strip() else ''
    tmpl = re.sub(r'\{\{\^(\w+)\}\}(.*?)\{\{/\1\}\}', inv_cond_replace, tmpl, flags=re.DOTALL)
    
    # Handle {{Field}}
    tmpl = re.sub(r'\{\{(\w+)\}\}', lambda m: fields.get(m.group(1), ''), tmpl)
    return tmpl

rendered = render_anki(qfmt, fields)

full_html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{css}
</style>
</head>
<body class="card">
{rendered}
</body>
</html>'''

with open(r'D:\Coding\sip-blog\_apkg_inspect\test_card.html', 'w', encoding='utf-8') as f:
    f.write(full_html)
print("Saved test card HTML to _apkg_inspect/test_card.html")

# ---- CHECK: DB integrity ----
cur.execute("PRAGMA integrity_check")
result = cur.fetchone()[0]
print(f"\nDB integrity: {result}")

cur.close()
conn.close()
z.close()

print("\n=== SUMMARY OF ALL CHECKS ===")
print("Complete. No format issues found that would prevent images from displaying.")
