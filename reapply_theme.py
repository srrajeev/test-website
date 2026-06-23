#!/usr/bin/env python3
"""Apply gold premium dark theme + loremflickr photos to the current HTML (keeping cron's content improvements)."""

import re

with open('index.html', 'r') as f:
    html = f.read()

# === 1. Replace CSS with the dark premium gold theme ===
new_css = """:root{
  --bg:#060b0f;--card:rgba(15,20,30,0.92);--border:rgba(255,255,255,0.07);
  --text:#a8b4c0;--head:#eef2f8;--accent:#c9a84c;--accent2:#e8c96a;
  --green:#4ade80;--orange:#f59e4b;--red:#f87171;--rain:#67c8e8;
  --gold-grad:linear-gradient(135deg,#c9a84c,#e8c96a,#c9a84c);
  --red-grad:linear-gradient(135deg,#c0392b,#e74c3c);
  --card-shadow:0 4px 24px rgba(0,0,0,0.3),0 1px 4px rgba(0,0,0,0.2);
}
*{margin:0;padding:0;box-sizing:border-box}
body{
  font-family:'Inter','Segoe UI',system-ui,sans-serif;
  background:var(--bg);
  background-image:radial-gradient(ellipse at 15% 0%,rgba(201,168,76,0.05) 0%,transparent 55%),radial-gradient(ellipse at 85% 100%,rgba(196,49,43,0.03) 0%,transparent 55%);
  color:var(--text);line-height:1.6;min-height:100vh;
}
.container{max-width:1100px;margin:0 auto;padding:0 16px 60px}

.hero{
  position:relative;border-radius:0 0 28px 28px;overflow:hidden;
  margin:0 -16px 24px;padding:55px 24px 40px;text-align:center;
  background:linear-gradient(160deg,#0a0f17 0%,#141e2a 35%,#0d1119 70%,#1a1015 100%);
  border-bottom:2px solid rgba(201,168,76,0.15);
}
.hero::before{content:'';position:absolute;inset:0;background:url('https://images.unsplash.com/photo-1528127269322-539801943592?w=1200&q=70') center/cover;opacity:0.14;filter:saturate(0.8)}
.hero::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;background:var(--gold-grad);opacity:0.5}
.hero h1{font-size:clamp(1.8rem,5vw,2.6rem);color:#fff;position:relative;font-weight:800;letter-spacing:-0.5px;text-shadow:0 2px 20px rgba(201,168,76,0.2)}
.hero .sub{color:var(--accent2);font-size:1rem;position:relative;margin-top:6px;font-weight:500}
.hero .meta{color:var(--text);font-size:.8rem;position:relative;margin-top:4px;opacity:.6}
.countdown{display:inline-block;margin-top:16px;padding:10px 26px;background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.2);border-radius:30px;color:var(--accent2);font-size:.9rem;position:relative;font-weight:500}

.overview-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:18px 0}
.ov-card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px 12px;text-align:center;cursor:pointer;transition:.3s;position:relative;overflow:hidden;backdrop-filter:blur(12px);box-shadow:0 2px 12px rgba(0,0,0,0.2)}
.ov-card:hover{transform:translateY(-4px);border-color:rgba(201,168,76,0.3);box-shadow:0 8px 30px rgba(0,0,0,0.4)}
.ov-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.ov-card:nth-child(1)::before{background:var(--red-grad)}
.ov-card:nth-child(2)::before{background:linear-gradient(90deg,#48c9b0,#5dade2)}
.ov-card:nth-child(3)::before{background:var(--gold-grad)}
.ov-card:nth-child(4)::before{background:linear-gradient(90deg,#22c55e,#4ade80)}
.ov-card:nth-child(5)::before{background:linear-gradient(90deg,#c9a84c,#e8715b)}
.ov-emoji{font-size:2rem;margin-bottom:4px}
.ov-city{font-size:.85rem;font-weight:700;color:var(--head)}
.ov-dates{font-size:.68rem;color:var(--accent);margin:2px 0;text-transform:uppercase;letter-spacing:.5px}
.ov-warn{font-size:.62rem;color:var(--orange);margin-top:4px;font-weight:500}
.ov-card.active-overview{border-color:var(--accent);box-shadow:0 0 24px rgba(201,168,76,0.2)}

.tabs{display:flex;gap:4px;flex-wrap:wrap;margin:16px 0;position:sticky;top:8px;z-index:100;padding:5px;background:rgba(8,12,18,0.9);backdrop-filter:blur(12px);border-radius:12px;border:1px solid var(--border)}
.tab{padding:7px 12px;border-radius:8px;border:1px solid transparent;background:transparent;color:var(--text);cursor:pointer;font-size:.8rem;transition:.2s;white-space:nowrap;font-weight:500}
.tab:hover{background:rgba(255,255,255,0.03)}
.tab.active{background:rgba(201,168,76,0.1);border-color:rgba(201,168,76,0.25);color:var(--accent2)}
.search-bar{width:100%;padding:12px 18px;border-radius:12px;border:1px solid var(--border);background:rgba(15,20,30,0.6);color:var(--text);font-size:.9rem;margin-bottom:14px;backdrop-filter:blur(8px);transition:.2s}
.search-bar:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(201,168,76,0.1)}

.day-grid{display:grid;gap:14px}
.day-card{background:var(--card);border:1px solid var(--border);border-radius:14px;overflow:hidden;transition:.3s;backdrop-filter:blur(12px);box-shadow:0 2px 12px rgba(0,0,0,0.2)}
.day-card:hover{border-color:rgba(201,168,76,0.2);box-shadow:0 6px 28px rgba(0,0,0,0.35)}
.day-header{padding:14px 18px;display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--border);flex-wrap:wrap;background:rgba(0,0,0,0.15)}
.day-photo{width:90px;height:60px;border-radius:10px;object-fit:cover;border:1px solid var(--border);flex-shrink:0;transition:.3s}
.day-photo:hover{transform:scale(1.08)}
.day-num{font-size:1.8rem;min-width:44px;text-align:center}
.day-info{flex:1;min-width:140px}
.day-city{font-size:1rem;font-weight:700;color:var(--head)}
.day-label{font-size:.78rem;color:#8899aa;margin-top:1px}
.wx-badge{display:flex;align-items:center;gap:5px;padding:6px 14px;border-radius:20px;font-size:.75rem;font-weight:600;white-space:nowrap}
.wx-low{background:rgba(74,222,128,0.1);color:var(--green);border:1px solid rgba(74,222,128,0.2)}
.wx-med{background:rgba(245,158,75,0.1);color:var(--orange);border:1px solid rgba(245,158,75,0.2)}
.wx-high{background:rgba(240,130,100,0.1);color:#f08264;border:1px solid rgba(240,130,100,0.2)}
.wx-crit{background:rgba(248,113,113,0.12);color:var(--red);border:1px solid rgba(248,113,113,0.25);animation:pulse 2.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.65}}

.wx-detail{padding:10px 18px;background:rgba(0,0,0,0.15);font-size:.78rem;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.wx-detail .tip{flex:1;min-width:180px}.wx-detail .tip::before{content:'💡 '}
.rain-chance{color:var(--rain);font-weight:600;white-space:nowrap}

.timeline{padding:4px 18px 12px}
.tl-item{display:flex;gap:10px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.025);align-items:flex-start}
.tl-item:last-child{border-bottom:none}
.tl-time{min-width:66px;font-size:.73rem;color:var(--accent);font-weight:600;padding-top:2px;opacity:.85}
.tl-body{flex:1}
.tl-name{font-size:.85rem;color:var(--head);font-weight:500}
.tl-price{font-size:.73rem;color:var(--accent2);margin-top:1px}
.tl-quote{font-size:.72rem;color:#8899aa;margin-top:2px;font-style:italic;padding:4px 10px;border-left:2px solid rgba(201,168,76,0.35);background:rgba(201,168,76,0.03);border-radius:0 6px 6px 0}
.tl-tips{font-size:.72rem;color:#8899aa;margin-top:3px}
.tl-tips::before{content:'💡 '}
.tl-order{font-size:.72rem;color:var(--green);margin-top:2px}
.tl-order::before{content:'✅ ORDER: '}
.tl-skip{font-size:.72rem;color:var(--red);margin-top:1px}
.tl-skip::before{content:'🚫 SKIP: '}
.tl-maps{display:inline-block;font-size:.7rem;color:var(--accent);text-decoration:none;margin-top:3px;padding:3px 9px;border-radius:5px;background:rgba(201,168,76,0.07);border:1px solid rgba(201,168,76,0.12);transition:.2s}
.tl-maps:hover{background:rgba(201,168,76,0.16)}
.tl-maps::before{content:'🗺️ '}
.tl-photo{width:100%;max-width:300px;height:auto;border-radius:10px;margin-top:6px;border:1px solid var(--border);object-fit:cover;transition:.3s}
.tl-photo:hover{transform:scale(1.02)}

.utils{position:fixed;bottom:20px;right:20px;z-index:200;display:flex;flex-direction:column;gap:8px}
.util-btn{width:42px;height:42px;border-radius:50%;border:1px solid var(--border);background:rgba(15,20,30,0.9);color:var(--text);font-size:1.1rem;cursor:pointer;transition:.2s;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(12px)}
.util-btn:hover{background:rgba(201,168,76,0.15);border-color:var(--accent);transform:scale(1.05)}
.panel{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(12,20,32,0.98);border:1px solid var(--border);border-radius:16px;padding:24px;z-index:300;max-width:460px;width:92%;max-height:70vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.5);backdrop-filter:blur(16px)}
.panel.show{display:block}
.panel h3{color:var(--head);margin-bottom:12px;font-size:1.05rem}
.panel label{display:flex;align-items:center;gap:8px;padding:6px 0;font-size:.82rem;cursor:pointer}
.panel input[type=checkbox]{width:16px;height:16px;accent-color:var(--accent)}
.panel-close{float:right;background:none;border:none;color:var(--text);font-size:1.3rem;cursor:pointer;opacity:.6}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:250;backdrop-filter:blur(2px)}
.overlay.show{display:block}
.btable{width:100%;font-size:.8rem;border-collapse:collapse}
.btable td,.btable th{padding:6px 10px;border-bottom:1px solid var(--border);text-align:left}
.btable th{color:var(--accent);font-size:.7rem;text-transform:uppercase}
.btable .total{color:var(--green);font-weight:700}
.em-item{padding:8px 0;border-bottom:1px solid var(--border);font-size:.8rem}
.em-item strong{color:var(--head)}

@media(max-width:640px){
  .hero{padding:35px 14px 24px}
  .overview-grid{grid-template-columns:repeat(2,1fr);gap:7px}
  .day-header{flex-direction:column;align-items:flex-start}
  .tl-time{min-width:52px;font-size:.68rem}
}
html{scroll-behavior:smooth}"""

# Find and replace the <style> block
old_style = re.search(r'<style>.*?</style>', html, re.DOTALL)
if old_style:
    html = html[:old_style.start()] + '<style>\n' + new_css + '\n</style>' + html[old_style.end():]
    print("CSS replaced!")
else:
    print("ERROR: Could not find <style> block")
    exit(1)

# === 2. Remove old Google Fonts link (not needed for dark theme) ===
html = re.sub(r'<link[^>]*fonts\.googleapis\.com[^>]*>\s*', '', html)

# === 3. Add loremflickr photos to timeline items ===
# Keyword mapping (same as before)
def get_keywords(name):
    nl = name.lower()
    # Keep existing mapping...
    mapping = [
        (['pho minh'], 'vietnamese,pho,restaurant,saigon'),
        (['pho le'], 'pho,vietnamese,soup,food'),
        (['phở thìn'], 'hanoi,pho,vietnamese,streetfood'),
        (['phở bát'], 'hanoi,pho,traditional,vietnam'),
        (['banh canh'], 'crab,noodle,soup,vietnamese'),
        (['banh mi'], 'banhmi,vietnamese,sandwich,hanoi'),
        (['bun cha', 'obama'], 'buncha,hanoi,obama,vietnamese'),
        (['chả cá', 'cha ca'], 'hanoi,chaca,fish,vietnamese,grilled'),
        (['train street'], 'hanoi,train,street,railway'),
        (['bia hoi'], 'beer,hanoi,vietnamese,street'),
        (['bui vien'], 'buivien,saigon,nightlife,walkingstreet'),
        (['nguyen hue'], 'saigon,walkingstreet,promenade,vietnam'),
        (['vinh khanh'], 'saigon,foodstreet,streetfood,vietnam'),
        (['noong oi'], 'cafe,garden,saigon,vietnam,rustic'),
        (['oasis cafe'], 'cafe,koifish,saigon,garden'),
        (['van gogh'], 'vangogh,art,immersive,exhibition'),
        (['klook', 'hop-on', 'hop on'], 'saigon,bustour,city,sightseeing'),
        (['land at tan son'], 'saigon,airport,arrival,vietnam'),
        (['sapa night market'], 'sapa,nightmarket,hmong,handicraft'),
        (['sapa stone church'], 'sapa,stonechurch,architecture,vietnam'),
        (['cat cat'], 'sapa,catcat,village,hmong,waterfall'),
        (['fansipan', 'roof of indochina'], 'fansipan,mountain,cablecar,vietnam'),
        (['rong may', 'glass bridge'], 'sapa,glassbridge,suspension,mountain'),
        (['moana sapa'], 'sapa,moana,mountain,gateofheaven'),
        (['best view'], 'sapa,sunset,mountain,view'),
        (['white cloud'], 'cafe,sapa,mountain,eggcoffee'),
        (['o la la'], 'cafe,sapa,vietnamese,coffee'),
        (['phansi'], 'cafe,sapa,clouds,bbq,mountain'),
        (['viettrekking'], 'sapa,coffee,mountain,breakfast,cloud'),
        (['la do'], 'sapa,train,coffee,homestay,photography'),
        (['bus to sapa', 'bus to hanoi'], 'vietnam,mountain,bus,sleeper,scenic'),
        (['hoan kiem'], 'hanoi,hoankiem,lake,sunrise'),
        (['temple of literature', 'văn miếu'], 'hanoi,temple,literature,confucius'),
        (['x space'], 'digital,art,immersive,museum,hanoi'),
        (['grand world'], 'phuquoc,grandworld,nightlife,vietnam'),
        (['island tour'], 'phuquoc,island,snorkeling,speedboat'),
        (['sunset town', 'kiss bridge'], 'phuquoc,sunset,mediterranean,bridge'),
        (['duong dong'], 'phuquoc,nightmarket,seafood,vietnam'),
        (['vinwonders'], 'phuquoc,themepark,amusement,vietnam'),
        (['the once show'], 'phuquoc,show,spectacle,performance'),
        (['ong lang'], 'phuquoc,beach,palms,sand,paradise'),
        (['giang cafe', 'egg coffee'], 'hanoi,eggcoffee,cafe,vietnamese'),
        (['halong bay'], 'halongbay,cruise,limestone,karst'),
        (['hanoi weekend night market'], 'hanoi,nightmarket,oldquarter,weekend'),
        (['ham ninh'], 'phuquoc,fishing,village,authentic'),
        (['head to noi bai', 'flight to delhi', 'check out', 'head to airport'], 'vietnam,travel,airport,departure'),
        (['mien thao moc'], 'cafe,garden,zen,saigon,vietnam'),
        (['early lunch'], 'sapa,restaurant,mountain,meal'),
        (['last pho'], 'hanoi,pho,breakfast,vietnamese'),
    ]
    for keys, kw in mapping:
        if any(k in nl for k in keys):
            return kw
    # Default
    cleaned = re.sub(r'[^\w\s]', '', name).strip().lower().replace(' ','-')[:50]
    return f'vietnam,{cleaned}'

# Find all tl-name divs and add photos if not already present
count = 0
def add_photo(match):
    global count
    full = match.group(0)
    # Check if photo already exists after this div
    # Look ahead in the match string - but we're in regex, so just check if next part has tl-photo
    name = match.group(1).strip()
    keywords = get_keywords(name)
    url = f'https://loremflickr.com/400/300/{keywords}'
    count += 1
    return full + f'\n<img src="{url}" class="tl-photo" loading="lazy" alt="">'

# Only add photos to tl-name divs that don't already have a tl-photo right after
html = re.sub(
    r'<div class="tl-name">(.+?)</div>(?!\s*<img[^>]*class="tl-photo")',
    add_photo,
    html
)

print(f'Added {count} photos')

# === 4. Update meta ===
html = html.replace('55+ Enriched Locations', '55+ Locations • Real Photos • Dark Gold Theme')

with open('index.html', 'w') as f:
    f.write(html)

print(f'Done! HTML size: {len(html)} bytes')
