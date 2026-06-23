#!/usr/bin/env python3
"""Add Unsplash photos to every timeline item in the Vietnam travel website."""

import re

# Keyword mapping for each location (using cleaned name)
def get_keywords(name):
    name_lower = name.lower()
    if 'pho' in name_lower and 'minh' in name_lower:
        return 'vietnamese,pho,restaurant,saigon'
    if 'pho' in name_lower and 'le' in name_lower:
        return 'pho,vietnamese,soup,food'
    if 'phở' in name_lower and 'thìn' in name_lower:
        return 'hanoi,pho,vietnamese,streetfood'
    if 'phở' in name_lower and 'bát' in name_lower:
        return 'hanoi,pho,traditional,vietnam'
    if 'banh canh' in name_lower:
        return 'crab,noodle,soup,vietnamese'
    if 'banh mi' in name_lower:
        return 'banhmi,vietnamese,sandwich,hanoi'
    if 'bun cha' in name_lower or 'obama' in name_lower:
        return 'buncha,hanoi,obama,vietnamese'
    if 'chả cá' in name_lower or 'cha ca' in name_lower:
        return 'hanoi,chaca,fish,vietnamese,grilled'
    if 'train street' in name_lower:
        return 'hanoi,train,street,railway'
    if 'bia hoi' in name_lower:
        return 'beer,hanoi,vietnamese,street'
    if 'bui vien' in name_lower:
        return 'buivien,saigon,nightlife,walkingstreet'
    if 'nguyen hue' in name_lower:
        return 'saigon,walkingstreet,promenade,vietnam'
    if 'vinh khanh' in name_lower:
        return 'saigon,foodstreet,streetfood,vietnam'
    if 'noong oi' in name_lower:
        return 'cafe,garden,saigon,vietnam,rustic'
    if 'oasis cafe' in name_lower:
        return 'cafe,koifish,saigon,garden'
    if 'van gogh' in name_lower:
        return 'vangogh,art,immersive,exhibition'
    if 'klook' in name_lower or 'hop-on' in name_lower:
        return 'saigon,bustour,city,sightseeing'
    if 'land at tan son' in name_lower:
        return 'saigon,airport,arrival,vietnam'
    if 'sapa night market' in name_lower:
        return 'sapa,nightmarket,hmong,handicraft'
    if 'sapa stone church' in name_lower:
        return 'sapa,stonechurch,architecture,vietnam'
    if 'cat cat' in name_lower:
        return 'sapa,catcat,village,hmong,waterfall'
    if 'fansipan' in name_lower or 'roof of indochina' in name_lower:
        return 'fansipan,mountain,cablecar,vietnam'
    if 'rong may' in name_lower or 'glass bridge' in name_lower:
        return 'sapa,glassbridge,suspension,mountain'
    if 'moana sapa' in name_lower:
        return 'sapa,moana,mountain,gateofheaven'
    if 'best view' in name_lower:
        return 'sapa,sunset,mountain,view'
    if 'white cloud' in name_lower:
        return 'cafe,sapa,mountain,eggcoffee'
    if 'o la la' in name_lower and 'coffee' in name_lower:
        return 'cafe,sapa,vietnamese,coffee'
    if 'phansi' in name_lower:
        return 'cafe,sapa,clouds,bbq,mountain'
    if 'viettrekking' in name_lower:
        return 'sapa,coffee,mountain,breakfast,cloud'
    if 'la do' in name_lower:
        return 'sapa,train,coffee,homestay,photography'
    if 'bus to sapa' in name_lower or 'bus to hanoi' in name_lower:
        return 'vietnam,mountain,bus,sleeper,scenic'
    if 'hoan kiem' in name_lower:
        return 'hanoi,hoankiem,lake,sunrise'
    if 'temple of literature' in name_lower or 'văn miếu' in name_lower:
        return 'hanoi,temple,literature,confucius'
    if 'x space' in name_lower:
        return 'digital,art,immersive,museum,hanoi'
    if 'grand world' in name_lower:
        return 'phuquoc,grandworld,nightlife,vietnam'
    if '4 island' in name_lower or 'island tour' in name_lower:
        return 'phuquoc,island,snorkeling,speedboat'
    if 'sunset town' in name_lower or 'kiss bridge' in name_lower:
        return 'phuquoc,sunset,mediterranean,bridge'
    if 'duong dong' in name_lower:
        return 'phuquoc,nightmarket,seafood,vietnam'
    if 'vinwonders' in name_lower:
        return 'phuquoc,themepark,amusement,vietnam'
    if 'the once show' in name_lower:
        return 'phuquoc,show,spectacle,performance'
    if 'ong lang' in name_lower:
        return 'phuquoc,beach,palms,sand,paradise'
    if 'giang cafe' in name_lower or 'egg coffee' in name_lower:
        return 'hanoi,eggcoffee,cafe,vietnamese'
    if 'halong bay' in name_lower:
        return 'halongbay,cruise,limestone,karst'
    if 'hanoi weekend night market' in name_lower:
        return 'hanoi,nightmarket,oldquarter,weekend'
    if 'head to noi bai' in name_lower or 'flight to delhi' in name_lower:
        return 'hanoi,airport,departure,travel'
    if 'mien thao moc' in name_lower:
        return 'cafe,garden,zen,saigon,vietnam'
    if 'check out' in name_lower or 'head to airport' in name_lower:
        return 'saigon,airport,departure,travel'
    if 'early lunch' in name_lower:
        return 'sapa,restaurant,mountain,meal'
    if 'last pho' in name_lower:
        return 'hanoi,pho,breakfast,vietnamese'
    # Default: use cleaned name
    cleaned = re.sub(r'[^\w\s]', '', name).strip().lower().replace(' ','-')[:50]
    return f'vietnam,{cleaned}'

with open('index.html', 'r') as f:
    html = f.read()

# Store original for comparison
original = html

# Count modifications
count = 0

# Find each tl-name div and add photo after it
# Pattern: <div class="tl-name">CONTENT</div>
# Add after: <img src="..." class="tl-photo" loading="lazy" alt="">

def add_photo(match):
    global count
    full_match = match.group(0)
    name = match.group(1).strip()
    keywords = get_keywords(name)
    url = f'https://source.unsplash.com/400x300/?{keywords}'
    photo_html = f'\n<img src="{url}" class="tl-photo" loading="lazy" alt="">'
    count += 1
    return full_match + photo_html

html = re.sub(
    r'<div class="tl-name">(.+?)</div>',
    add_photo,
    html
)

# Add CSS for tl-photo
css_addition = '.tl-photo{width:100%;max-width:300px;height:auto;border-radius:10px;margin-top:6px;border:1px solid var(--border);object-fit:cover;transition:.3s}.tl-photo:hover{transform:scale(1.02)}'

# Insert CSS before </style>
html = html.replace('</style>', css_addition + '\n</style>', 1)

# Update meta line
html = html.replace(
    '55+ Enriched Locations',
    f'55+ Enriched Locations • Real Photos Added'
)

print(f'Added photos to {count} locations')
print(f'HTML size: {len(html)} bytes (was {len(original)} bytes)')

with open('index.html', 'w') as f:
    f.write(html)

print('Done! Written to index.html')
