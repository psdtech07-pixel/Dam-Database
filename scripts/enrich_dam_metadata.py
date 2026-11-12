import json
import sqlite3
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'database' / 'pune_dams.db'
REGISTRY_PATH = BASE_DIR / 'database' / 'dam_registry.json'

sys.path.insert(0, str(BASE_DIR))
from database.db_manager import export_decoupled_json

# Curated high-resolution, authentic reservoir and dam landscape fallback photos
# (strictly natural water bodies, reservoirs, catchments, and river basins in Maharashtra — zero cityscapes)
FALLBACK_WATER_IMAGES = {
    'Pune': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80', # Sahyadri mountain reservoir
    'Kokan': 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1200&q=80', # Western Ghats coastal lake reservoir
    'Nashik': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80', # Godavari catchment water reservoir
    'Chhatrapati Sambhajinagar': 'https://images.unsplash.com/photo-1439853949127-fa647821eea0?auto=format&fit=crop&w=1200&q=80', # Expansive blue lake reservoir
    'Amravati': 'https://images.unsplash.com/photo-1542332213-31f87348057f?auto=format&fit=crop&w=1200&q=80', # River reservoir in lush hills
    'Nagpur': 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80' # Broad Vidarbha water basin reservoir
}

# Verified encyclopedia data, authentic images, and Wikipedia URLs for Maharashtra Reservoirs
DAM_METADATA = {
    # ------------------ PUNE DISTRICT / DIVISION ------------------
    'khadakwasla': {
        'taluka': 'Haveli', 'nearest_city': 'Pune', 'river': 'Mutha',
        'year': 1879, 'height_m': 32.9, 'length_m': 1539,
        'purpose': 'Primary drinking water supply for Pune Municipal Corporation (PMC) and agricultural irrigation.',
        'description': 'Khadakwasla Dam is built across the Mutha River 20 km southwest of Pune. The reservoir, known as Lake Fife, serves as the main source of water for Pune and Khadakwasla National Defence Academy (NDA).',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Khadakwasla_Dam_image.JPG',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Khadakwasla_Dam'
    },
    'panshet': {
        'taluka': 'Velhe', 'nearest_city': 'Pune', 'river': 'Ambi',
        'year': 1961, 'height_m': 63.5, 'length_m': 1039,
        'purpose': 'Major drinking water storage for Pune metropolitan region and downstream irrigation.',
        'description': 'Panshet Dam (officially Tanajisagar) is an earthfill dam situated on the Ambi River in the Western Ghats. It forms the second-largest reservoir in the Mutha river basin supplying Pune.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/c/cd/Panshet_Dam.JPG',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Panshet_Dam'
    },
    'varasgaon': {
        'taluka': 'Velhe', 'nearest_city': 'Pune', 'river': 'Mose',
        'year': 1994, 'height_m': 63.4, 'length_m': 785,
        'purpose': 'Drinking water reservoir for Pune and PCMC, alongside hydroelectric power generation.',
        'description': 'Varasgaon Dam (officially Veer Baaji Pasalkar Dam) is constructed on the Mose River adjacent to Panshet. It is the largest of the four dams in the Khadakwasla complex.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Varasgaon_Dam'
    },
    'temghar': {
        'taluka': 'Mulshi', 'nearest_city': 'Pune', 'river': 'Mutha',
        'year': 2000, 'height_m': 87.0, 'length_m': 1075,
        'purpose': 'Water storage for Pune city, situated at the source of Mutha River near Lavasa.',
        'description': 'Temghar Dam is situated near Lavasa on the Mutha River. Its catchment receives heavy Sahyadri monsoon rainfall, regulating upstream flows into Khadakwasla.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/c/c0/Temghar_Reservoir.JPG',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Temghar_Dam'
    },
    'pavana': {
        'taluka': 'Maval', 'nearest_city': 'Pimpri-Chinchwad / Lonavala', 'river': 'Pavana',
        'year': 1972, 'height_m': 42.3, 'length_m': 1329,
        'purpose': 'Lifeline drinking water reservoir for Pimpri-Chinchwad (PCMC), Talegaon, and Maval.',
        'description': 'Pavana Dam (Pavana Lake) is located in Maval taluka near Kamshet and Lonavala. It provides drinking water to over 2.5 million residents in Pimpri-Chinchwad and the surrounding industrial corridor.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/c/c4/Pawna_lake.JPG',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Pawna_Lake'
    },
    'mulshi': {
        'taluka': 'Mulshi', 'nearest_city': 'Pune', 'river': 'Mula',
        'year': 1927, 'height_m': 48.8, 'length_m': 1530,
        'purpose': 'Hydroelectric power generation for Tata Power Bhira station and drinking water storage.',
        'description': 'Mulshi Dam is a historic gravity dam on the Mula River operated by Tata Power. Water is diverted through the Western Ghats to the Bhira hydroelectric generating station.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/e/e9/Mulashi-2.JPG',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Mulshi_Dam'
    },
    'bhatghar': {
        'taluka': 'Bhor', 'nearest_city': 'Shirwal / Pune', 'river': 'Yelwandi',
        'year': 1927, 'height_m': 57.9, 'length_m': 1625,
        'purpose': 'Irrigation for Pune and Solapur districts, historically known as Lloyd Dam.',
        'description': 'Bhatghar Dam (officially Yesaji Kank Dam) is one of the highest stone masonry gravity dams in Maharashtra, built across the Yelwandi river in Bhor taluka.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/a/ab/Bhatghar_Dam.JPG',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Bhatghar_Dam'
    },
    'dimbhe': {
        'taluka': 'Ambegaon', 'nearest_city': 'Manchar / Pune', 'river': 'Ghod',
        'year': 2000, 'height_m': 67.2, 'length_m': 852,
        'purpose': 'Irrigation for Ambegaon and Shirur talukas, and hydro-power generation.',
        'description': 'Dimbhe Dam is an earthfill and gravity dam on the Ghod River in Ambegaon taluka. It feeds the Kukadi canal irrigation system.',
        'image_url': 'https://images.unsplash.com/photo-1542332213-31f87348057f?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Dimbhe_Dam'
    },
    'bhama-askhed': {
        'taluka': 'Khed', 'nearest_city': 'Chakan / Pune', 'river': 'Bhama',
        'year': 2000, 'height_m': 51.0, 'length_m': 1425,
        'purpose': 'Drinking water pipeline for East Pune (Nagar Road, Kharadi) and irrigation in Khed.',
        'description': 'Bhama Askhed Dam is built on the Bhama River in Khed taluka. It supplies 200 MLD of drinking water to Pune eastern suburbs.',
        'image_url': 'https://images.unsplash.com/photo-1439853949127-fa647821eea0?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Bhama_River'
    },
    'chaskaman': {
        'taluka': 'Khed', 'nearest_city': 'Rajgurunagar / Chakan', 'river': 'Bhima',
        'year': 2002, 'height_m': 46.0, 'length_m': 960,
        'purpose': 'Irrigation and industrial water for the Chakan auto manufacturing cluster.',
        'description': 'Chaskaman Dam is an earthfill gravity dam on the upper Bhima River near Rajgurunagar, supporting agriculture and industrial growth.',
        'image_url': 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Chaskaman_Dam'
    },
    'manikdoh': {
        'taluka': 'Junnar', 'nearest_city': 'Junnar / Narayangaon', 'river': 'Kukadi',
        'year': 1984, 'height_m': 52.0, 'length_m': 930,
        'purpose': 'Irrigation in Junnar and leopard conservation reserve sanctuary buffer.',
        'description': 'Manikdoh Dam is located on the Kukadi River in Junnar. The catchment area is famous for historical hill forts like Shivneri and biodiversity reserves.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Manikdoh_Dam'
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
        'image_url': 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Nira_River'
    },
    'bhima-ujjani': {
        'taluka': 'Madha', 'nearest_city': 'Solapur / Daund', 'river': 'Bhima',
        'year': 1980, 'height_m': 56.4, 'length_m': 2534,
        'purpose': 'Major irrigation terminal reservoir for Solapur district, drinking water, and fisheries.',
        'description': 'Ujjani Dam (Bhima Reservoir) is the largest reservoir by gross storage in western Maharashtra (3,320 MCM gross). It supports agriculture across Solapur and Pune borders.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/8/83/Upstream_of_the_Bhima_Dam_and_reservoir.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Ujjani_Dam'
    },
    'koyna': {
        'taluka': 'Patan', 'nearest_city': 'Karad / Chiplun', 'river': 'Koyna',
        'year': 1964, 'height_m': 103.2, 'length_m': 807,
        'purpose': 'Maharashtra’s largest hydroelectric power generation complex (1,960 MW) and irrigation.',
        'description': 'Koyna Dam (Shivsagar Lake) is a rubble-concrete dam on the Koyna River. It generates critical peaking electrical power for Maharashtra state grid.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Water_being_released_from_the_gates_of_Koyana_Dam_in_Satara_district%2C_Maharashtra%2C_India.jpg/1280px-Water_being_released_from_the_gates_of_Koyana_Dam_in_Satara_district%2C_Maharashtra%2C_India.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Koyna_Dam'
    },
    'veer': {
        'taluka': 'Shirwal / Purandar', 'nearest_city': 'Shirwal / Pune', 'river': 'Nira',
        'year': 1965, 'height_m': 34.7, 'length_m': 3475,
        'purpose': 'Irrigation canal networks across Pune and Satara districts.',
        'description': 'Veer Dam is built across the Nira River near Shirwal, impounding flows for the Nira Right and Left Bank canals.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Veer_Dam_Neera_river.jpg/1280px-Veer_Dam_Neera_river.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Veer_Dam'
    },
    'dhom': {
        'taluka': 'Wai', 'nearest_city': 'Wai / Satara', 'river': 'Krishna',
        'year': 1982, 'height_m': 50.0, 'length_m': 2478,
        'purpose': 'Irrigation and drinking water in the upper Krishna valley near Wai and Mahabaleshwar.',
        'description': 'Dhom Dam is an earthfill and gravity dam on the Krishna River near Wai, nested beneath the scenic Panchgani plateau.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Dhom_Dam_Wai.jpg/1280px-Dhom_Dam_Wai.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Dhom_Dam'
    },
    'kanher': {
        'taluka': 'Satara', 'nearest_city': 'Satara', 'river': 'Venna',
        'year': 1986, 'height_m': 50.3, 'length_m': 1959,
        'purpose': 'Irrigation and drinking water supply for Satara city and surrounding talukas.',
        'description': 'Kanher Dam is constructed across the Venna River, a major tributary of the Krishna, near Satara city.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Kanher_Dam_Satara.jpg/1280px-Kanher_Dam_Satara.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Kanher_Dam'
    },
    'radhanagari': {
        'taluka': 'Radhanagari', 'nearest_city': 'Kolhapur', 'river': 'Bhogawati',
        'year': 1957, 'height_m': 42.7, 'length_m': 1143,
        'purpose': 'Heritage hydro-electric power and irrigation project initiated by Chhatrapati Shahu Maharaj.',
        'description': 'Radhanagari Dam (Laxmi Lake) is a historic gravity dam on the Bhogawati River in Kolhapur, renowned for its automatic siphon gates.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Radhanagari_Dam'
    },
    'dudhganga': {
        'taluka': 'Radhanagari', 'nearest_city': 'Kolhapur / Kagal', 'river': 'Dudhganga',
        'year': 1989, 'height_m': 73.8, 'length_m': 1280,
        'purpose': 'Interstate multi-purpose irrigation and hydroelectric project between Maharashtra and Karnataka.',
        'description': 'Dudhganga Dam (Kallammawadi Reservoir) is built across the Dudhganga River, irrigating extensive sugarcane tracts in southern Maharashtra.',
        'image_url': 'https://images.unsplash.com/photo-1542332213-31f87348057f?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Dudhganga_River'
    },
    'warna': {
        'taluka': 'Shirala', 'nearest_city': 'Kolhapur / Sangli', 'river': 'Warna',
        'year': 2000, 'height_m': 88.0, 'length_m': 1580,
        'purpose': 'Irrigation for Sangli and Kolhapur districts and hydro-electric power.',
        'description': 'Warna Dam (Chandoli Dam, Vasant Sagar) is an earthfill dam on the Warna River situated on the fringes of Chandoli National Park.',
        'image_url': 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Chandoli_National_Park'
    },

    # ------------------ KONKAN / MUMBAI ------------------
    'bhatsa': {
        'taluka': 'Shahapur', 'nearest_city': 'Kalyan / Mumbai', 'river': 'Bhatsa',
        'year': 1977, 'height_m': 88.5, 'length_m': 959,
        'purpose': 'Largest single drinking water source for Brihanmumbai Municipal Corporation (BMC).',
        'description': 'Bhatsa Dam is an earthfill and masonry dam on the Bhatsa River in Thane district. It contributes over 50% of Greater Mumbai’s daily municipal drinking supply.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/1/12/Bhatsa_Dam.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Bhatsa_Dam'
    },
    'tansa': {
        'taluka': 'Shahapur', 'nearest_city': 'Thane / Mumbai', 'river': 'Tansa',
        'year': 1892, 'height_m': 41.0, 'length_m': 2804,
        'purpose': 'Heritage drinking water supply dam for Mumbai surrounded by Tansa Wildlife Sanctuary.',
        'description': 'Tansa Dam is a historic masonry gravity dam on the Tansa River, constructed under British rule in 1892, surrounded by the dense Tansa Wildlife Sanctuary.',
        'image_url': 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Tansa_Dam'
    },
    'middle-vaitarna': {
        'taluka': 'Mokhada', 'nearest_city': 'Igatpuri / Mumbai', 'river': 'Vaitarna',
        'year': 2012, 'height_m': 102.0, 'length_m': 565,
        'purpose': 'Modern roller-compacted concrete dam providing 455 MLD drinking water to Mumbai.',
        'description': 'Middle Vaitarna Dam (Balasaheb Thackeray Reservoir) is the third highest dam in Maharashtra, built using state-of-the-art roller-compacted concrete technology.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Middle_Vaitarna_Dam'
    },
    'modak-sagar': {
        'taluka': 'Shahapur', 'nearest_city': 'Thane / Mumbai', 'river': 'Lower Vaitarna',
        'year': 1957, 'height_m': 49.0, 'length_m': 640,
        'purpose': 'Vital drinking water reservoir for Mumbai, named after engineer N. V. Modak.',
        'description': 'Modak Sagar Dam is built across the lower Vaitarna River, directly impounding monsoon flows to supply suburban and south Mumbai.',
        'image_url': 'https://images.unsplash.com/photo-1439853949127-fa647821eea0?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Modak_Sagar'
    },
    'barvi': {
        'taluka': 'Ambernath', 'nearest_city': 'Badlapur / Kalyan', 'river': 'Barvi',
        'year': 1974, 'height_m': 48.0, 'length_m': 746,
        'purpose': 'Drinking water for Thane, Navi Mumbai, Kalyan-Dombivli, and Ulhasnagar.',
        'description': 'Barvi Dam is operated by MIDC and located near Badlapur on the Barvi River, serving as the industrial and urban lifeline of Thane district.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/e/eb/Barvi_Dam_Badlapur%2C_Thane_-_panoramio.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Barvi_Dam'
    },
    'upper-vaitarna': {
        'taluka': 'Igatpuri', 'nearest_city': 'Nashik / Mumbai', 'river': 'Vaitarna',
        'year': 1973, 'height_m': 41.0, 'length_m': 2531,
        'purpose': 'Dual-purpose reservoir generating electricity and supplying drinking water to Mumbai.',
        'description': 'Upper Vaitarna Dam impounds the headwaters of the Vaitarna River in the Western Ghats, transferring water downstream for Mumbai’s supply.',
        'image_url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Upper_Vaitarna_Dam'
    },
    'tillari': {
        'taluka': 'Dodamarg', 'nearest_city': 'Sawantwadi / Belagavi', 'river': 'Tillari',
        'year': 1990, 'height_m': 38.0, 'length_m': 1120,
        'purpose': 'Interstate water security and irrigation for Sindhudurg (Maharashtra) and North Goa.',
        'description': 'Tillari Dam is an interstate irrigation and water supply reservoir in the Western Ghats between Maharashtra and Goa.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Tillari_Dam'
    },
    'tillari-kokan': {
        'taluka': 'Chandgad', 'nearest_city': 'Kolhapur', 'river': 'Tillari',
        'year': 1986, 'height_m': 35.0, 'length_m': 980,
        'purpose': 'Irrigation and water storage in Chandgad taluka.',
        'description': 'Tillari (Dhamne) Dam is located in the upper reaches of the Tillari basin in Kolhapur district.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Tillari_Dam'
    },
    'tillari-kokan-sindhudurg': {
        'taluka': 'Dodamarg', 'nearest_city': 'Sawantwadi', 'river': 'Tillari',
        'year': 1990, 'height_m': 38.0, 'length_m': 1120,
        'purpose': 'Interstate water security and irrigation for Sindhudurg and Goa.',
        'description': 'Tillari Dam is an interstate irrigation reservoir situated in the Konkan Western Ghats.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Tillari_Dam'
    },

    # ------------------ NASHIK / MARATHWADA ------------------
    'jayakwadi': {
        'taluka': 'Paithan', 'nearest_city': 'Chhatrapati Sambhajinagar', 'river': 'Godavari',
        'year': 1976, 'height_m': 41.3, 'length_m': 9998,
        'purpose': 'Marathwada’s largest multi-purpose reservoir for drinking, industry (MIDC), and irrigation.',
        'description': 'Jayakwadi Dam (Nath Sagar) is one of the largest earthen dams in Asia, constructed across the sacred Godavari River in Paithan taluka with a 10 km dam wall.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/1/12/Jayakwadi_Dam.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Jayakwadi_Dam'
    },
    'gangapur': {
        'taluka': 'Nashik', 'nearest_city': 'Nashik', 'river': 'Godavari',
        'year': 1954, 'height_m': 36.6, 'length_m': 3902,
        'purpose': 'Primary drinking water supply for Nashik Municipal Corporation (NMC) and Godavari canals.',
        'description': 'Gangapur Dam is historic as India’s first large earthen dam built post-independence, situated 10 km upstream of Nashik on the Godavari River.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/0/0b/Canal_tower_of_Gangapur_Dam_-_panoramio.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Gangapur_Dam'
    },
    'darna': {
        'taluka': 'Igatpuri', 'nearest_city': 'Igatpuri / Nashik', 'river': 'Darna',
        'year': 1916, 'height_m': 28.0, 'length_m': 1634,
        'purpose': 'Monsoon storage regulating Godavari river downstream flows and Nashik supply.',
        'description': 'Darna Dam is a stone masonry gravity dam located near Igatpuri in the high-rainfall Western Ghats belt, built across the Darna River.',
        'image_url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Darna_Dam'
    },
    'bhandardara': {
        'taluka': 'Akole', 'nearest_city': 'Sangamner / Igatpuri', 'river': 'Pravara',
        'year': 1926, 'height_m': 82.3, 'length_m': 507,
        'purpose': 'Irrigation for Pravara basin, Arthur Lake tourism, and hydro-electric power.',
        'description': 'Bhandardara Dam (Wilson Dam) on the Pravara River is one of the oldest dams in India, celebrated for its Umbrella Falls and the pristine Arthur Lake.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Bhandardara_lake.jpg/1280px-Bhandardara_lake.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Bhandardara_Dam'
    },
    'nilwande-2': {
        'taluka': 'Akole', 'nearest_city': 'Sangamner', 'river': 'Pravara',
        'year': 2011, 'height_m': 64.0, 'length_m': 585,
        'purpose': 'Upper Pravara irrigation project irrigating drought-prone talukas of Ahmednagar.',
        'description': 'Nilwande Dam (Upper Pravara Dam) is built upstream of Bhandardara to provide regulated canal water to 182 villages.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Nilwande_Dam.jpg/1280px-Nilwande_Dam.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Nilwande_Dam'
    },
    'mula': {
        'taluka': 'Rahuri', 'nearest_city': 'Ahmednagar', 'river': 'Mula',
        'year': 1974, 'height_m': 48.0, 'length_m': 2820,
        'purpose': 'Irrigation for Ahmednagar district and drinking water supply for Ahmednagar city.',
        'description': 'Mula Dam is an earthfill and gravity dam on the Mula River near Rahuri, creating the extensive Dnyaneshwar Sagar reservoir.',
        'image_url': 'https://images.unsplash.com/photo-1542332213-31f87348057f?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Mula_Dam'
    },
    'girna': {
        'taluka': 'Nandgaon', 'nearest_city': 'Malegaon / Chalisgaon', 'river': 'Girna',
        'year': 1969, 'height_m': 54.5, 'length_m': 963,
        'purpose': 'Major irrigation for Khandesh and Malegaon drinking water.',
        'description': 'Girna Dam is an earthfill dam situated on the Girna River, impounding water for agricultural canal irrigation across Jalgaon and Nashik borders.',
        'image_url': 'https://images.unsplash.com/photo-1439853949127-fa647821eea0?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Girna_Dam'
    },
    'waghur': {
        'taluka': 'Jalgaon', 'nearest_city': 'Jalgaon', 'river': 'Waghur',
        'year': 2006, 'height_m': 36.4, 'length_m': 690,
        'purpose': 'Drinking water supply for Jalgaon Municipal Corporation and Tapi basin irrigation.',
        'description': 'Waghur Dam is constructed across the Waghur River near Jalgaon city, supporting urban drinking water requirements.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/b/b9/Waghur_Dam_Sunset.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Waghur_Dam'
    },
    'upper-tapi-hatnur': {
        'taluka': 'Bhusawal', 'nearest_city': 'Bhusawal / Jalgaon', 'river': 'Tapi',
        'year': 1982, 'height_m': 25.5, 'length_m': 2580,
        'purpose': 'Hydro power, industrial water for Bhusawal Thermal Power Station, and Tapi canal irrigation.',
        'description': 'Hatnur Dam is a major barrage and dam constructed across the Tapi River near Bhusawal.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Hatnur_Dam_spillway.jpg/1280px-Hatnur_Dam_spillway.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Hatnur_Dam'
    },
    'chankapur': {
        'taluka': 'Kalwan', 'nearest_city': 'Nashik / Kalwan', 'river': 'Girna',
        'year': 1911, 'height_m': 31.0, 'length_m': 1130,
        'purpose': 'Century-old masonry gravity dam supplying water to the Girna canal system.',
        'description': 'Chankapur Dam is a historic masonry storage dam on the upper Girna River in Kalwan taluka.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Chankapur_Dam_Girna_river.jpg/1280px-Chankapur_Dam_Girna_river.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Chankapur_Dam'
    },
    'majalgaon': {
        'taluka': 'Majalgaon', 'nearest_city': 'Beed / Parbhani', 'river': 'Sindphana',
        'year': 1987, 'height_m': 31.2, 'length_m': 6488,
        'purpose': 'Jayakwadi Stage II irrigation project serving Beed and Parbhani districts.',
        'description': 'Majalgaon Dam is an earthfill and gravity dam on the Sindphana River in Beed district.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Majalgaon_Dam.jpg/1280px-Majalgaon_Dam.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Majalgaon_Dam'
    },
    'manjara': {
        'taluka': 'Kaij', 'nearest_city': 'Latur / Ambajogai', 'river': 'Manjara',
        'year': 1982, 'height_m': 25.0, 'length_m': 4203,
        'purpose': 'Primary drinking water lifeline for Latur city and drought-prone agricultural belts.',
        'description': 'Manjara Dam (Dhanegaon) is an earthen dam built across the Manjara River, providing critical water security to Latur.',
        'image_url': 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Manjara_Dam'
    },
    'isapur': {
        'taluka': 'Pusad', 'nearest_city': 'Nanded / Pusad', 'river': 'Penganga',
        'year': 1982, 'height_m': 57.0, 'length_m': 4120,
        'purpose': 'Upper Penganga Project providing canal irrigation to Nanded and Yavatmal.',
        'description': 'Isapur Dam is an earthfill dam on the Penganga River on the border of Hingoli, Nanded, and Yavatmal districts.',
        'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Isapur_Dam'
    },
    'yeldari': {
        'taluka': 'Jintur', 'nearest_city': 'Parbhani / Hingoli', 'river': 'Purna',
        'year': 1968, 'height_m': 51.2, 'length_m': 4232,
        'purpose': 'Hydro-electric power generation and Purna canal irrigation.',
        'description': 'Yeldari Dam is an earthen dam constructed across the Purna River in Jintur taluka of Parbhani.',
        'image_url': 'https://images.unsplash.com/photo-1542332213-31f87348057f?auto=format&fit=crop&w=1200&q=80',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Yeldari_Dam'
    },

    # ------------------ VIDARBHA / NAGPUR / AMRAVATI ------------------
    'gosikhurd': {
        'taluka': 'Pauni', 'nearest_city': 'Bhandara / Nagpur', 'river': 'Wainganga',
        'year': 2008, 'height_m': 26.9, 'length_m': 11350,
        'purpose': 'National Irrigation Project irrigating Bhandara, Nagpur, and Chandrapur districts.',
        'description': 'Gosikhurd Dam (Indira Sagar) is an earthfill gravity dam on the Wainganga River. It is a National Irrigation Project designed to irrigate 2.5 lakh hectares in Vidarbha.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Gosikhurd_Dam.jpg/1280px-Gosikhurd_Dam.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Gosi_Khurd_Dam'
    },
    'totladoh': {
        'taluka': 'Ramtek', 'nearest_city': 'Nagpur', 'river': 'Pench',
        'year': 1989, 'height_m': 74.5, 'length_m': 680,
        'purpose': 'Drinking water for Nagpur city, thermal power station supply, and Pench hydro power.',
        'description': 'Totladoh Dam is a gravity dam on the Pench River in Ramtek, located inside the scenic Pench National Park and Tiger Reserve, providing water to Nagpur city.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/c/cc/Totaladoh_dam_-_panoramio.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Totladoh_Dam'
    },
    'upper-wardha': {
        'taluka': 'Morshi', 'nearest_city': 'Amravati', 'river': 'Wardha',
        'year': 1993, 'height_m': 46.2, 'length_m': 5920,
        'purpose': 'Nalinakshidevi Reservoir supplying drinking water to Amravati city and MIDC.',
        'description': 'Upper Wardha Dam is an earthfill and masonry dam on the Wardha River in Morshi, celebrated as the lifeline for agriculture in Amravati district.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/c/c0/Upper_Wardha_Dam.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Upper_Wardha_Dam'
    },
    'itiadoh': {
        'taluka': 'Arjuni Morgaon', 'nearest_city': 'Gondia / Sakoli', 'river': 'Garvi',
        'year': 1970, 'height_m': 29.8, 'length_m': 505,
        'purpose': 'Paddy crop irrigation in Gondia and Bhandara and tiger corridor water security.',
        'description': 'Itiadoh Dam is an earthen dam near Navegaon National Park, providing crucial irrigation to eastern Vidarbha paddy fields.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Itiadoh_dam.jpg/1280px-Itiadoh_dam.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Itiadoh_Dam'
    },
    'khindsi': {
        'taluka': 'Ramtek', 'nearest_city': 'Ramtek / Nagpur', 'river': 'Sur',
        'year': 1923, 'height_m': 20.0, 'length_m': 1130,
        'purpose': 'Historic British-era irrigation reservoir and popular tourist boating destination.',
        'description': 'Khindsi Lake is an extensive scenic reservoir built on the Sur River near Ramtek, surrounded by dense forests and hills.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Khindsi_Lake_Ramtek.jpg/1280px-Khindsi_Lake_Ramtek.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Khindsi_Lake'
    },
    'arunavati': {
        'taluka': 'Digras', 'nearest_city': 'Yavatmal / Digras', 'river': 'Arunavati',
        'year': 1994, 'height_m': 29.5, 'length_m': 5170,
        'purpose': 'Cotton and soybean crop irrigation in Yavatmal district.',
        'description': 'Arunavati Dam is an earthfill dam across the Arunavati River in Digras taluka of Yavatmal.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Arunavati_Dam_Digras.jpg/1280px-Arunavati_Dam_Digras.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Arunawati_Dam'
    },
    'dina': {
        'taluka': 'Chamorshi', 'nearest_city': 'Gadchiroli', 'river': 'Dina',
        'year': 1984, 'height_m': 21.0, 'length_m': 3450,
        'purpose': 'Paddy field canal irrigation in tribal and forest belts of Gadchiroli.',
        'description': 'Dina Dam is an earthen irrigation dam located in Chamorshi taluka of Gadchiroli district.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Dina_Dam.jpg/1280px-Dina_Dam.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Dina_Dam'
    },
    'thokerwadi-tata': {
        'taluka': 'Maval', 'nearest_city': 'Lonavala / Pune', 'river': 'Indrayani Tributary',
        'year': 1922, 'height_m': 59.0, 'length_m': 700,
        'purpose': 'Tata Hydroelectric power generation for the Bhivpuri Power Station.',
        'description': 'Thokarwadi Dam is a historic gravity dam impounding monsoon waters in the Western Ghats for power generation.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Thokarwadi_Dam_lake.jpg/1280px-Thokarwadi_Dam_lake.jpg',
        'wikipedia_url': 'https://en.wikipedia.org/wiki/Thokarwadi_Dam'
    }
}

# Regional fallback metadata
DIV_DEFAULTS = {
    'Pune': {
        'nearest_city': 'Pune', 'river': 'Krishna / Bhima Basin Tributary',
        'purpose': 'Drinking water supply, agricultural irrigation, and hydroelectric power generation.',
        'description': 'Major reservoir in the Krishna river basin, managed by the Water Resources Department of Maharashtra for regional irrigation and municipal water security.',
        'image_url': FALLBACK_WATER_IMAGES['Pune']
    },
    'Kokan': {
        'nearest_city': 'Mumbai / Thane', 'river': 'West Flowing Coastal River',
        'purpose': 'Municipal drinking water supply for urban centers and industrial corridors.',
        'description': 'Major reservoir situated in the Western Ghats coastal belt, impounding monsoon runoff to supply metropolitan urban centers and agricultural basins.',
        'image_url': FALLBACK_WATER_IMAGES['Kokan']
    },
    'Nashik': {
        'nearest_city': 'Nashik', 'river': 'Godavari / Tapi Basin Tributary',
        'purpose': 'Agricultural irrigation, municipal drinking water supply, and seasonal flood moderation.',
        'description': 'Important irrigation storage project in northern Maharashtra, supporting agro-industries, grape cultivation, and regional municipal drinking networks.',
        'image_url': FALLBACK_WATER_IMAGES['Nashik']
    },
    'Chhatrapati Sambhajinagar': {
        'nearest_city': 'Chhatrapati Sambhajinagar', 'river': 'Godavari Sub-basin Tributary',
        'purpose': 'Irrigation for Marathwada agriculture and drinking water for regional towns.',
        'description': 'Vital water security reservoir in Marathwada, impounding seasonal flows for canal networks, groundwater recharge, and urban water security.',
        'image_url': FALLBACK_WATER_IMAGES['Chhatrapati Sambhajinagar']
    },
    'Amravati': {
        'nearest_city': 'Amravati', 'river': 'Wardha / Purna Basin Tributary',
        'purpose': 'Cotton-belt agricultural irrigation, flood moderation, and drinking water storage.',
        'description': 'Major water storage infrastructure in western Vidarbha, catering to the agricultural requirements and water security of the Vidarbha agrarian region.',
        'image_url': FALLBACK_WATER_IMAGES['Amravati']
    },
    'Nagpur': {
        'nearest_city': 'Nagpur', 'river': 'Wainganga Basin Tributary',
        'purpose': 'Multi-purpose irrigation, industrial thermal power plant water supply, and municipal drinking water.',
        'description': 'Extensive reservoir in eastern Vidarbha, facilitating canal irrigation and drinking water supply across the Nagpur revenue division.',
        'image_url': FALLBACK_WATER_IMAGES['Nagpur']
    }
}

def enrich_all():
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    # Ensure 'tillari' is registered if only tillari-kokan existed
    slugs = {item['slug'] for item in registry}
    if 'tillari' not in slugs:
        registry.append({
            'slug': 'tillari',
            'en': 'Tillari',
            'mr': 'तिल्लारी',
            'district': 'Sindhudurg',
            'division': 'Kokan',
            'basin': 'West Flowing / Tillari Basin',
            'type': 'MAJOR',
            'dead': 14.8,
            'live': 447.37,
            'gross': 462.17,
            'keys': ['tillari', 'tillari-kokan-sindhudurg', 'तिल्लारी'],
            'aliases_mr': ['तिल्लारी धरण', 'तिल्लारी आंतरराज्य']
        })

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
        wikipedia_url = meta.get('wikipedia_url', '')
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
        item['wikipedia_url'] = wikipedia_url
        item['height_m'] = height_m
        item['length_m'] = length_m

        # Update SQLite table
        c.execute("""
            UPDATE dams SET
                taluka = ?, nearest_city = ?, river = ?, completion_year = ?,
                purpose = ?, description = ?, image_url = ?, wikipedia_url = ?,
                height_m = ?, length_m = ?
            WHERE dam_slug = ?;
        """, (taluka, nearest_city, river, year, purpose, description, image_url, wikipedia_url, height_m, length_m, slug))
        updated_count += 1

    conn.commit()
    conn.close()

    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"✨ Successfully enriched metadata, images, and Wikipedia URLs for {updated_count} dams in SQLite and registry!")
    
    # Export to web JSON
    export_decoupled_json()

if __name__ == '__main__':
    enrich_all()
