#!/usr/bin/env python3
"""Replace all loremflickr URLs with picsum.photos using unique seeds per location"""

import re
from collections import OrderedDict

with open('index.html', 'r') as f:
    html = f.read()

# Find all IMG URLs and their context (item header)
imgs = re.findall(r'(img:")(https://loremflickr\.com/400/300/[^"]+)(")', html)

# Collect all unique URLs and assign a simple counter
seen = {}
counter = 1
replacements = []

for prefix, url, suffix in imgs:
    if url not in seen:
        seen[url] = counter
        counter += 1
    
    idx = seen[url]
    # Generate unique seed from URL keywords
    keywords = url.replace('https://loremflickr.com/400/300/', '')
    # Use the first meaningful keyword as seed base, add index for uniqueness
    seed_base = keywords.split(',')[0] if ',' in keywords else keywords
    seed = f'{seed_base}{idx}'
    
    new_url = f'https://picsum.photos/seed/{seed}/400/300'
    
    old = f'{prefix}{url}{suffix}'
    new = f'{prefix}{new_url}{suffix}'
    if old != new:
        replacements.append((old, new))

# Apply replacements
for old, new in replacements:
    html = html.replace(old, new, 1)

print(f'Replaced {len(replacements)} URLs → Picsum')
print(f'Unique seeds used: {len(seen)}')

# Also update city card backgrounds
bg_replacements = [
    ('loremflickr.com/600/300/sapa,rice,terrace,mountain,vietnam', 'picsum.photos/seed/sapa-terrace/600/300'),
    ('loremflickr.com/600/300/saigon,skyline,vietnam,city', 'picsum.photos/seed/saigon-skyline/600/300'),
    ('loremflickr.com/600/300/phuquoc,beach,island,paradise', 'picsum.photos/seed/phuquoc-beach/600/300'),
    ('loremflickr.com/600/300/hanoi,oldquarter,lake,vietnam', 'picsum.photos/seed/hanoi-quarter/600/300'),
]
for old, new in bg_replacements:
    html = html.replace(old, new)

print('City backgrounds updated')

with open('index.html', 'w') as f:
    f.write(html)

# Verify
picsum_count = html.count('picsum.photos')
print(f'Picsum URLs: {picsum_count}')
print('Done!')
