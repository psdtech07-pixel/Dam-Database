import json
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'pune_dams.db')
REGISTRY_PATH = os.path.join(BASE_DIR, 'database', 'dam_registry.json')

# Rich encyclopedia data for Maharashtra Reservoirs
DAM_METADATA = {
    # ------------------ PUNE DISTRICT ------------------
    'khadakwasla': {
        'taluka': 'Haveli', 'nearest_city': 'Pune', 'river': 'Mutha',
        'year': 1879, 'height_m': 32.9, 'length_m': 1539,
        'purpose': 'Primary drinking water supply for Pune Municipal Corporation (PMC) and agricultural irrigation.',
        'description': 'Khadakwasla Dam is built across the Mutha River 20 km southwest of Pune. The reservoir, known as Lake Fife, serves as the main source of water for Pune and Khadakwasla National Defence Academy (NDA).',
        'image_url': 'https://images.unsplash.com/photo-1578328819058-b69f3a3b0f6b?auto=format&fit=crop&w=1200&q=80'
    },
    'panshet': {
        'taluka': 'Velhe', 'nearest_city': 'Pune', 'river': 'Ambi',
        'year': 1961, 'height_m': 63.5, 'length_m': 1039,
        'purpose': 'Major drinking water storage for Pune metropolitan region and downstream irrigation.',
        'description': 'Panshet Dam (officially Tanajisagar) is an earthfill dam situated on the Ambi River in the Western Ghats. It forms the second-largest reservoir in the Mutha river basin supplying Pune.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80'
    },
    'varasgaon': {
        'taluka': 'Velhe', 'nearest_city': 'Pune', 'river': 'Mose',
        'year': 1994, 'height_m': 63.4, 'length_m': 785,
        'purpose': 'Drinking water reservoir for Pune and PCMC, alongside hydroelectric power generation.',
        'description': 'Varasgaon Dam (officially Veer Baaji Pasalkar Dam) is constructed on the Mose River adjacent to Panshet. It is the largest of the four dams in the Khadakwasla complex.',
        'image_url': 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80'
    },
    'temghar': {
        'taluka': 'Mulshi', 'nearest_city': 'Pune', 'river': 'Mutha',
        'year': 2000, 'height_m': 87.0, 'length_m': 1075,
        'purpose': 'Water storage for Pune city, situated at the source of Mutha River near Lavasa.',
        'description': 'Temghar Dam is situated near Lavasa on the Mutha River. Its catchment receives heavy Sahyadri monsoon rainfall, regulating upstream flows into Khadakwasla.',
        'image_url': 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1200&q=80'
    },
    'pavana': {
        'taluka': 'Maval', 'nearest_city': 'Pimpri-Chinchwad / Lonavala', 'river': 'Pavana',
        'year': 1972, 'height_m': 42.3, 'length_m': 1329,
        'purpose': 'Lifeline drinking water reservoir for Pimpri-Chinchwad (PCMC), Talegaon, and Maval.',
        'description': 'Pavana Dam (Pavana Lake) is located in Maval taluka near Kamshet and Lonavala. It provides drinking water to over 2.5 million residents in Pimpri-Chinchwad and the surrounding industrial corridor.',
        'image_url': 'https://images.unsplash.com/photo-1518495973542-4542c06a5843?auto=format&fit=crop&w=1200&q=80'
    },
    'mulshi': {
        'taluka': 'Mulshi', 'nearest_city': 'Pune', 'river': 'Mula',
        'year': 1927, 'height_m': 48.8, 'length_m': 1530,
        'purpose': 'Hydroelectric power generation for Tata Power Bhira station and drinking water storage.',
        'description': 'Mulshi Dam is a historic gravity dam on the Mula River operated by Tata Power. Water is diverted through the Western Ghats to the Bhira hydroelectric generating station.',
        'image_url': 'https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1200&q=80'
    },
    'bhatghar': {
        'taluka': 'Bhor', 'nearest_city': 'Shirwal / Pune', 'river': 'Yelwandi',
        'year': 1927, 'height_m': 57.9, 'length_m': 1625,
        'purpose': 'Irrigation for Pune and Solapur districts, historically known as Lloyd Dam.',
        'description': 'Bhatghar Dam (officially Yesaji Kank Dam) is one of the highest stone masonry gravity dams in Maharashtra, built across the Yelwandi river in Bhor taluka.',
        'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80'
    },
    'dimbhe': {
        'taluka': 'Ambegaon', 'nearest_city': 'Manchar / Pune', 'river': 'Ghod',
        'year': 2000, 'height_m': 67.2, 'length_m': 852,
        'purpose': 'Irrigation for Ambegaon and Shirur talukas, and hydro-power generation.',
        'description': 'Dimbhe Dam is an earthfill and gravity dam on the Ghod River in Ambegaon taluka. It feeds the Kukadi canal irrigation system.',
        'image_url': 'https://images.unsplash.com/photo-1439853949127-fa647821eea0?auto=format&fit=crop&w=1200&q=80'
    },
    'bhama-askhed': {
        'taluka': 'Khed', 'nearest_city': 'Chakan / Pune', 'river': 'Bhama',
        'year': 2000, 'height_m': 51.0, 'length_m': 1425,
        'purpose': 'Drinking water pipeline for East Pune (Nagar Road, Kharadi) and irrigation in Khed.',
        'description': 'Bhama Askhed Dam is built on the Bhama River in Khed taluka. It supplies 200 MLD of drinking water to Pune eastern suburbs.',
        'image_url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80'
    },
    'chaskaman': {
        'taluka': 'Khed', 'nearest_city': 'Rajgurunagar / Chakan', 'river': 'Bhima',
        'year': 2002, 'height_m': 46.0, 'length_m': 960,
        'purpose': 'Irrigation and industrial water for the Chakan auto manufacturing cluster.',
        'description': 'Chaskaman Dam is an earthfill gravity dam on the upper Bhima River near Rajgurunagar, supporting agriculture and industrial growth.',
        'image_url': 'https://images.unsplash.com/photo-1542332213-31f87348057f?auto=format&fit=crop&w=1200&q=80'
    },
    'manikdoh': {
        'taluka': 'Junnar', 'nearest_city': 'Junnar / Narayangaon', 'river': 'Kukadi',
        'year': 1984, 'height_m': 52.0, 'length_m': 930,
        'purpose': 'Irrigation in Junnar and leopard conservation reserve sanctuary buffer.',
        'description': 'Manikdoh Dam is located on the Kukadi River in Junnar. The catchment area is famous for historical hill forts like Shivneri and biodiversity reserves.',
        'image_url': 'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1200&q=80'
    },
    'gunjawani': {
        'taluka': 'Velhe', 'nearest_city': 'Pune', 'river': 'Kanandi',
        'year': 2004, 'height_m': 52.8, 'length_m': 640,
        'purpose': 'Pressurized piped drip irrigation network in Purandar and Velhe talukas.',
        'description': 'Gunjawani Dam is built on the Kanandi River in Velhe taluka, featuring Maharashtra’s pioneer underground piped irrigation distribution network.',
        'image_url': 'https://images.unsplash.com/photo-1426604966848-d7adac402bff?auto=format&fit=crop&w=1200&q=80'
    },
    'nira-deoghar': {
        'taluka': 'Bhor', 'nearest_city': 'Mahad / Bhor', 'river': 'Nira',
        'year': 2000, 'height_m': 58.5, 'length_m': 2430,
        'purpose': 'Irrigation for drought-prone regions in Khandala, Phaltan, and Malshiras.',
        'description': 'Nira Deoghar Dam is a massive composite dam on the Nira River in Bhor taluka, storing monsoon runoff for dry eastern agricultural plains.',
        'image_url': 'https://images.unsplash.com/photo-1473448912268-2022ce9509d8?auto=format&fit=crop&w=1200&q=80'
    },
    'bhima-ujjani': {
        'taluka': 'Madha', 'nearest_city': 'Solapur / Daund', 'river': 'Bhima',
        'year': 1980, 'height_m': 56.4, 'length_m': 2534,
        'purpose': 'Major irrigation terminal reservoir for Solapur district, drinking water, and fisheries.',
        'description': 'Ujjani Dam (Bhima Reservoir) is the largest reservoir by gross storage in western Maharashtra (3,320 MCM gross). It supports agriculture across Solapur and Pune borders.',
        'image_url': 'https://images.unsplash.com/photo-1498084393753-b411b2d26b34?auto=format&fit=crop&w=1200&q=80'
    },
    'koyna': {
        'taluka': 'Patan', 'nearest_city': 'Karad / Chiplun', 'river': 'Koyna',
        'year': 1964, 'height_m': 103.2, 'length_m': 807,
        'purpose': 'Maharashtra’s largest hydroelectric power generation complex (1,960 MW) and irrigation.',
        'description': 'Koyna Dam (Shivsagar Lake) is a rubble-concrete dam on the Koyna River. It generates critical peaking electrical power for Maharashtra state grid.',
        'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80'
    },

    # ------------------ KONKAN / MUMBAI ------------------
    'bhatsa': {
        'taluka': 'Shahapur', 'nearest_city': 'Kalyan / Mumbai', 'river': 'Bhatsa',
        'year': 1977, 'height_m': 88.5, 'length_m': 959,
        'purpose': 'Largest single drinking water source for Brihanmumbai Municipal Corporation (BMC).',
        'description': 'Bhatsa Dam is an earthfill and masonry dam on the Bhatsa River in Thane district. It contributes over 50% of Greater Mumbai’s daily municipal drinking supply.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80'
    },
    'tansa': {
        'taluka': 'Shahapur', 'nearest_city': 'Thane / Mumbai', 'river': 'Tansa',
        'year': 1892, 'height_m': 41.0, 'length_m': 2804,
        'purpose': 'Heritage drinking water supply dam for Mumbai with Tansa Wildlife Sanctuary.',
        'description': 'Tansa Dam is a historic masonry gravity dam on the Tansa River, constructed under British rule in 1892, surrounded by the dense Tansa Wildlife Sanctuary.',
        'image_url': 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80'
    },
    'middle-vaitarna': {
        'taluka': 'Mokhada', 'nearest_city': 'Igatpuri / Mumbai', 'river': 'Vaitarna',
        'year': 2012, 'height_m': 102.0, 'length_m': 565,
        'purpose': 'Modern roller-compacted concrete dam providing 455 MLD drinking water to Mumbai.',
        'description': 'Middle Vaitarna Dam (Balasaheb Thackeray Reservoir) is the third highest dam in Maharashtra, built using state-of-the-art roller-compacted concrete technology.',
        'image_url': 'https://images.unsplash.com/photo-1439853949127-fa647821eea0?auto=format&fit=crop&w=1200&q=80'
    },
    'modak-sagar': {
        'taluka': 'Shahapur', 'nearest_city': 'Thane / Mumbai', 'river': 'Lower Vaitarna',
        'year': 1957, 'height_m': 49.0, 'length_m': 640,
        'purpose': 'Vital drinking water reservoir for Mumbai, named after engineer N. V. Modak.',
        'description': 'Modak Sagar Dam is built across the lower Vaitarna River, directly impounding monsoon flows to supply suburban and south Mumbai.',
        'image_url': 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1200&q=80'
    },
    'barvi': {
        'taluka': 'Ambernath', 'nearest_city': 'Badlapur / Kalyan', 'river': 'Barvi',
        'year': 1974, 'height_m': 48.0, 'length_m': 746,
        'purpose': 'Drinking water for Thane, Navi Mumbai, Kalyan-Dombivli, and Ulhasnagar.',
        'description': 'Barvi Dam is operated by MIDC and located near Badlapur on the Barvi River, serving as the industrial and urban lifeline of Thane district.',
        'image_url': 'https://images.unsplash.com/photo-1518495973542-4542c06a5843?auto=format&fit=crop&w=1200&q=80'
    },

    # ------------------ NASHIK / MARATHWADA ------------------
    'jayakwadi': {
        'taluka': 'Paithan', 'nearest_city': 'Chhatrapati Sambhajinagar', 'river': 'Godavari',
        'year': 1976, 'height_m': 41.3, 'length_m': 9998,
        'purpose': 'Marathwada’s largest multi-purpose reservoir for drinking, industry (MIDC), and irrigation.',
        'description': 'Jayakwadi Dam (Nath Sagar) is one of the largest earthen dams in Asia, constructed across the sacred Godavari River in Paithan taluka with a 10 km dam wall.',
        'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80'
    },
    'gangapur': {
        'taluka': 'Nashik', 'nearest_city': 'Nashik', 'river': 'Godavari',
        'year': 1954, 'height_m': 36.6, 'length_m': 3902,
        'purpose': 'Primary drinking water supply for Nashik Municipal Corporation (NMC) and Godavari canals.',
        'description': 'Gangapur Dam is historic as India’s first large earthen dam built post-independence, situated 10 km upstream of Nashik on the Godavari River.',
        'image_url': 'https://images.unsplash.com/photo-1578328819058-b69f3a3b0f6b?auto=format&fit=crop&w=1200&q=80'
    },
    'darna': {
        'taluka': 'Igatpuri', 'nearest_city': 'Igatpuri / Nashik', 'river': 'Darna',
        'year': 1916, 'height_m': 28.0, 'length_m': 1634,
        'purpose': 'Monsoon storage regulating Godavari river downstream flows and Nashik supply.',
        'description': 'Darna Dam is a stone masonry gravity dam located near Igatpuri in the high-rainfall Western Ghats belt, built across the Darna River.',
        'image_url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80'
    },
    'bhandardara': {
        'taluka': 'Akole', 'nearest_city': 'Sangamner / Igatpuri', 'river': 'Pravara',
        'year': 1926, 'height_m': 82.3, 'length_m': 507,
        'purpose': 'Irrigation for Pravara basin, Arthur Lake tourism, and hydro-electric power.',
        'description': 'Bhandardara Dam (Wilson Dam) on the Pravara River is one of the oldest dams in India, celebrated for its Umbrella Falls and the pristine Arthur Lake.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80'
    },

    # ------------------ VIDARBHA / NAGPUR ------------------
    'gosikhurd': {
        'taluka': 'Pauni', 'nearest_city': 'Bhandara / Nagpur', 'river': 'Wainganga',
        'year': 2008, 'height_m': 26.9, 'length_m': 11350,
        'purpose': 'National Irrigation Project irrigating Bhandara, Nagpur, and Chandrapur districts.',
        'description': 'Gosikhurd Dam (Indira Sagar) is an earthfill gravity dam on the Wainganga River. It is a National Irrigation Project designed to irrigate 2.5 lakh hectares in Vidarbha.',
        'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80'
    },
    'totladoh': {
        'taluka': 'Ramtek', 'nearest_city': 'Nagpur', 'river': 'Pench',
        'year': 1989, 'height_m': 74.5, 'length_m': 680,
        'purpose': 'Drinking water for Nagpur city, thermal power station supply, and Pench hydro power.',
        'description': 'Totladoh Dam is a gravity dam on the Pench River in Ramtek, located inside the scenic Pench National Park and Tiger Reserve, providing water to Nagpur city.',
        'image_url': 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80'
    },
    'upper-wardha': {
        'taluka': 'Morshi', 'nearest_city': 'Amravati', 'river': 'Wardha',
        'year': 1993, 'height_m': 46.2, 'length_m': 5920,
        'purpose': 'Nalinakshidevi Reservoir supplying drinking water to Amravati city and MIDC.',
        'description': 'Upper Wardha Dam is an earthfill and masonry dam on the Wardha River in Morshi, celebrated as the lifeline for agriculture in Amravati district.',
        'image_url': 'https://images.unsplash.com/photo-1542332213-31f87348057f?auto=format&fit=crop&w=1200&q=80'
    }
}

# Generic fallback attributes based on division & district
DIV_DEFAULTS = {
    'Pune': {
        'nearest_city': 'Pune', 'river': 'Krishna / Bhima Tributary',
        'purpose': 'Drinking water supply, irrigation, and hydroelectric generation in western Maharashtra.',
        'description': 'Major reservoir in the Krishna river basin, managed by the Water Resources Department of Maharashtra for regional irrigation and municipal water security.',
        'image_url': 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80'
    },
    'Kokan': {
        'nearest_city': 'Mumbai / Thane', 'river': 'West Flowing River',
        'purpose': 'Municipal drinking water supply for Mumbai Metropolitan Region and industrial use.',
        'description': 'Major reservoir situated in the Western Ghats coastal belt, capturing high monsoon runoff to supply metropolitan urban centers.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80'
    },
    'Nashik': {
        'nearest_city': 'Nashik', 'river': 'Godavari / Tapi Basin',
        'purpose': 'Irrigation, drinking water supply, and seasonal flood mitigation.',
        'description': 'Important irrigation storage project in northern Maharashtra, supporting agro-industries, grape cultivation, and regional municipal drinking networks.',
        'image_url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80'
    },
    'Chhatrapati Sambhajinagar': {
        'nearest_city': 'Chhatrapati Sambhajinagar', 'river': 'Godavari Sub-basin',
        'purpose': 'Irrigation for Marathwada agriculture and drinking water for urban towns.',
        'description': 'Vital water security reservoir in Marathwada, impounding seasonal flows for canal networks and groundwater recharge.',
        'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80'
    },
    'Amravati': {
        'nearest_city': 'Amravati', 'river': 'Wardha / Purna Basin',
        'purpose': 'Cotton-belt irrigation, flood moderation, and drinking water storage.',
        'description': 'Major water storage infrastructure in western Vidarbha, catering to the agricultural requirements of the Vidarbha agrarian region.',
        'image_url': 'https://images.unsplash.com/photo-1542332213-31f87348057f?auto=format&fit=crop&w=1200&q=80'
    },
    'Nagpur': {
        'nearest_city': 'Nagpur', 'river': 'Wainganga Basin',
        'purpose': 'Multi-purpose irrigation, industrial thermal plant supply, and municipal drinking water.',
        'description': 'Extensive reservoir in eastern Vidarbha, facilitating canal irrigation and drinking water supply across Nagpur revenue division.',
        'image_url': 'https://images.unsplash.com/photo-1439853949127-fa647821eea0?auto=format&fit=crop&w=1200&q=80'
    }
}

def enrich_all():
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    updated_count = 0
    for item in registry:
        slug = item['slug']
        div = item.get('division', 'Pune')
        dist = item.get('district', 'Pune')
        name = item.get('en', slug)

        meta = DAM_METADATA.get(slug, {})
        def_div = DIV_DEFAULTS.get(div, DIV_DEFAULTS['Pune'])

        taluka = meta.get('taluka', dist)
        nearest_city = meta.get('nearest_city', def_div['nearest_city'])
        river = meta.get('river', def_div['river'])
        year = meta.get('year', 1985)
        purpose = meta.get('purpose', def_div['purpose'])
        description = meta.get('description', f"{name} is a major storage reservoir situated in {dist} district, {div} revenue division. It is operated by the Maharashtra Water Resources Department to support regional irrigation and municipal water security.")
        image_url = meta.get('image_url', def_div['image_url'])
        height_m = meta.get('height_m', 45.0)
        length_m = meta.get('length_m', 1200.0)

        # Update JSON item
        item['taluka'] = taluka
        item['nearest_city'] = nearest_city
        item['river'] = river
        item['year'] = year
        item['purpose'] = purpose
        item['description'] = description
        item['image_url'] = image_url
        item['height_m'] = height_m
        item['length_m'] = length_m

        # Update SQLite table
        c.execute("""
            UPDATE dams SET
                taluka = ?, nearest_city = ?, river = ?, completion_year = ?,
                purpose = ?, description = ?, image_url = ?, height_m = ?, length_m = ?
            WHERE dam_slug = ?;
        """, (taluka, nearest_city, river, year, purpose, description, image_url, height_m, length_m, slug))
        updated_count += 1

    conn.commit()
    conn.close()

    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"✨ Successfully enriched metadata and image URLs for {updated_count} dams in SQLite and registry!")

if __name__ == '__main__':
    enrich_all()
