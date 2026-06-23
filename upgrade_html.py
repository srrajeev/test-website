#!/usr/bin/env python3
"""Fix the JS-rendered HTML: add gold theme CSS for JS classes + loremflickr photos to each timeline item."""

import re, json

with open('index.html', 'r') as f:
    html = f.read()

# ===== ADD CSS FOR JS-RENDERED CLASSES =====
js_css = """
.day-view{padding:0;animation:fadeIn .4s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.tl-title{font-size:.85rem;color:var(--head);font-weight:600;margin:4px 0}
.tl-detail{font-size:.73rem;color:var(--text);margin-top:3px;line-height:1.5}
.tl-detail a{color:var(--accent);font-weight:600;text-decoration:none}
.tl-img{width:100%;max-width:320px;height:auto;border-radius:10px;margin-top:8px;border:1px solid var(--border);object-fit:cover;transition:.3s}
.tl-img:hover{transform:scale(1.02)}
.city-card{cursor:pointer;border-radius:var(--radius,14px);overflow:hidden;background:var(--card);border:1px solid var(--border);transition:.3s;box-shadow:var(--card-shadow)}
.city-card:hover{transform:translateY(-3px);border-color:rgba(201,168,76,0.3);box-shadow:0 8px 30px rgba(0,0,0,0.4)}
.city-img{height:120px;background-size:cover!important;background-position:center!important;position:relative}
.city-img .overlay{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.8),transparent 70%);display:flex;flex-direction:column;justify-content:flex-end;padding:16px;color:#fff}
.city-img .overlay h2{font-size:1.1rem;margin:0;color:#fff}
.city-img .overlay span{font-size:.75rem;opacity:.85}
.city-body{padding:12px 16px}
.quick{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px}
.quick span{padding:2px 8px;border-radius:4px;font-size:.68rem;background:rgba(201,168,76,0.08);color:var(--accent);border:1px solid rgba(201,168,76,0.12)}
.warn{font-size:.7rem;color:var(--orange);margin-top:6px;font-weight:500}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:14px 0}
.stat-card{text-align:center;padding:12px 6px;background:var(--card);border-radius:var(--radius,14px);border:1px solid var(--border);box-shadow:var(--card-shadow)}
.stat-card .num{font-size:1.3rem;font-weight:800;color:var(--head)}
.stat-card .lbl{font-size:.68rem;color:var(--text);margin-top:2px;text-transform:uppercase}
.nav{display:flex;gap:4px;flex-wrap:wrap;margin:16px 0;position:sticky;top:8px;z-index:100;padding:5px;background:rgba(8,12,18,0.9);backdrop-filter:blur(12px);border-radius:12px;border:1px solid var(--border)}
.nav button{padding:7px 12px;border-radius:8px;border:1px solid transparent;background:transparent;color:var(--text);cursor:pointer;font-size:.8rem;transition:.2s;font-weight:500}
.nav button:hover{background:rgba(255,255,255,0.03)}
.nav button.active{background:rgba(201,168,76,0.1);border-color:rgba(201,168,76,0.25);color:var(--accent2)}
.nav input{flex:1;min-width:140px;padding:7px 14px;border-radius:8px;border:1px solid var(--border);background:rgba(15,20,30,0.6);color:var(--text);font-size:.8rem}
.nav input:focus{outline:none;border-color:var(--accent)}
.header{text-align:center;padding:55px 24px 40px;margin-bottom:20px;position:relative;border-bottom:2px solid rgba(201,168,76,0.15);border-radius:0 0 28px 28px;margin:0 -16px 24px;background:linear-gradient(160deg,#0a0f17,#141e2a,#0d1119,#1a1015)}
.header::before{content:'';position:absolute;inset:0;background:url('https://images.unsplash.com/photo-1528127269322-539801943592?w=1200&q=70') center/cover;opacity:0.12;filter:saturate(0.8)}
.header::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;background:var(--gold-grad);opacity:0.5}
.header h1{font-size:clamp(1.8rem,5vw,2.6rem);color:#fff;position:relative;font-weight:800;letter-spacing:-0.5px;text-shadow:0 2px 20px rgba(201,168,76,0.2)}
.header .sub{color:var(--accent2);position:relative;margin-top:6px;font-size:1rem;font-weight:500}
.toggle{position:fixed;top:12px;right:16px;z-index:200;width:38px;height:38px;border-radius:50%;border:1px solid var(--border);background:rgba(15,20,30,0.9);color:var(--text);font-size:1rem;cursor:pointer;backdrop-filter:blur(12px)}
.util-btn{position:fixed;bottom:20px;right:20px;z-index:200;width:42px;height:42px;border-radius:50%;border:1px solid var(--border);background:rgba(15,20,30,0.9);color:var(--text);font-size:1.1rem;cursor:pointer;transition:.2s;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(12px)}
.util-btn:hover{background:rgba(201,168,76,0.15);border-color:var(--accent);transform:scale(1.05)}
.panel{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(12,20,32,0.98);border:1px solid var(--border);border-radius:16px;padding:24px;z-index:300;max-width:400px;width:90%;max-height:70vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.panel.open{display:block}
"""

# Insert JS CSS before </style>
html = html.replace('</style>', js_css + '\n</style>', 1)

# ===== ADD LOREMFLICKR IMAGES TO DATA ITEMS =====
def get_img_keywords(name, detail=''):
    """Generate loremflickr keywords from item name + detail."""
    nl = (name + ' ' + detail).lower()
    matches = {
        'fansipan': 'fansipan,mountain,cablecar,vietnam,summit',
        'cat cat': 'sapa,catcat,village,hmong,waterfall',
        'rong may': 'sapa,glassbridge,suspension,mountain,sky',
        'glass bridge': 'sapa,glassbridge,mountain,skywalk',
        'phansi': 'cafe,sapa,mountain,bbq,ship',
        'viettrekking': 'sapa,coffee,mountain,cloud,breakfast',
        'la do': 'sapa,train,railway,cafe,homestay',
        'white cloud': 'cafe,sapa,mountain,eggcoffee,vietnam',
        'best view': 'sapa,sunset,mountain,panorama',
        'o la la': 'cafe,sapa,coffee,vietnamese,hidden',
        'moana sapa': 'sapa,moana,heaven,gate,photo',
        'sapa night market': 'sapa,nightmarket,hmong,handicraft',
        'buivien': 'buivien,saigon,nightlife,walkingstreet',
        'bui vien': 'buivien,saigon,nightlife,walkingstreet,beer',
        'pho minh': 'vietnamese,pho,restaurant,saigon,noodle',
        'pho le': 'pho,vietnamese,soup,saigon,food',
        'phở thìn': 'hanoi,pho,vietnamese,streetfood,garlic',
        'banh canh': 'crab,noodle,soup,vietnamese,saigon',
        'banh mi': 'banhmi,vietnamese,sandwich,hanoi',
        'vinh khanh': 'saigon,streetfood,seafood,oyster',
        'noong oi': 'cafe,garden,saigon,vietnam,rustic',
        'van gogh': 'vangogh,immersive,art,exhibition,digital',
        'bus tour': 'saigon,bustour,city,sightseeing,double-decker',
        'grand world': 'phuquoc,grandworld,nightlife,vietnam',
        'island tour': 'phuquoc,snorkeling,island,speedboat,beach',
        'sunset town': 'phuquoc,sunset,mediterranean,bridge',
        'duong dong': 'phuquoc,nightmarket,seafood,vietnam',
        'vinwonders': 'phuquoc,themepark,amusement,vietnam',
        'the once show': 'phuquoc,show,performance,spectacle',
        'ham ninh': 'phuquoc,fishing,village,authentic',
        'hoan kiem': 'hanoi,hoankiem,lake,sunrise,peaceful',
        'temple of literature': 'hanoi,temple,literature,confucius',
        'bia hoi': 'hanoi,beer,street,corner,vietnamese',
        'giang cafe': 'hanoi,eggcoffee,cafe,vintage',
        'bun cha': 'hanoi,buncha,obama,vietnamese,grilled',
        'chả cá': 'hanoi,fish,vietnamese,grilled,restaurant',
        'x space': 'hanoi,digital,art,immersive,museum',
        'train street': 'hanoi,train,street,railway,photography',
        'halong bay': 'halongbay,cruise,limestone,karst,sung-sot',
        'sapa bus': 'vietnam,mountain,road,sleeper,bus,scenic',
    }
    for key, kw in matches.items():
        if key in nl:
            return kw
    # Fallback
    cleaned = re.sub(r'[^\w\s-]', '', name).strip().lower().replace(' ','-')[:40]
    return f'vietnam,{cleaned}'

# Modifying the DATA object: add img field to each item
# The DATA is defined as: {t:"time",h:"header",d:"detail"}
# We need to add: ,img:"url" to each item

data_match = re.search(r'const DATA = (\{.*?\n\});', html, re.DOTALL)
if data_match:
    data_str = data_match.group(1)
    # Parse city names
    cities = re.findall(r'(\w+):\s*\{', data_str)
    print(f"Found cities: {cities}")
    
    # For each item {t:"...",h:"...",d:"..."}, add img field
    def add_img_to_item(match):
        full = match.group(0)
        # Extract the h (header) field
        h_match = re.search(r'h:"(.+?)"', full)
        d_match = re.search(r'd:"(.+?)"', full)
        header = h_match.group(1) if h_match else ''
        detail = d_match.group(1) if d_match else ''
        keywords = get_img_keywords(header, detail)
        url = f'https://loremflickr.com/400/300/{keywords}'
        # Add img field before closing brace
        return full[:-1] + f',img:"{url}"' + '}'
    
    # Find all {t:...} items in the data
    new_data_str = re.sub(r'\{t:"[^"]*",h:"[^"]*"(?:,d:"(?:[^"\\]|\\.)*")?\}', add_img_to_item, data_str)
    
    # Count added imgs
    old_count = data_str.count('"t":')
    new_count = new_data_str.count('"img":')
    print(f"Added {new_count} images to {old_count} items")
    
    html = html.replace(data_str, new_data_str)
else:
    print("ERROR: Could not find DATA object")

# ===== UPDATE RENDER FUNCTION TO INCLUDE IMAGES =====
# Find: ${item.d?`<div class="tl-detail">${item.d}</div>`:''}
# Add after: ${item.img?`<img src="${item.img}" class="tl-img" loading="lazy" alt="">`:''}

old_render = r"""${item.d?`<div class="tl-detail">${item.d}</div>`:''}"""
new_render = r"""${item.d?`<div class="tl-detail">${item.d}</div>`:''}${item.img?`<img src="${item.img}" class="tl-img" loading="lazy" alt="">`:''}"""

html = html.replace(old_render, new_render)
print("Render function updated!" if old_render in html or new_render in html else "Render update check done")

# ===== Make body use container class =====
# Update the theme toggle to work with dark-only mode

with open('index.html', 'w') as f:
    f.write(html)

print(f'Done! HTML: {len(html)} bytes')

# Verify
imgs = html.count('loremflickr.com')
print(f'LoremFlickr IMGs: {imgs}')
