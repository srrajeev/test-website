#!/usr/bin/env python3
"""ATOS Configuration — Vietnam Trip 2026"""
import os
from datetime import date

# === TRIP CONFIG ===
TRIP = {
    "name": "Vietnam 2026",
    "traveler": "SK",
    "start": "2026-06-28",
    "end": "2026-07-10",
    "currency": "INR",
    "inr_to_vnd": 279,
    "total_budget": 64000,  # INR
    "solo": True,
    "non_veg": True,
}

# === CITIES ===
CITIES = {
    "HCMC": {
        "name": "Ho Chi Minh City",
        "country": "Vietnam",
        "lat": 10.8231, "lon": 106.6297,
        "timezone": "Asia/Ho_Chi_Minh",
        "days": ["Jun 28", "Jun 29"],
        "arrival": "2026-06-28T21:00",
        "departure": "2026-06-30T14:00",
    },
    "Phu Quoc": {
        "name": "Phu Quoc Island",
        "country": "Vietnam",
        "lat": 10.2294, "lon": 103.9891,
        "timezone": "Asia/Ho_Chi_Minh",
        "days": ["Jun 30", "Jul 1", "Jul 2", "Jul 3"],
        "arrival": "2026-06-30T15:00",
        "departure": "2026-07-03T16:00",
    },
    "Hanoi": {
        "name": "Hanoi",
        "country": "Vietnam",
        "lat": 21.0285, "lon": 105.8542,
        "timezone": "Asia/Ho_Chi_Minh",
        "days": ["Jul 3", "Jul 4", "Jul 7", "Jul 8", "Jul 9", "Jul 10"],
        "arrival": "2026-07-03T20:00",
        "departure": "2026-07-10T14:00",
    },
    "Sapa": {
        "name": "Sapa",
        "country": "Vietnam",
        "lat": 22.3364, "lon": 103.8438,
        "timezone": "Asia/Ho_Chi_Minh",
        "days": ["Jul 4", "Jul 5", "Jul 6", "Jul 7"],
        "arrival": "2026-07-04T15:30",
        "departure": "2026-07-07T16:00",
    },
    "Halong Bay": {
        "name": "Halong Bay",
        "country": "Vietnam",
        "lat": 20.9101, "lon": 107.1839,
        "timezone": "Asia/Ho_Chi_Minh",
        "days": ["Jul 9"],
        "arrival": "2026-07-09T08:00",
        "departure": "2026-07-09T18:00",
    },
}

# === ITINERARY (13 days) ===
ITINERARY = [
    {"day": 0, "date": "Jun 28", "dow": "SUN", "city": "HCMC", "label": "Night Arrival", "icon": "🌙",
     "weather": {"temp_hi": 31, "temp_lo": 24, "condition": "Clear", "rain": 20, "risk": "low"},
     "tip": "Sunday = Bui Vien peak night! Streets pedestrian-only, neon everywhere",
     "plan": [
         {"time": "9:00 PM", "activity": "Land Tan Son Nhat (SGN)", "maps": "", "cost": "", "category": "transit"},
         {"time": "10:30 PM", "activity": "Check-in District 1", "maps": "", "cost": "", "category": "hotel"},
         {"time": "10:45 PM", "activity": "Bui Vien Walking Street — Sunday peak!", "maps": "https://maps.google.com/?q=Bui+Vien+Walking+Street+HCMC", "cost": "Beer ₹53-88", "category": "nightlife"},
     ]},
    {"day": 1, "date": "Jun 29", "dow": "MON", "city": "HCMC", "label": "Full Day Explorer", "icon": "🏙️",
     "weather": {"temp_hi": 31, "temp_lo": 24, "condition": "PM Storm", "rain": 60, "risk": "medium"},
     "tip": "Outdoor 7AM-2PM. Museum/cafe crawl after. Rain is predictable!",
     "plan": [
         {"time": "7:30 AM", "activity": "Pho breakfast — Pho Minh (since 1940s)", "maps": "", "cost": "₹246-316", "category": "food"},
         {"time": "8:30 AM", "activity": "Hop-On Hop-Off Bus @ Opera House", "maps": "https://maps.google.com/?q=Saigon+Opera+House+HCMC", "cost": "₹509 ⭐4.4", "category": "activity"},
         {"time": "10:45 AM", "activity": "Banh Canh Cua Ba Ba — MICHELIN 2026!", "maps": "https://maps.google.com/?q=84/6+Nguyen+Bieu+Quan+5+HCMC", "cost": "₹158-351 ⭐4.3", "category": "food"},
         {"time": "12:45 PM", "activity": "Van Gogh Metashow — 30+ immersive rooms", "maps": "https://maps.google.com/?q=Thiso+Mall+Sala+Thu+Duc", "cost": "₹878 ⭐4.6", "category": "activity"},
         {"time": "5:45 PM", "activity": "Vinh Khanh Food St — Seafood dinner", "maps": "https://maps.google.com/?q=Vinh+Khanh+Food+Street+D4+HCMC", "cost": "₹105-175 ⭐4.5", "category": "food"},
         {"time": "7:30 PM", "activity": "Bui Vien — Round 2!", "maps": "https://maps.google.com/?q=Bui+Vien+Walking+Street+HCMC", "cost": "", "category": "nightlife"},
     ]},
    {"day": 2, "date": "Jun 30", "dow": "TUE", "city": "Phu Quoc", "label": "Arrival + Grand World", "icon": "✈️",
     "weather": {"temp_hi": 31, "temp_lo": 23, "condition": "PM Shower", "rain": 45, "risk": "medium"},
     "tip": "Evening FREE shows at Grand World: Venice water show 9:30PM + Laser 10:45PM",
     "plan": [
         {"time": "7:00 AM", "activity": "Cu Chi Tunnels (morning best)", "maps": "", "cost": "~₹500", "category": "activity"},
         {"time": "2:00 PM", "activity": "Fly HCMC → Phu Quoc (1hr)", "maps": "", "cost": "~₹2,500-3,500", "category": "transit"},
         {"time": "6:00 PM", "activity": "Grand World — FREE entry", "maps": "https://maps.google.com/?q=Grand+World+Phu+Quoc", "cost": "FREE", "category": "activity"},
         {"time": "9:30 PM", "activity": "Charm of Venice Show — FREE!", "maps": "", "cost": "FREE", "category": "activity"},
         {"time": "10:45 PM", "activity": "Laser Show — FREE!", "maps": "", "cost": "FREE", "category": "activity"},
     ]},
    {"day": 3, "date": "Jul 1", "dow": "WED", "city": "Phu Quoc", "label": "4 Island Tour", "icon": "🏝️",
     "weather": {"temp_hi": 31, "temp_lo": 24, "condition": "Mixed", "rain": 50, "risk": "high"},
     "tip": "BOOK LOCAL ₹4,200 (NOT online ₹8,250!). July = low season, negotiate!",
     "plan": [
         {"time": "7:00 AM", "activity": "4 Island Tour — Hotel pickup", "maps": "https://maps.google.com/?q=An+Thoi+Port+Phu+Quoc", "cost": "₹4,200-5,250", "category": "activity"},
         {"time": "8:00 AM", "activity": "World's longest oversea cable car", "maps": "", "cost": "included", "category": "activity"},
         {"time": "10:00 AM", "activity": "Sea Walking — walk ocean floor!", "maps": "", "cost": "included", "category": "activity"},
         {"time": "5:30 PM", "activity": "Sunset Town — Kiss Bridge FREE", "maps": "https://maps.google.com/?q=Sunset+Town+Phu+Quoc", "cost": "FREE", "category": "activity"},
         {"time": "7:00 PM", "activity": "Duong Dong Night Market", "maps": "https://maps.google.com/?q=Duong+Dong+Night+Market+Phu+Quoc", "cost": "₹200-500", "category": "food"},
     ]},
    {"day": 4, "date": "Jul 2", "dow": "THU", "city": "Phu Quoc", "label": "VinWonders", "icon": "🎢",
     "weather": {"temp_hi": 31, "temp_lo": 24, "condition": "Partly Cloudy", "rain": 40, "risk": "low"},
     "tip": "Aquarium + indoor shows = rain-proof! THE ONCE SHOW 6:45PM — $12M production!",
     "plan": [
         {"time": "9:00 AM", "activity": "VinWonders — Vietnam's largest!", "maps": "https://maps.google.com/?q=VinWonders+Phu+Quoc", "cost": "₹3,410", "category": "activity"},
         {"time": "1:00 PM", "activity": "Deep Sea Restaurant — aquarium view", "maps": "", "cost": "₹500-700", "category": "food"},
         {"time": "3:00 PM", "activity": "Typhoon Water Park", "maps": "", "cost": "included", "category": "activity"},
         {"time": "6:45 PM", "activity": "THE ONCE SHOW — $12M production!", "maps": "", "cost": "included", "category": "activity"},
     ]},
    {"day": 5, "date": "Jul 3", "dow": "FRI", "city": "Hanoi", "label": "Beach AM + Fly + Hanoi PM", "icon": "✈️",
     "weather": {"temp_hi": 33, "temp_lo": 26, "condition": "Hot", "rain": 45, "risk": "medium"},
     "tip": "Ong Lang hidden beach morning, then fly. Hanoi evening: Weekend Night Market!",
     "plan": [
         {"time": "7:00 AM", "activity": "Ong Lang Beach — hidden gem", "maps": "https://maps.google.com/?q=Ong+Lang+Beach+Phu+Quoc", "cost": "FREE", "category": "activity"},
         {"time": "11:00 AM", "activity": "Ham Ninh Fishing Village", "maps": "https://maps.google.com/?q=Ham+Ninh+Village+Phu+Quoc", "cost": "₹200-400", "category": "food"},
         {"time": "3:00 PM", "activity": "Fly Phu Quoc → Hanoi (2hr)", "maps": "", "cost": "~₹3,000-4,000", "category": "transit"},
         {"time": "8:00 PM", "activity": "Hanoi Weekend Night Market!", "maps": "https://maps.google.com/?q=Hanoi+Night+Market+Old+Quarter", "cost": "₹200-500", "category": "nightlife"},
     ]},
    {"day": 6, "date": "Jul 4", "dow": "SAT", "city": "Sapa", "label": "Hanoi AM → Sapa PM", "icon": "⛰️",
     "weather": {"temp_hi": 22, "temp_lo": 17, "condition": "Foggy PM", "rain": 40, "risk": "medium"},
     "tip": "Bus ~9:30 AM arrive 3:30 PM. Sapa cool mountain air!",
     "plan": [
         {"time": "7:00 AM", "activity": "Pho Thin — #1 pho in Hanoi", "maps": "https://maps.google.com/?q=Pho+Thin+Hanoi", "cost": "₹150 ⭐4.5", "category": "food"},
         {"time": "9:30 AM", "activity": "Sapa Express Bus (6hrs)", "maps": "", "cost": "₹700-1,050", "category": "transit"},
         {"time": "3:30 PM", "activity": "Arrive Sapa — check-in", "maps": "", "cost": "", "category": "hotel"},
         {"time": "4:00 PM", "activity": "Sapa Square + Cathedral", "maps": "https://maps.google.com/?q=Sapa+Square+Church", "cost": "FREE", "category": "activity"},
         {"time": "6:00 PM", "activity": "Dinner — local BBQ", "maps": "", "cost": "₹300-500", "category": "food"},
     ]},
    {"day": 7, "date": "Jul 5", "dow": "SUN", "city": "Sapa", "label": "Moana + Cat Cat + Cafes", "icon": "📸",
     "weather": {"temp_hi": 21, "temp_lo": 16, "condition": "Morning Clear", "rain": 35, "risk": "low"},
     "tip": "Outdoor activities BEFORE 2PM. July fog rolls in afternoon.",
     "plan": [
         {"time": "7:00 AM", "activity": "Moana Sapa — photo spot", "maps": "https://maps.google.com/?q=Moana+Sapa", "cost": "₹350", "category": "activity"},
         {"time": "9:00 AM", "activity": "Cat Cat Village — waterfall", "maps": "https://maps.google.com/?q=Cat+Cat+Village+Sapa", "cost": "₹475 ⭐4.4", "category": "activity"},
         {"time": "12:00 PM", "activity": "Lunch — local Thang Co", "maps": "", "cost": "₹200-300", "category": "food"},
         {"time": "2:00 PM", "activity": "Cafe crawl — The Hill Station", "maps": "https://maps.google.com/?q=Hill+Station+Sapa", "cost": "₹150-250", "category": "cafe"},
         {"time": "5:00 PM", "activity": "Sunset at Sapa Square", "maps": "", "cost": "FREE", "category": "activity"},
     ]},
    {"day": 8, "date": "Jul 6", "dow": "MON", "city": "Sapa", "label": "Rong May Thrill Day", "icon": "🎢",
     "weather": {"temp_hi": 20, "temp_lo": 16, "condition": "Cloudy", "rain": 45, "risk": "medium"},
     "tip": "Rong May: glass bridge + zipline + alpine coaster. No weekend crowd difference.",
     "plan": [
         {"time": "8:00 AM", "activity": "Rong May Tourism Area", "maps": "https://maps.google.com/?q=Rong+May+Tourism+Sapa", "cost": "₹1,400 ⭐4.5", "category": "activity"},
         {"time": "12:00 PM", "activity": "Lunch — BBQ buffet included", "maps": "", "cost": "included", "category": "food"},
         {"time": "2:00 PM", "activity": "Heaven's Gate pass — viewpoint", "maps": "https://maps.google.com/?q=Heaven's+Gate+Sapa", "cost": "FREE", "category": "activity"},
         {"time": "4:00 PM", "activity": "Return Sapa town", "maps": "", "cost": "", "category": "transit"},
         {"time": "7:00 PM", "activity": "Dinner + cultural show", "maps": "", "cost": "₹400-600", "category": "food"},
     ]},
    {"day": 9, "date": "Jul 7", "dow": "TUE", "city": "Sapa", "label": "Fansipan → Hanoi", "icon": "🏔️",
     "weather": {"temp_hi": 19, "temp_lo": 15, "condition": "Morning Clear", "rain": 30, "risk": "low"},
     "tip": "Fansipan MOVED Sun→Tue: Sun queue = 2 HOURS, Tue = 10 min!",
     "plan": [
         {"time": "7:00 AM", "activity": "Fansipan Cable Car — Indochina's roof!", "maps": "https://maps.google.com/?q=Fansipan+Cable+Car+Sapa", "cost": "₹2,800 ⭐4.7", "category": "activity"},
         {"time": "11:00 AM", "activity": "Lunch — summit cafe", "maps": "", "cost": "₹300-400", "category": "food"},
         {"time": "1:00 PM", "activity": "Return Sapa town", "maps": "", "cost": "", "category": "transit"},
         {"time": "4:00 PM", "activity": "Sapa Express Bus → Hanoi (6hrs)", "maps": "", "cost": "₹700-1,050", "category": "transit"},
         {"time": "10:00 PM", "activity": "Arrive Hanoi — check-in", "maps": "", "cost": "", "category": "hotel"},
     ]},
    {"day": 10, "date": "Jul 8", "dow": "WED", "city": "Hanoi", "label": "Full Day Explorer", "icon": "🏙️",
     "weather": {"temp_hi": 34, "temp_lo": 27, "condition": "Hot + PM Storm", "rain": 55, "risk": "medium"},
     "tip": "Morning outdoor, afternoon indoor. X Space immersive + Train Street!",
     "plan": [
         {"time": "7:00 AM", "activity": "Pho Thin — second visit (it's that good)", "maps": "https://maps.google.com/?q=Pho+Thin+Hanoi", "cost": "₹150 ⭐4.5", "category": "food"},
         {"time": "8:30 AM", "activity": "Hoan Kiem Lake + Ngoc Son Temple", "maps": "https://maps.google.com/?q=Hoan+Kiem+Lake+Hanoi", "cost": "₹70", "category": "activity"},
         {"time": "10:00 AM", "activity": "Temple of Literature — 1000 years old", "maps": "https://maps.google.com/?q=Temple+of+Literature+Hanoi", "cost": "₹105 ⭐4.7", "category": "activity"},
         {"time": "12:00 PM", "activity": "Bun Cha — Obama's spot", "maps": "https://maps.google.com/?q=Bun+Cha+Huong+Lien+Hanoi", "cost": "₹250 ⭐4.5", "category": "food"},
         {"time": "2:00 PM", "activity": "X Space Immersive — 8 zones", "maps": "https://maps.google.com/?q=X+Space+Immersive+Hanoi", "cost": "₹700 ⭐4.6", "category": "activity"},
         {"time": "5:00 PM", "activity": "Train Street — iconic photo", "maps": "https://maps.google.com/?q=Hanoi+Train+Street", "cost": "₹100 coffee", "category": "activity"},
         {"time": "7:00 PM", "activity": "Water Puppet Theatre", "maps": "https://maps.google.com/?q=Thang+Long+Water+Puppet+Hanoi", "cost": "₹350 ⭐4.6", "category": "activity"},
     ]},
    {"day": 11, "date": "Jul 9", "dow": "THU", "city": "Halong Bay", "label": "Day Trip — Highest Risk Day", "icon": "🚢",
     "weather": {"temp_hi": 33, "temp_lo": 27, "condition": "Check Wind", "rain": 40, "risk": "high"},
     "tip": "HIGHEST risk day. Check windy.com 3 days before. Backup: Water Puppet + Ceramic Mural.",
     "plan": [
         {"time": "6:30 AM", "activity": "Limousine bus to Halong Bay (2.5hrs)", "maps": "", "cost": "₹800-1,200", "category": "transit"},
         {"time": "9:00 AM", "activity": "Halong Bay cruise — caves + kayaking", "maps": "https://maps.google.com/?q=Halong+Bay+Cruise", "cost": "₹1,500-2,500 ⭐4.6", "category": "activity"},
         {"time": "12:00 PM", "activity": "Seafood lunch on boat", "maps": "", "cost": "included", "category": "food"},
         {"time": "3:00 PM", "activity": "Titop Island — beach + viewpoint", "maps": "https://maps.google.com/?q=Titop+Island+Halong+Bay", "cost": "included", "category": "activity"},
         {"time": "5:00 PM", "activity": "Return bus to Hanoi", "maps": "", "cost": "included", "category": "transit"},
         {"time": "8:00 PM", "activity": "Dinner — Hanoi Old Quarter", "maps": "", "cost": "₹300-500", "category": "food"},
     ]},
    {"day": 12, "date": "Jul 10", "dow": "FRI", "city": "Hanoi", "label": "Departure Day", "icon": "✈️",
     "weather": {"temp_hi": 34, "temp_lo": 27, "condition": "Hot", "rain": 35, "risk": "low"},
     "tip": "Morning market run. Airport by 12 PM. Flight to Delhi.",
     "plan": [
         {"time": "7:00 AM", "activity": "Dong Xuan Market — souvenirs", "maps": "https://maps.google.com/?q=Dong+Xuan+Market+Hanoi", "cost": "₹500-2000", "category": "shopping"},
         {"time": "9:00 AM", "activity": "Last pho — Pho Bat Dan", "maps": "https://maps.google.com/?q=Pho+Bat+Dan+Hanoi", "cost": "₹140 ⭐4.6", "category": "food"},
         {"time": "11:00 AM", "activity": "Airport taxi — Noi Bai", "maps": "", "cost": "₹700-1,000", "category": "transit"},
         {"time": "2:00 PM", "activity": "Fly Hanoi → Delhi", "maps": "", "cost": "included in intl", "category": "transit"},
     ]},
]

# === BUDGET BREAKDOWN ===
BUDGET = {
    "total_planned": 64000,
    "categories": {
        "flights": {"planned": 18000, "spent": 0, "items": ["Delhi-HCMC intl", "HCMC-Phu Quoc", "Phu Quoc-Hanoi", "Hanoi-Delhi intl"]},
        "hotels": {"planned": 12000, "spent": 0, "items": ["9 nights @ ₹800-1,500"]},
        "activities": {"planned": 29751, "spent": 0, "items": ["Tours, parks, attractions"]},
        "food": {"planned": 8000, "spent": 0, "items": ["13 days meals"]},
        "transport_local": {"planned": 4000, "spent": 0, "items": ["Buses, taxis, Grab"]},
        "shopping": {"planned": 3000, "spent": 0, "items": ["Souvenirs, gifts"]},
    },
    "by_city": {
        "HCMC": 2600,
        "Phu Quoc": 8745,
        "Sapa": 11190,
        "Hanoi": 7200,
    }
}

# === SCAM DATA (from research) ===
SCAMS = [
    {"city": "HCMC", "type": "Taxi", "scam": "Fake taxi meters / overcharging", "risk": "high",
     "avoid": "Use Grab app only. Never street hail.",
     "action": "Download Grab before landing. Always check plate matches app."},
    {"city": "HCMC", "type": "Pickpocket", "scam": "Bui Vien pickpockets", "risk": "medium",
     "avoid": "Keep phone in front pocket. No back pocket wallet.",
     "action": "Money belt under clothes. Minimal cash out."},
    {"city": "HCMC", "type": "Motorbike", "scam": "Bag snatching from motorbikes", "risk": "high",
     "avoid": "Don't hold phone near road edge.",
     "action": "Walk on building side of sidewalk. Cross-body bag."},
    {"city": "Phu Quoc", "type": "Tour", "scam": "4-island tour overcharging", "risk": "high",
     "avoid": "Online booking ₹8,250 vs local ₹4,200",
     "action": "Book at hotel reception or local agencies. Walk-in prices 50% lower."},
    {"city": "Phu Quoc", "type": "Taxi", "scam": "No meter / inflated fares", "risk": "high",
     "avoid": "Only use Grab or Mai Linh taxi",
     "action": "Agree price before getting in if no Grab."},
    {"city": "Phu Quoc", "type": "Market", "scam": "Duong Dong night market per-100g pricing trap", "risk": "medium",
     "avoid": "Clarify total price, not per-100g",
     "action": "Ask 'how much total?' not 'how much per 100g'."},
    {"city": "Hanoi", "type": "Cyclo", "scam": "Cyclo scam — agreed ₹200, charged ₹2000", "risk": "high",
     "avoid": "NEVER take cyclos. Walk or Grab.",
     "action": "Politely refuse. If trapped, pay ₹500 max and walk away."},
    {"city": "Hanoi", "type": "Shoe shine", "scam": "Unsolicited shoe shine → demand ₹1000", "risk": "medium",
     "avoid": "Keep walking. Don't stop.",
     "action": "If they already started, pay ₹100 max."},
    {"city": "Sapa", "type": "Trekking", "scam": "Fake guides offering 'free' trekking", "risk": "medium",
     "avoid": "Book through hotel. Official guides have ID.",
     "action": "Demand official guide card. Refuse 'free' offers."},
    {"city": "Halong Bay", "type": "Cruise", "scam": "Bait-and-switch cruise quality", "risk": "medium",
     "avoid": "Book top-rated on Klook/Tripadvisor.",
     "action": "Photograph boat name. Complain on the spot if different."},
    {"city": "All", "type": "SIM Card", "scam": "Airport SIM overcharging (₹2000 vs ₹500)", "risk": "high",
     "avoid": "Buy at official Viettel/Vinaphone store.",
     "action": "Buy at city center, not airport. ~₹500 for 5GB/7 days."},
    {"city": "All", "type": "Exchange", "scam": "Money exchange short counting", "risk": "medium",
     "avoid": "Only exchange at banks or official counters.",
     "action": "Count money yourself before leaving counter. Use ATM instead."},
]

# === FOOD INTELLIGENCE ===
FOOD = {
    "must_try": [
        {"dish": "Pho (Pho Thin)", "city": "Hanoi", "where": "Pho Thin", "price": "₹150", "rating": 4.5, "note": "#1 pho in Vietnam"},
        {"dish": "Bun Cha", "city": "Hanoi", "where": "Bun Cha Huong Lien", "price": "₹250", "rating": 4.5, "note": "Obama ate here"},
        {"dish": "Banh Canh Cua", "city": "HCMC", "where": "Banh Canh Cua Ba Ba", "price": "₹158-351", "rating": 4.3, "note": "MICHELIN Bib Gourmand 2026"},
        {"dish": "Banh Mi Huynh Hoa", "city": "HCMC", "where": "Bui Vien", "price": "₹105", "rating": 4.9, "note": "Bourdain-approved"},
        {"dish": "Seafood (Vinh Khanh)", "city": "HCMC", "where": "Vinh Khanh Food St", "price": "₹105-175", "rating": 4.5, "note": "Time Out UK top 31"},
        {"dish": "Sim Wine", "city": "Phu Quoc", "where": "Duong Dong Market", "price": "₹200-400", "rating": 0, "note": "Local specialty — rose myrtle wine"},
        {"dish": "Fish Sauce", "city": "Phu Quoc", "where": "Duong Dong", "price": "₹300-600", "rating": 0, "note": "World's best fish sauce — souvenir"},
        {"dish": "Thang Co", "city": "Sapa", "where": "Sapa town", "price": "₹200-300", "rating": 0, "note": "Hmong horse meat stew — adventurous!"},
        {"dish": "Grilled Mountain Food", "city": "Sapa", "where": "Sapa BBQ", "price": "₹300-500", "rating": 0, "note": "Buffalo, pork, vegetables on grill"},
        {"dish": "Deep Sea Restaurant", "city": "Phu Quoc", "where": "VinWonders", "price": "₹500-700", "rating": 0, "note": "Aquarium view dining"},
    ],
    "by_city": {
        "HCMC": {"breakfast": "Pho Minh (₹246-316)", "lunch": "Banh Canh Cua Ba Ba (₹158-351)", "dinner": "Vinh Khanh Food St (₹105-175)", "cafe": "Cong Caphe (₹150)"},
        "Phu Quoc": {"breakfast": "Hotel breakfast", "lunch": "4-island tour lunch (included)", "dinner": "Duong Dong Night Market (₹200-500)", "cafe": "Oasis Cafe (₹150)"},
        "Hanoi": {"breakfast": "Pho Thin (₹150)", "lunch": "Bun Cha Huong Lien (₹250)", "dinner": "Hanoi Old Quarter (₹300-500)", "cafe": "Train St cafe (₹100)"},
        "Sapa": {"breakfast": "Hotel breakfast", "lunch": "Local Thang Co (₹200-300)", "dinner": "Sapa BBQ (₹400-600)", "cafe": "The Hill Station (₹150-250)"},
    },
    "veg_options": [
        "Banh Mi Chay (vegetarian banh mi) — everywhere",
        "Com Chay (vegetarian rice) — most restaurants",
        "Fresh spring rolls — request no shrimp",
        "Pho Chay — vegetable broth pho, common in Hanoi",
    ]
}

# === PACKING ===
PACKING = {
    "documents": ["Passport (6+ months validity)", "Visa approval letter", "Travel insurance", "Flight printouts", "Hotel bookings", "Emergency contacts"],
    "electronics": ["Phone + charger", "Power bank (20000mAh)", "Universal adapter (Type A/C)", "Earphones", "Camera (optional)"],
    "clothing": ["Light cotton t-shirts (5-6)", "Shorts (3)", "Light jacket (Sapa cool)", "Rain jacket/poncho", "Swimwear (Phu Quoc)", "Comfortable walking shoes", "Flip flops", "Socks (5 pairs)"],
    "health": ["Basic first aid kit", "Mosquito repellent (DEET)", "Sunscreen SPF50+", "Hand sanitizer", "Wet wipes", "Any prescription meds", "Anti-diarrheal (Imodium)", "Rehydration salts"],
    "misc": ["Money belt", "Sunglasses", "Hat/cap", "Reusable water bottle", "Snacks for travel", "Small backpack", "Zip-lock bags (waterproof)"],
    "weather_specific": {
        "HCMC": "Rain gear essential — PM storms daily. UV protection.",
        "Phu Quoc": "Reef-safe sunscreen. Snorkel gear optional. Seasickness meds.",
        "Hanoi": "Hot + humid. Light clothes. PM storm protection.",
        "Sapa": "Cool mountain mornings (15-17°C). Light jacket + layers. Fog protection for camera.",
    }
}

# === CONTENT IDEAS ===
CONTENT = {
    "reels": [
        {"title": "Bui Vien Sunday Night — Neon Chaos 🌙", "day": 0, "concept": "Walking through pedestrian-only street, neon lights, street food, beers", "hook": "POV: It's Sunday night in Saigon and the streets are ALIVE"},
        {"title": "MICHELIN Crab Noodles for ₹158 🦀", "day": 1, "concept": "Banh Canh Cua Ba Ba — close-up of crab broth, queue, sells out by 1PM", "hook": "This ₹158 MICHELIN noodle bowl sells out every single day"},
        {"title": "World's Longest Oversea Cable Car 🚡", "day": 3, "concept": "4-island tour, cable car POV, sea walking helmet cam", "hook": "I walked on the OCEAN FLOOR in Vietnam"},
        {"title": "VinWonders $12M Show 🎢", "day": 4, "concept": "Theme park day + THE ONCE show — fire, water, light spectacle", "hook": "This $12M show is INCLUDED in a ₹3,410 theme park ticket"},
        {"title": "Fansipan — Roof of Indochina 🏔️", "day": 9, "concept": "Cable car ascent, summit clouds, Buddha statue, 10-min queue flex", "hook": "2 hour queue on Sunday. 10 minutes on Tuesday. Timing is EVERYTHING."},
        {"title": "Halong Bay — Nature's Masterpiece 🚢", "day": 11, "concept": "Cruise through limestone karsts, cave exploration, kayaking", "hook": "This is why Halong Bay is a UNESCO World Heritage Site"},
        {"title": "Train Street — Inches from Death 🚂", "day": 10, "concept": "Drinking coffee as train passes 2 feet away", "hook": "Would you drink coffee HERE?"},
    ],
    "youtube_titles": [
        "I Spent ₹54,000 in Vietnam for 13 Days (Full Breakdown)",
        "Vietnam's MICHELIN Street Food Costs LESS Than McDonald's",
        "The Fansipan Timing Hack That Saved Me 2 Hours",
        "Vietnam Night Markets: What Tourists Get Wrong",
        "Solo Vietnam: 4 Cities in 13 Days — Complete Guide",
    ],
    "photo_spots": [
        {"spot": "Bui Vien neon at night", "city": "HCMC", "time": "10 PM", "tip": "Long exposure for light trails"},
        {"spot": "Sunset Town Kiss Bridge", "city": "Phu Quoc", "time": "5:30 PM", "tip": "Golden hour — silhouette on bridge"},
        {"spot": "Fansipan summit", "city": "Sapa", "time": "8 AM", "tip": "Cloud sea below — arrive early for clear shot"},
        {"spot": "Train Street", "city": "Hanoi", "time": "5 PM", "tip": "Train passes ~3:45 and 7:00 PM. Coffee shop rooftop angle"},
        {"spot": "Halong Bay from Titop Island", "city": "Halong Bay", "time": "3 PM", "tip": "Climb to viewpoint — 400 steps, best panorama"},
        {"spot": "Sapa rice terraces", "city": "Sapa", "time": "7 AM", "tip": "Morning fog creates layered mountain shots"},
        {"spot": "Temple of Literature", "city": "Hanoi", "time": "8 AM", "tip": "Empty before tour buses arrive"},
    ],
    "stories": [
        "Day 0: Landing in Saigon — first impressions",
        "Day 1: MICHELIN street food hunt",
        "Day 3: Island hopping — cable car + sea walking",
        "Day 7: Sapa mountain life — Cat Cat village",
        "Day 9: Summit of Indochina — Fansipan",
        "Day 11: Halong Bay — risk vs reward",
    ]
}

# === EMERGENCY ===
EMERGENCY = {
    "contacts": {
        "india_embassy_hanoi": "+84-24-38239899",
        "india_embassy_hcmc": "+84-28-39303200",
        "police": "113",
        "ambulance": "115",
        "fire": "114",
        "tourist_police_hcmc": "+84-28-39372525",
        "tourist_police_hanoi": "+84-24-39361204",
    },
    "backup_plans": {
        "flight_cancelled": "Rebook via VietJet/Vietnam Airlines. Claim travel insurance. Hotel extra night ~₹1000.",
        "lost_baggage": "File report at airport. Buy essentials at local market (₹500-1000). Track via airline app.",
        "medical_emergency": "Vinmec Hospital (Hanoi/HCMC) — English speaking. FV Hospital (HCMC). Travel insurance covers.",
        "hotel_problem": "Booking.com 24/7 support. Backup: Agoda same-day booking. Hostelworld for budget.",
        "severe_weather_halong": "CANCEL cruise. Backup day: Water Puppet Theatre + Ceramic Mural + Hanoi museums.",
        "severe_weather_sapa": "Skip cable car. Backup: Sapa Museum + indoor cafes + local market.",
        "lost_phone": "Use hotel wifi to contact via email. Backup: Buy local SIM + cheap phone (₹2000).",
        "money_theft": "Emergency funds via Western Union. Card freeze immediately. File police report for insurance.",
    },
    "hospitals": [
        {"name": "Vinmec International Hospital", "city": "Hanoi", "phone": "+84-24-39743418", "english": True},
        {"name": "FV Hospital (Franco-Vietnamese)", "city": "HCMC", "phone": "+84-28-54113334", "english": True},
        {"name": "Vinmec Phu Quoc", "city": "Phu Quoc", "phone": "+84-297-3990000", "english": True},
        {"name": "Lao Cai Provincial Hospital", "city": "Sapa", "phone": "+84-214-3832114", "english": False},
    ]
}

# === APIFY CONFIG ===
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
APIFY_ACTORS = {
    "google_maps": "nwua9Gu5YrADL7ZDj",
    "google_maps_reviews": "xMD5jyqWqvxJui09o",
    "tripadvisor": "nCyBsbLnHsA7CAQ3g",
}

# === PATHS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")  # test-website/data/
REPO_DIR = os.path.dirname(BASE_DIR)  # test-website/
