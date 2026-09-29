"""Comprehensive seed script for crags and routes across Germany, Austria, Switzerland, and France."""
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-689eef206658"

CRAGS = [
    # ==========================
    # GERMANY
    # ==========================
    {
        "id": "frankenjura-krottensee",
        "name": "Frankenjura - Krottenseer Forst",
        "country": "Germany",
        "region": "Bavaria",
        "location": "Betzenstein, Bavaria, Germany",
        "disciplines": ["sport climbing"],
        "description": "The cradle of modern hard sport climbing nestled in Bavarian beech forests. Known for steep limestone pockets, sharp mono/two-finger pockets, and powerful short cruxes.",
        "grade_range": "6a - 9a / 5.10a - 5.14d",
        "routes": [
            {"name": "Action Directe", "grade": "9a (5.14d)", "type": "sport", "pitches": 1, "description": "The world's first 9a put up by Wolfgang Güllich. Steep 45-degree overhang on dynamic finger pockets."},
            {"name": "Wallstreet", "grade": "8c (5.14b)", "type": "sport", "pitches": 1, "description": "Historical testpiece featuring razor crimps and sharp pockets on Krottenseer Turm."},
            {"name": "Sautanz", "grade": "6b+ (5.10d)", "type": "sport", "pitches": 1, "description": "Classic pocketed face climbing with excellent friction."}
        ],
        "accommodations": [
            {"name": "Gasthof Zur Post Betzenstein", "type": "hotel", "distance_miles": 3.0, "notes": "Traditional Bavarian inn serving hearty food and local beer."},
            {"name": "Campingplatz Bärenschlucht", "type": "campsite", "distance_miles": 5.5, "notes": "Scenic riverside campground popular with international climbers."}
        ]
    },
    {
        "id": "pfalz-buntsandstein",
        "name": "Palatinate (Pfalz) - Dahner Felsenland",
        "country": "Germany",
        "region": "Rhineland-Palatinate",
        "location": "Dahn, Rhineland-Palatinate, Germany",
        "disciplines": ["trad climbing", "sport climbing"],
        "description": "Dramatic red bunter sandstone towers rising out of the Palatinate Forest. Renowned for strict ground-up ethics, ring-bolt protection, slopers, and honeycombed sandstone.",
        "grade_range": "5a - 8b / 5.7 - 5.13d",
        "routes": [
            {"name": "Teufelstisch Südkante", "grade": "6a (5.10a)", "type": "trad", "pitches": 2, "description": "Iconic pillar climb with exposure and sandstone slopers."},
            {"name": "Flug des Bussards", "grade": "7b (5.12b)", "type": "trad/sport", "pitches": 1, "description": "Steep arete on honeycombed ironstone bands."}
        ],
        "accommodations": [
            {"name": "Camping Neudahner Weiher", "type": "campsite", "distance_miles": 2.0, "notes": "Lakeside camping under sandstone spires."},
            {"name": "Felsenland Gasthof Dahn", "type": "hotel", "distance_miles": 1.5, "notes": "Cozy rooms with sauna and climber breakfast."}
        ]
    },
    {
        "id": "elbsandstein-saxony",
        "name": "Saxon Switzerland (Elbsandstein)",
        "country": "Germany",
        "region": "Saxony",
        "location": "Bad Schandau, Saxony, Germany",
        "disciplines": ["trad climbing"],
        "description": "Ancient sandstone towers along the Elbe River canyon. Pure traditional ground-up climbing with strict conservation ethics: no chalk, no metal cams/nuts, only knotted slings.",
        "grade_range": "IV - XII / 5.5 - 5.14c",
        "routes": [
            {"name": "Barbarine Westwand", "grade": "VI (5.8)", "type": "trad", "pitches": 3, "description": "Historic line up one of the most famous freestanding rock towers in Europe."},
            {"name": "Talweg (Falkenstein)", "grade": "VIIa (5.10a)", "type": "trad", "pitches": 5, "description": "Classic multi-pitch chimney and corner ascent of the Falkenstein giant monolith."}
        ],
        "accommodations": [
            {"name": "Camping Ostrauer Mühle", "type": "campsite", "distance_miles": 2.0, "notes": "Traditional climber base in the Kirnitzschtal valley."},
            {"name": "Parkhotel Bad Schandau", "type": "hotel", "distance_miles": 3.0, "notes": "Comfortable spa hotel on the Elbe River."}
        ]
    },
    {
        "id": "kochel-bavaria",
        "name": "Kochel am See",
        "country": "Germany",
        "region": "Bavaria",
        "location": "Kochel am See, Upper Bavaria, Germany",
        "disciplines": ["sport climbing"],
        "description": "Steep limestone crags nestled directly above Lake Kochel in the Bavarian Alpine foothills. Famous for pumpy overhanging walls, tufas, and sustained power-endurance testpieces.",
        "grade_range": "6b - 9a / 5.10d - 5.14d",
        "routes": [
            {"name": "Weisse Rose", "grade": "8c+ (5.14c)", "type": "sport", "pitches": 1, "description": "Historic Toni Lamprecht line on steep grey water-washed limestone."},
            {"name": "Kochel Kante", "grade": "6c (5.11b)", "type": "sport", "pitches": 1, "description": "Aesthetic exposed arete with panoramic lake views."}
        ],
        "accommodations": [
            {"name": "Campingplatz Kesselberg", "type": "campsite", "distance_miles": 1.5, "notes": "Directly on Lake Kochel, great for swimming after climbing."},
            {"name": "Seehotel Grauer Bär", "type": "hotel", "distance_miles": 2.0, "notes": "Lakeside terrace hotel with Bavarian food."}
        ]
    },
    {
        "id": "battert-baden",
        "name": "Battert Felsen - Black Forest",
        "country": "Germany",
        "region": "Baden-Württemberg",
        "location": "Baden-Baden, Black Forest, Germany",
        "disciplines": ["trad climbing", "sport climbing"],
        "description": "Historic volcanic quartz-porphyry rock needles and walls perched above the spa city of Baden-Baden. Classic technical climbing with solid gear placement and scenic forest towers.",
        "grade_range": "4a - 8a / 5.5 - 5.13b",
        "routes": [
            {"name": "Falkenwand Kuhweg", "grade": "5c (5.9)", "type": "trad", "pitches": 2, "description": "Classic friction slab and crack line on clean volcanic stone."},
            {"name": "Badener Wand Schwarze Kante", "grade": "6b (5.10d)", "type": "trad", "pitches": 2, "description": "Exposed arete climbing above the trees."}
        ],
        "accommodations": [
            {"name": "Naturfreundehaus Baden-Baden", "type": "hostel/lodge", "distance_miles": 0.8, "notes": "Rustic alpine-style lodge directly adjacent to the approach trail."},
            {"name": "Hotel Magnetberg", "type": "hotel", "distance_miles": 2.5, "notes": "Thermal spa hotel overlooking the hills."}
        ]
    },
    {
        "id": "allgaeu-kempten",
        "name": "Allgäu Limestone (Rottachberg & Tiefenbach)",
        "country": "Germany",
        "region": "Bavaria",
        "location": "Oberstdorf / Kempten, Allgäu Alps, Germany",
        "disciplines": ["sport climbing", "bouldering"],
        "description": "Lush alpine limestone valley offering athletic pocket pulling, conglomerates, and high-quality crags facing all aspects amidst idyllic Bavarian meadow backdrops.",
        "grade_range": "5c - 8c+ / 5.9 - 5.14c",
        "routes": [
            {"name": "Rottachberg Himmelsleiter", "grade": "7a+ (5.12a)", "type": "sport", "pitches": 1, "description": "Sustained steep pocket climbing on immaculate grey limestone."},
            {"name": "Tiefenbach Wasserfallwand", "grade": "6c (5.11a)", "type": "sport", "pitches": 1, "description": "Cool summer crag climbing beside a cascading mountain creek."}
        ],
        "accommodations": [
            {"name": "Camping Oberstdorf", "type": "campsite", "distance_miles": 3.0, "notes": "Alpine valley camping with mountain view pitches."},
            {"name": "Alpenhotel Tiefenbach", "type": "hotel", "distance_miles": 1.2, "notes": "Traditional Alpine hotel right near the gorges."}
        ]
    },

    # ==========================
    # AUSTRIA
    # ==========================
    {
        "id": "zillertal-ewige-jagdgfrunde",
        "name": "Zillertal - Ewige Jagdgründe",
        "country": "Austria",
        "region": "Tyrol",
        "location": "Ginzling, Tyrol, Austria",
        "disciplines": ["sport climbing", "bouldering"],
        "description": "Towering high-friction granite blocks and cliffs set along a glacier-fed alpine river in Tyrol. Renowned for slopers, crimp edges, and breathtaking alpine atmosphere.",
        "grade_range": "5c - 9a+ / 5.9 - 5.15a",
        "routes": [
            {"name": "Schwarzer Peter", "grade": "7a (5.11d)", "type": "sport", "pitches": 1, "description": "Classic high-friction granite face on the Wig/Wam towers."},
            {"name": "The Flame", "grade": "9a+ (5.15a)", "type": "sport", "pitches": 1, "description": "World-famous endurance testpiece bolted by Jörg Verhoeven, FA by Jakob Schubert."},
            {"name": "Marmotta Bouldering Sector", "grade": "V4 - V12", "type": "boulder", "pitches": 1, "description": "Gneiss/granite blocks scattered along the riverbank."}
        ],
        "accommodations": [
            {"name": "Gasthof Karlsteg", "type": "inn/apartment", "distance_miles": 1.5, "notes": "Historic Tyrolean inn minutes from the crag."},
            {"name": "Camping Mayrhofen", "type": "campsite", "distance_miles": 6.0, "notes": "Full-facility campground with pool, gear stores, and train access."}
        ]
    },
    {
        "id": "wilder-kaiser",
        "name": "Wilder Kaiser - Fleischbank & Totenkirchl",
        "country": "Austria",
        "region": "Tyrol",
        "location": "Kufstein / St. Johann, Tyrol, Austria",
        "disciplines": ["trad climbing", "sport climbing"],
        "description": "Legendary alpine limestone massif steeped in history. Famous for big multi-pitch adventures, vertical pillars, deep water grooves (Wasserrillen), and steep headwalls.",
        "grade_range": "5b - 8b / 5.8 - 5.13d",
        "routes": [
            {"name": "Dülfer Führe (Fleischbank Ostwand)", "grade": "6b (5.10d)", "type": "trad", "pitches": 12, "description": "One of the classic six great north faces of the Alps, historic 1912 route."},
            {"name": "Pumprisse (Fleischbank)", "grade": "7a (5.11d)", "type": "trad/sport", "pitches": 8, "description": "First alpine grade VII in Europe, climbed by Reinhard Karl & Helmut Kiene."}
        ],
        "accommodations": [
            {"name": "Stripsenjochhaus Alpine Hut", "type": "hut/apartment", "distance_miles": 0.5, "notes": "Historic DAV alpine refuge right at the base of the north faces."},
            {"name": "Camping Michelnhof", "type": "campsite", "distance_miles": 4.0, "notes": "Quiet campground at the foot of the Kaiser mountains."}
        ]
    },
    {
        "id": "oetztal-niederthai",
        "name": "Ötztal - Niederthai & Engelswand",
        "country": "Austria",
        "region": "Tyrol",
        "location": "Umhausen / Längenfeld, Ötztal, Austria",
        "disciplines": ["sport climbing", "bouldering"],
        "description": "A premier Tyrolean alpine valley with over 20 granite and gneiss sport sectors. Featuring the famous Engelswand cliff, slab climbing, and family-friendly alpine crags.",
        "grade_range": "4b - 8c / 5.6 - 5.14b",
        "routes": [
            {"name": "Engelswand Himmelsstiege", "grade": "6a+ (5.10b)", "type": "sport", "pitches": 4, "description": "Pleasure multi-pitch route on solid orange gneiss plates with generous bolts."},
            {"name": "Niederthai Sonnenplatte", "grade": "6b (5.10d)", "type": "sport", "pitches": 1, "description": "Sun-drenched slab and crimp testpiece near the Stuibenfall waterfall."}
        ],
        "accommodations": [
            {"name": "Camping Ötztal Längenfeld", "type": "campsite", "distance_miles": 4.0, "notes": "Modern campsite with heated washrooms, spa discounts, and camper pitches."},
            {"name": "Aqua Dome Thermal Resort", "type": "hotel", "distance_miles": 4.5, "notes": "World-class thermal bath resort for post-climbing regeneration."}
        ]
    },
    {
        "id": "schleierwasserfall-tirol",
        "name": "Schleierwasserfall",
        "country": "Austria",
        "region": "Tyrol",
        "location": "Going am Wilden Kaiser, Tyrol, Austria",
        "disciplines": ["sport climbing"],
        "description": "The ultimate European hardcore sport climbing cave. A massive amphitheater overhung by up to 30 meters with a waterfall plunging in front of huge limestone stalactites and tufas.",
        "grade_range": "7a - 9b / 5.11d - 5.15b",
        "routes": [
            {"name": "Huberbuam Open Air", "grade": "9a+ (5.15a)", "type": "sport", "pitches": 1, "description": "Alexander Huber's historic 1996 milestone, now regarded as one of the world's first 9a+ routes."},
            {"name": "Weisse Rose (Schleier)", "grade": "8c+ (5.14c)", "type": "sport", "pitches": 1, "description": "Massive endurance roof testpiece across sweeping tufas."}
        ],
        "accommodations": [
            {"name": "Going Village Pension", "type": "inn/apartment", "distance_miles": 2.5, "notes": "Quiet guesthouse in the village below the Kaiser."},
            {"name": "Campingplatz Schwarzsee Kitzbühel", "type": "campsite", "distance_miles": 6.0, "notes": "Scenic lake campground near climbing areas."}
        ]
    },

    # ==========================
    # SWITZERLAND
    # ==========================
    {
        "id": "magic-wood-avers",
        "name": "Magic Wood - Avers Valley",
        "country": "Switzerland",
        "region": "Graubünden",
        "location": "Ausserferrera, Graubünden, Switzerland",
        "disciplines": ["bouldering"],
        "description": "One of the greatest bouldering meccas on Earth. Hundreds of moss-covered dark gneiss blocks scattered along a thundering glacial river under an alpine pine canopy.",
        "grade_range": "V2 - V16 / 5+ - 8c+",
        "routes": [
            {"name": "Riverbed", "grade": "V13 (8b)", "type": "boulder", "pitches": 1, "description": "Iconic compression and crimp line right on the river bank."},
            {"name": "Unendliche Geschichte", "grade": "V11 (8a+)", "type": "boulder", "pitches": 1, "description": "Peter Würth testpiece with sequential dynamic moves on clean slopers."},
            {"name": "Jack the Chipper", "grade": "V5 (6c)", "type": "boulder", "pitches": 1, "description": "Highball warm-up classic with great holds and clean landing."}
        ],
        "accommodations": [
            {"name": "Gasthaus Edelweiss (Bodhi Camping)", "type": "campsite/hostel", "distance_miles": 0.2, "notes": "The bouldering community hub in Ausserferrera with crash pad rentals and cafe."},
            {"name": "Hotel Post Andeer", "type": "hotel", "distance_miles": 6.5, "notes": "Thermal bath hotel perfect for rest days."}
        ]
    },
    {
        "id": "chironico-ticino",
        "name": "Chironico & Cresciano - Ticino Granite",
        "country": "Switzerland",
        "region": "Ticino",
        "location": "Ticino, Switzerland",
        "disciplines": ["bouldering", "sport climbing"],
        "description": "Sun-drenched chestnut forests with flawless grey granite and gneiss blocks. Famous for world-class crimpy boulders and technical friction slab/overhang sport climbing.",
        "grade_range": "V3 - V16 / 6a - 9a",
        "routes": [
            {"name": "Dreamtime (Cresciano)", "grade": "V15 (8c)", "type": "boulder", "pitches": 1, "description": "Fred Nicole's world-first 8c boulder, aesthetic crimps on a standing block."},
            {"name": "Doctor Pinch (Chironico)", "grade": "V8 (7b+)", "type": "boulder", "pitches": 1, "description": "Precision pinch-and-heel problem on pure granite."},
            {"name": "Le Souffle du Dragon", "grade": "8a (5.13b)", "type": "sport", "pitches": 1, "description": "Technical granite wall climb with delicate micro-edges."}
        ],
        "accommodations": [
            {"name": "Ostello Cresciano", "type": "hostel", "distance_miles": 1.0, "notes": "Dedicated climber hostel with boulder gear and community lounge."},
            {"name": "Camping Bellinzona", "type": "campsite", "distance_miles": 12.0, "notes": "Sunny valley camping near castles and grocery shops."}
        ]
    },
    {
        "id": "grimsel-eldorado",
        "name": "Grimsel Pass - Eldorado Slabs",
        "country": "Switzerland",
        "region": "Bernese Oberland",
        "location": "Grimsel Pass, Bern, Switzerland",
        "disciplines": ["trad climbing", "sport climbing"],
        "description": "Glacier-polished granite multi-pitch domes perched above alpine turquoise reservoirs. The pinnacle of friction climbing, pure slabs, and technical footwork in the high Alps.",
        "grade_range": "5c - 7c / 5.9 - 5.12d",
        "routes": [
            {"name": "Motörhead (Eldorado)", "grade": "6b (5.10d)", "type": "sport/trad", "pitches": 14, "description": "One of the most famous alpine rock routes in Europe; 500m of clean granite crack and slab."},
            {"name": "Septumania", "grade": "6a+ (5.10b)", "type": "sport", "pitches": 11, "description": "Superb friction slab lines with delicate balance moves."}
        ],
        "accommodations": [
            {"name": "Grimsel Hospiz", "type": "hotel", "distance_miles": 3.0, "notes": "Historic high-alpine lake hotel at 1,980m altitude."},
            {"name": "Camping Aareschlucht Meiringen", "type": "campsite", "distance_miles": 16.0, "notes": "Valley campsite near the foot of the mountain pass."}
        ]
    },
    {
        "id": "gastlosen-prealps",
        "name": "Gastlosen Range (Les Dents Rouges)",
        "country": "Switzerland",
        "region": "Fribourg / Vaud",
        "location": "Jaun, Fribourg, Switzerland",
        "disciplines": ["sport climbing", "trad climbing"],
        "description": "A jagged saw-tooth limestone mountain chain known as the Swiss Dolomites. Offers hundreds of single- and multi-pitch routes on steep, razor-sharp pocketed grey limestone.",
        "grade_range": "5c - 8b / 5.9 - 5.13d",
        "routes": [
            {"name": "La Fissure aux Fées", "grade": "6a (5.10a)", "type": "sport", "pitches": 5, "description": "Classic multi-pitch line climbing directly up a prominent limestone spire."},
            {"name": "Les Dents Blanches", "grade": "7a (5.11d)", "type": "sport", "pitches": 4, "description": "Airy face climbing on solid water-sculpted pockets."}
        ],
        "accommodations": [
            {"name": "Chalet du Soldat (Soldatenhaus)", "type": "hut/lodge", "distance_miles": 0.5, "notes": "Mountain refuge right beneath the cliffs with hearty Swiss fondue."},
            {"name": "Camping Jaun", "type": "campsite", "distance_miles": 3.5, "notes": "Quiet village campground near the waterfall."}
        ]
    },

    # ==========================
    # FRANCE
    # ==========================
    {
        "id": "ceuse-haute-provence",
        "name": "Falaises de Céüse",
        "country": "France",
        "region": "Hautes-Alpes",
        "location": "Gap / Sigoyer, Hautes-Alpes, France",
        "disciplines": ["sport climbing"],
        "description": "Widely regarded as the best sport climbing cliff on Earth. A crescent limestone cliff perched at 2,000m with unmatched blue/grey streaked rock, pockets, and endurance walls.",
        "grade_range": "6a - 9a+ / 5.10a - 5.15a",
        "routes": [
            {"name": "Biographie / Realization", "grade": "9a+ (5.15a)", "type": "sport", "pitches": 1, "description": "Chris Sharma's legendary line, historically the world's standard for 5.15a."},
            {"name": "Démence (Secteur Biographie)", "grade": "7b (5.12b)", "type": "sport", "pitches": 1, "description": "Superb 35m pump-fest on pristine grey pocketed limestone."},
            {"name": "L'Ami de Tout le Monde", "grade": "6b (5.10d)", "type": "sport", "pitches": 1, "description": "Sustained steep juggy warmup on Secteur Cascade."}
        ],
        "accommodations": [
            {"name": "Camping des Guérins", "type": "campsite", "distance_miles": 0.5, "notes": "Legendary basecamp for Céüse climbers at the start of the approach trail."},
            {"name": "Gîte du Col de Guérins", "type": "apartment/gite", "distance_miles": 0.6, "notes": "Comfortable rustic alpine apartments overlooking the mountain."}
        ]
    },
    {
        "id": "fontainebleau-forest",
        "name": "Fontainebleau Forest (Bleau)",
        "country": "France",
        "region": "Île-de-France",
        "location": "Fontainebleau, Île-de-France, France",
        "disciplines": ["bouldering"],
        "description": "The spiritual birthplace of bouldering. Thousands of soft white sandstone blocks across vast ancient forests, famous for rounded slopers, technical mantels, and circuit problems.",
        "grade_range": "3a - 8c / V0 - V15",
        "routes": [
            {"name": "Carnaval (Bas Cuvier)", "grade": "V8 (7b+)", "type": "boulder", "pitches": 1, "description": "Classic technical friction sloper and dyno move."},
            {"name": "L'Alchimiste (Apremont)", "grade": "V13 (8b+)", "type": "boulder", "pitches": 1, "description": "Famous micro-crimp line revisited by Nalle Hukkataival."},
            {"name": "Orange Circuit Cuvier #12", "grade": "V2 (5c)", "type": "boulder", "pitches": 1, "description": "Essential test of foot precision and delicate manteling."}
        ],
        "accommodations": [
            {"name": "Camping Les Prés (Grez-sur-Loing)", "type": "campsite", "distance_miles": 6.0, "notes": "Picturesque riverside camp popular with international boulderers."},
            {"name": "Gîte Bleau Village", "type": "apartment/gite", "distance_miles": 3.0, "notes": "Climber gîte with pad rentals and kitchen facilities."}
        ]
    },
    {
        "id": "verdon-gorge",
        "name": "Gorges du Verdon - Falaise de l'Escalès",
        "country": "France",
        "region": "Provence",
        "location": "La Palud-sur-Verdon, Provence, France",
        "disciplines": ["sport climbing", "trad climbing"],
        "description": "Spectacular 400m limestone canyon plunging into turquoise waters. Known for top-down abseils, dizzying exposure, bullet-hard grey limestone water-grooves, and multi-pitch classics.",
        "grade_range": "5c - 8c+ / 5.9 - 5.14c",
        "routes": [
            {"name": "La Demande", "grade": "6a+ (5.10b)", "type": "trad", "pitches": 12, "description": "Historical 1968 classic following deep chimneys and cracks over 350m."},
            {"name": "Pichenibule", "grade": "7b+ (5.12c)", "type": "sport", "pitches": 10, "description": "Groundbreaking multi-pitch face climb on flawless grey vertical limestone."},
            {"name": "Polpot", "grade": "7c+ (5.13a)", "type": "sport", "pitches": 1, "description": "Iconic single-pitch sheer vertical testpiece on pocketed drop-offs."}
        ],
        "accommodations": [
            {"name": "Camping Municipal Bourbon", "type": "campsite", "distance_miles": 1.5, "notes": "Right in La Palud-sur-Verdon, meeting point for gorge climbers."},
            {"name": "Hôtel Le Grand Jardin", "type": "hotel", "distance_miles": 1.2, "notes": "Charming village hotel with garden and climber-friendly staff."}
        ]
    },
    {
        "id": "calanques-marseille",
        "name": "Massif des Calanques",
        "country": "France",
        "region": "Provence",
        "location": "Marseille / Cassis, Provence, France",
        "disciplines": ["sport climbing", "trad climbing"],
        "description": "Towering pure-white limestone cliffs rising directly from the Mediterranean Sea. Fjord-like sea inlets (calanques) with multi-pitches, sea breezes, and deep-water soloing.",
        "grade_range": "5a - 8c / 5.7 - 5.14b",
        "routes": [
            {"name": "Arête des Cassis (En-Vau)", "grade": "5c (5.9)", "type": "trad", "pitches": 5, "description": "Iconic traverse line directly above the turquoise sea in Calanque d'En-Vau."},
            {"name": "La Voie du Toit (Sormiou)", "grade": "6b (5.10d)", "type": "sport", "pitches": 4, "description": "Stunning water-side climbing on immaculate white limestone."}
        ],
        "accommodations": [
            {"name": "Camping Les Cigales Cassis", "type": "campsite", "distance_miles": 3.0, "notes": "Campground set in pine groves minutes from the port of Cassis."},
            {"name": "Hôtel du Golfe Cassis", "type": "hotel", "distance_miles": 2.5, "notes": "Seaside harbor hotel with Mediterranean restaurants."}
        ]
    },
    {
        "id": "buoux-luberon",
        "name": "Buoux - Falaise de l'Aiguebrun",
        "country": "France",
        "region": "Provence",
        "location": "Buoux, Luberon, Provence, France",
        "disciplines": ["sport climbing"],
        "description": "The sacred golden temple of 1980s French sport climbing. Grey and golden pocketed molasse limestone walls, technical footwork, dynamic mono-pocket pulls, and iconic exposure.",
        "grade_range": "5c - 8c+ / 5.9 - 5.14c",
        "routes": [
            {"name": "Chouca", "grade": "8a+ (5.13c)", "type": "sport", "pitches": 1, "description": "World-famous pocket testpiece first climbed by Antoine Le Menestrel."},
            {"name": "La Rose des Sables", "grade": "7a (5.11d)", "type": "sport", "pitches": 1, "description": "Classic sustained face climbing on golden circular pockets."},
            {"name": "No Man's Land", "grade": "7b (5.12b)", "type": "sport", "pitches": 1, "description": "Airy arete and delicate technical movement."}
        ],
        "accommodations": [
            {"name": "Camping Municipal Apt", "type": "campsite", "distance_miles": 5.0, "notes": "Convenient valley campground in Apt with local provencal market."},
            {"name": "Auberge des Seguins", "type": "lodge/inn", "distance_miles": 0.4, "notes": "Historic stone inn located right at the foot of the Buoux cliffs."}
        ]
    },
    {
        "id": "saint-leger-ventoux",
        "name": "Saint-Léger-du-Ventoux",
        "country": "France",
        "region": "Provence",
        "location": "Saint-Léger-du-Ventoux, Vaucluse, France",
        "disciplines": ["sport climbing"],
        "description": "Tucked in the canyon below Mont Ventoux, a world-class sport climbing arena with both north- and south-facing limestone gorges packed with massive tufas, pinches, and steep caves.",
        "grade_range": "6b - 9b / 5.10d - 5.15b",
        "routes": [
            {"name": "Le Mur des Cyclopes", "grade": "7c (5.12d)", "type": "sport", "pitches": 1, "description": "Endurance tufa train climbing up a 35m gently overhanging wall."},
            {"name": "Crack à Pic", "grade": "8a (5.13b)", "type": "sport", "pitches": 1, "description": "Iconic overhanging kneebar and tufa route on Sector Pranian."}
        ],
        "accommodations": [
            {"name": "Gîte d'Étape Saint-Léger", "type": "hostel/gite", "distance_miles": 0.5, "notes": "Climber gîte in the heart of the village with gear storage."},
            {"name": "Camping Le Bosquet", "type": "campsite", "distance_miles": 7.0, "notes": "Spacious camping near Buis-les-Baronnies."}
        ]
    },
    {
        "id": "annot-sandstone",
        "name": "Annot - Grès d'Annot",
        "country": "France",
        "region": "Provence-Alpes-Côte d'Azur",
        "location": "Annot, Alpes-de-Haute-Provence, France",
        "disciplines": ["trad climbing", "bouldering", "sport climbing"],
        "description": "Enchanting chestnut forest filled with massive sandstone blocks and walls. Rare European mecca for pure splitter jam cracks, technical bouldering, and trad lines.",
        "grade_range": "5a - 8c / 5.7 - 5.14b",
        "routes": [
            {"name": "Spit Bull", "grade": "7b (5.12b)", "type": "trad", "pitches": 1, "description": "World-famous clean hand crack line on golden sandstone."},
            {"name": "Sector La Piste Boulders", "grade": "V3 - V12", "type": "boulder", "pitches": 1, "description": "High-friction sandstone blocks with clean landings under the trees."}
        ],
        "accommodations": [
            {"name": "Camping La Ribière", "type": "campsite", "distance_miles": 1.0, "notes": "Quiet campground in Annot within walking distance of crags."},
            {"name": "Hôtel de l'Avenue Annot", "type": "hotel", "distance_miles": 0.8, "notes": "Cozy town hotel with local dining."}
        ]
    }
]

def seed():
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("crags")

    print(f"Upserting {len(CRAGS)} premier European climbing locations...")
    for crag in CRAGS:
        doc_ref = collection.document(crag["id"])
        doc_ref.set(crag)
        print(f"  ✓ {crag['name']} [{crag['country']}] -> {crag['id']}")

    print(f"\nSuccessfully seeded all {len(CRAGS)} locations across DE, AT, CH, and FR!")

if __name__ == "__main__":
    seed()
