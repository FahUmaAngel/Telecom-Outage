import re

with open('telia_debug_dom.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find all input tags using regex for speed
inputs = re.findall(r'<input[^>]*>', html)
print(f'Found {len(inputs)} inputs.')

for i, inp in enumerate(inputs):
    if 'type="hidden"' in inp or 'type="submit"' in inp or 'type="radio"' in inp or 'type="checkbox"' in inp: continue
    
    # Extract attributes if they exist
    cls_match = re.search(r'class="([^"]*)"', inp)
    cls = cls_match.group(1) if cls_match else ''
    
    type_match = re.search(r'type="([^"]*)"', inp)
    typ = type_match.group(1) if type_match else ''
    
    ph_match = re.search(r'placeholder="([^"]*)"', inp)
    ph = ph_match.group(1) if ph_match else ''
    
    id_match = re.search(r'id="([^"]*)"', inp)
    id_str = id_match.group(1) if id_match else ''
    
    print(f'Input {i}: type={typ} | id={id_str} | placeholder={ph} | class={cls}')
    
print("\n--- Date text ---")
dates = re.findall(r'<[^>]*class="[^"]*date[^"]*"[^>]*>.*?<', html)
for d in dates[:20]:
    print(d)
