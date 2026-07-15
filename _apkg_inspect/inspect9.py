import zipfile, json, struct, sys, hashlib

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

z = zipfile.ZipFile(r'D:\Coding\sip-blog\SIP-Housing-Basic-Reversed.apkg')
media_data = json.loads(z.read('media'))

# Build hash map for JPGs
img_hashes = {}  # hash -> [(idx, fname, size)]
for k, v in media_data.items():
    if v.endswith('.jpg'):
        data = z.read(k)
        h = hashlib.md5(data).hexdigest()
        if h not in img_hashes:
            img_hashes[h] = []
        img_hashes[h].append((k, v, len(data)))

print(f"Unique JPG hashes: {len(img_hashes)}")
for h, entries in img_hashes.items():
    print(f"  Hash {h[:16]}...: {len(entries)} files")
    for idx, fname, sz in entries[:3]:
        print(f"    - {fname} ({sz} bytes)")
    if len(entries) > 3:
        print(f"    ... and {len(entries)-3} more")

# Analyze each unique image
print("\n=== DETAILED JPEG ANALYSIS ===")
for h, entries in img_hashes.items():
    idx, fname, sz = entries[0]
    data = z.read(idx)
    
    print(f"\n--- {fname} ({sz} bytes, {len(entries)} copies) ---")
    
    # Parse JPEG structure
    pos = 2
    markers = []
    sof0_info = None
    sos_start = None
    eoi_pos = data.find(b'\xff\xd9')
    
    while pos < len(data) - 1:
        if data[pos] != 0xFF:
            break
        marker = data[pos+1]
        marker_name = f'0xFF{marker:02X}'
        
        if marker == 0xD8:
            markers.append((marker_name, 2, 'SOI'))
            pos += 2
        elif marker == 0xD9:
            markers.append((marker_name, 2, 'EOI'))
            break
        elif marker == 0xDA:
            # SOS - rest is compressed data
            length = struct.unpack('>H', data[pos+2:pos+4])[0]
            markers.append((marker_name, length + 2, 'SOS'))
            sos_start = pos + 2 + length
            pos = eoi_pos if eoi_pos > 0 else len(data)
            break
        elif marker in (0xC0, 0xC1, 0xC2):
            length = struct.unpack('>H', data[pos+2:pos+4])[0]
            h_val = struct.unpack('>H', data[pos+5:pos+7])[0]
            w_val = struct.unpack('>H', data[pos+7:pos+9])[0]
            comp_count = data[pos+9]
            sof0_info = (w_val, h_val, comp_count)
            markers.append((marker_name, length + 2, f'SOFn ({w_val}x{h_val}, {comp_count} comp)'))
            pos += 2 + length
        else:
            if pos + 3 < len(data):
                length = struct.unpack('>H', data[pos+2:pos+4])[0]
                markers.append((marker_name, length + 2, ''))
                pos += 2 + length
            else:
                break
    
    print(f"  Dimensions: {sof0_info}")
    print(f"  SOS at offset: {sos_start}")
    print(f"  EOI at offset: {eoi_pos}")
    
    if sos_start and eoi_pos:
        scan_size = eoi_pos - sos_start
        # Analyze scan data entropy
        scan_data = data[sos_start:eoi_pos]
        
        # Count unique byte values
        unique_bytes = len(set(scan_data))
        total_scan = len(scan_data)
        
        # Count zero bytes
        zero_count = scan_data.count(0)
        
        # Count runs of identical bytes
        runs = 0
        prev = None
        for b in scan_data:
            if b == prev:
                runs += 1
            prev = b
        
        print(f"  Scan data: {total_scan} bytes, {unique_bytes} unique values")
        print(f"  Zero bytes: {zero_count} ({zero_count/total_scan*100:.1f}%)")
        print(f"  Same-byte runs: {runs} ({runs/total_scan*100:.1f}%)")
        
        if unique_bytes <= 5:
            print(f"  >> IMAGE APPEARS TO BE EXTREMELY FLAT/SIMPLE (near-single color)")
        elif unique_bytes <= 20:
            print(f"  >> IMAGE IS VERY SIMPLE (few distinct patterns)")
        elif unique_bytes <= 100:
            print(f"  >> IMAGE IS SOMEWHAT SIMPLE")
        else:
            print(f"  >> IMAGE HAS REASONABLE COMPLEXITY")

z.close()
