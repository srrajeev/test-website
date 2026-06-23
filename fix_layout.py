#!/usr/bin/env python3
"""Fix: deduplicate images + improve layout"""

import re
from collections import Counter

with open('index.html', 'r') as f:
    html = f.read()

# === FIX 1: Make all image URLs unique ===
imgs = re.findall(r'(img:")(https://loremflickr\.com/400/300/)([^"]+)(")', html)
seen_urls = Counter()
replacements = []

for prefix, base, keywords, suffix in imgs:
    url = base + keywords
    seen_urls[url] += 1
    count = seen_urls[url]
    
    if count > 1:
        # Make unique by appending a differentiator
        new_keywords = f'{keywords},spot{count}'
        old = f'{prefix}{base}{keywords}{suffix}'
        new = f'{prefix}{base}{new_keywords}{suffix}'
        replacements.append((old, new))
        print(f'  Dedupe: {keywords[:60]}... → spot{count}')

for old, new in replacements:
    html = html.replace(old, new, 1)  # Replace only the Nth occurrence

print(f'Deduped {len(replacements)} images')

# === FIX 2: Layout improvements ===
# Make day cards look better with proper spacing
layout_fixes = """
.city-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin:16px 0}
.nav input{flex:1;min-width:140px;padding:8px 14px;border-radius:8px;border:1px solid var(--border);background:rgba(15,20,30,0.6);color:var(--text);font-size:.8rem}
.header{padding:40px 24px 35px;text-align:center}
"""

# Find existing .city-grid and replace
if '.city-grid' in html:
    html = re.sub(r'\.city-grid\{[^}]*\}', '.city-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin:16px 0}', html)
    print('Layout: city-grid updated')
else:
    # Add it before </style>
    html = html.replace('</style>', layout_fixes + '\n</style>', 1)
    print('Layout: added missing styles')

# Fix: ensure day cards have gap between items
# The render function creates <div style="...margin-bottom:16px..."> — add border-bottom
old_render_card = 'margin-bottom:16px;box-shadow:var(--shadow);border-left:4px solid var(--accent)"'
new_render_card = 'margin-bottom:18px;box-shadow:var(--card-shadow);border-left:4px solid var(--accent);border-bottom:1px solid var(--border)"'
html = html.replace(old_render_card, new_render_card)
print('Layout: card shadows updated')

# === FIX 3: Add proper spacing for timeline items within cards ===
old_tl_item = '.tl-item{'
new_tl_item = '.tl-item{display:flex;gap:8px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.03);align-items:flex-start;'
if old_tl_item not in html:
    html = html.replace('</style>', new_tl_item + '\n}\n</style>', 1)
    print('Layout: tl-item styling added')

with open('index.html', 'w') as f:
    f.write(html)

print(f'Done! Final size: {len(html)} bytes')

# Verify
imgs_after = re.findall(r'img:"https://loremflickr[^"]+"', html)
unique_after = len(set(imgs_after))
print(f'Images: {len(imgs_after)} total, {unique_after} unique')
