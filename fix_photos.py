#!/usr/bin/env python3
"""Switch all Unsplash URLs to LoremFlickr (Unsplash Source API is down - 503)."""

with open('index.html', 'r') as f:
    html = f.read()

# Replace all source.unsplash.com URLs with loremflickr.com equivalents
# Format: https://source.unsplash.com/400x300/?k1,k2,k3 → https://loremflickr.com/400/300/k1,k2,k3
import re

count = 0
def replace_url(match):
    global count
    full = match.group(0)
    # Extract keywords from the URL
    m = re.search(r'400x300/\?(.+)$', full)
    if m:
        keywords = m.group(1)
        count += 1
        return f'https://loremflickr.com/400/300/{keywords}'
    # Fallback: try 400x300 format
    m2 = re.search(r'400x300/\?', full)
    if m2:
        count += 1
        return full.replace('source.unsplash.com/400x300/?', 'loremflickr.com/400/300/')
    return full

html = re.sub(r'https://source\.unsplash\.com/400x300/\?[^"\']+', replace_url, html)

# Also update the hero background image
html = html.replace('images.unsplash.com', 'images.unsplash.com')  # Keep hero bg

print(f'Replaced {count} Unsplash URLs → LoremFlickr')
print(f'HTML size: {len(html)} bytes')

with open('index.html', 'w') as f:
    f.write(html)

print('Done!')
