import zipfile, json, sqlite3, os, sys

# Fix stdout encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

z = zipfile.ZipFile(r'D:\Coding\sip-blog\SIP-Housing-Basic-Reversed.apkg')

media_data = json.loads(z.read('media'))

tmpdir = r'D:\Coding\sip-blog\_apkg_inspect'
os.makedirs(tmpdir, exist_ok=True)
with open(os.path.join(tmpdir, 'collection.anki2'), 'wb') as f:
    f.write(z.read('collection.anki2'))

conn = sqlite3.connect(os.path.join(tmpdir, 'collection.anki2'))
cur = conn.cursor()

# Get the collection config
cur.execute("SELECT models FROM col")
row = cur.fetchone()
models = json.loads(row[0])

for mid, model in models.items():
    print("=" * 60)
    print(f"Model ID: {mid}")
    name = model['name'].encode('ascii', errors='replace').decode('ascii')
    print(f"Name: {name}")
    print(f"Fields: {[(f['ord'], f['name']) for f in model['flds']]}")

    css = model.get('css', '')
    print("\n--- CSS ---")
    print(css)

    print("\n--- Templates ---")
    for i, tmpl in enumerate(model['tmpls']):
        print(f"\n  Template {i}: {tmpl['name']}")
        print(f"  QFMT:")
        print(tmpl['qfmt'])
        print(f"  AFMT:")
        print(tmpl['afmt'])

cur.close()
conn.close()
