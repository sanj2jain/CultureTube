"""Cleaning rules for the CultureTube catalog. Imported by build_catalog.py.

Order of checks for every candidate video:
  1. data/blocklist.txt   (video IDs or channel names, one per line)   -> drop
  2. JUNK patterns in title / BLOCK_CHANNELS                           -> drop
  3. data/review.json decisions ("keep" / "drop", made by a human/LLM) -> obey
  4. curated seeds, TRUSTED_CHANNELS                                   -> keep
  5. title/channel mentions the topic (or one of its ALIASES)          -> keep
  6. otherwise                                                         -> "unreviewed" (dropped, listed in data/to_review.json)
"""
import json, re
from pathlib import Path

DATA = Path(__file__).parent / "data"

# Music videos are fine in the Music section, but noise in Dance/Arts/Culture/Body.
NON_MUSIC_JUNK = re.compile(r"\bofficial\s+(music\s+)?video\b|\bofficial\s+audio\b|\(official\b", re.I)

JUNK = re.compile(r"""
  \#shorts?\b | \bshorts\b | reaction | react(ing|s)?\s+to | prank | tiktok | \bvlog\b | unboxing | asmr |
  whats?app\s*status | \bstatus\s+video | \bfull\s+video\s+song | \bvideo\s+song | \blyrics\b | \blyric\s+video | \bkaraoke\b |
  \bjukebox\b | \bmovie\s+scene | \btrailer\b | \bteaser\b |
  \bnursery | \bfor\s+kids\b | \bkids\b | \bages?\s*\d+\s*\+ | \btoddler | \bcartoon | \bcocomelon | sesame\s+street |
  \bzumba\b | \bweight\s*loss\b | \bbelly\s+fat\b | \bworkout\s+at\s+home | \bcalories\b |
  \bfortnite\b | \bminecraft\b | \broblox\b | \bgta\b | \bmeme | \bfunny\b | \bfails?\b | \bcringe |
  \bstream\s+highlights | \bpodcast\s+ep\b | \bhindi\s+news\b | \bnews\s+live\b |
  \bfor\s+(deep\s+)?(focus|study|studying|sleep|relaxation|concentration)\b | \bstudy\s+with\b | \blo-?fi\b |
  \bsleep\s+music | \bdeep\s+work\s+session | \bno\s+mid-roll | \bdeep\s+focus\b | \bmusic\s+to\s+(study|sleep|relax) |
  \bhow\s+to\s+make\s+money | \bcrypto | \bstock\s+market
""", re.I | re.X)

BLOCK_CHANNELS = {c.lower() for c in [
  "Sesame Street", "Cocomelon - Nursery Rhymes", "Little Baby Bum - Nursery Rhymes & Kids Songs", "ChuChu TV Nursery Rhymes & Kids Songs",
  "Super Simple Songs - Kids Songs", "Pinkfong Baby Shark - Kids' Songs & Stories", "MihranTV", "Just Dance", "SPE Music India",
  "T-Series", "Zee Music Company", "Zee Music Marathi", "Sony Music India", "Tips Official", "Saregama Music", "Shemaroo",
  "Speed Records", "Aditya Music", "Lahari Music", "Think Music India", "Sun TV", "Mazhavil Manorama", "Stories That Matter",
]}

# Broadly reliable sources: keep even if the title doesn't name the topic.
TRUSTED_CHANNELS = {c.lower() for c in [
  "UNESCO", "Films Division", "Prasar Bharati Archives", "darbarfestival", "Sangeet Natak Akademi", "indiavideodotorg",
  "BBC", "BBC Global", "BBC Reel", "BBC Ideas", "BBC Four", "DW Documentary", "DW Classical Music", "Great Big Story",
  "National Geographic", "Smithsonian Channel", "Smithsonian Folkways", "Smithsonian Folkways Recordings", "PBS", "NOVA PBS Official",
  "Red Bull Dance", "Red Bull Music Academy", "Red Bull Music", "Juste Debout", "Jacob's Pillow Dance", "Jacob's Pillow",
  "TED", "TED-Ed", "TEDx Talks", "YaleCourses", "CrashCourse", "khanacademymedicine", "Khan Academy", "MIT OpenCourseWare",
  "Martha Graham Dance Company", "Royal Ballet and Opera", "Royal Opera House", "Dance Notation Bureau", "dancenotationbureau",
  "Philharmonia Orchestra", "Free Documentary", "Free High School Science Texts", "Perspective", "Art History with Travis Lee Clark",
  "The Art Institute of Chicago", "The Metropolitan Museum of Art", "Tate", "Museum of Modern Art", "Smarthistory", "The Royal Academy of Arts",
  "Al Jazeera English", "VICE", "VICE News", "Vox", "Arte", "ARTE.tv Documentary", "Nowness", "NOWNESS", "Sadler's Wells",
  "Musculoskeletal Education Channel", "Kenhub - Learn Human Anatomy", "AnatomyZone", "Ninja Nerd", "Institute of Human Anatomy",
  "David Hoffman", "Culture Vulture Rises", "YAKfilms", "Steezy", "STEEZY", "Dance Masterclass", "Feldenkrais Institute",
]}

# Extra words that count as "mentions the topic".
ALIASES = {
  "Sufi whirling Sema": ["dervish", "rumi", "sama", "mevlevi", "whirl"],
  "Kalaripayattu": ["kalari", "kalaripayat"], "Kalaripayattu training": ["kalari"],
  "Qawwali": ["nusrat", "sabri", "qawwal"], "Mridangam": ["tani", "mridang", "thani"],
  "Tabla solo": ["tabla", "zakir"], "Sitar": ["raag", "raga", "ravi shankar", "sitar"],
  "Mohiniyattam": ["mohiniattam", "mohiniyattom"], "Breaking bboy": ["b-boy", "bgirl", "b-girl", "breakdance", "breakin", "bboy"],
  "Garba dandiya": ["garba", "dandiya", "navratri"], "Indian temple dance devadasi": ["devadasi", "devdasi", "temple dance"],
  "Lavani": ["lavni"], "Kalbelia": ["kalbeliya", "kalbelia", "sapera"], "Dhrupad": ["dagar", "gundecha"],
  "Bulgarian women's choir": ["bulgarian voices", "voices of bulgaria", "bulgarian", "le mystere"],
  "Throat singing Tuvan": ["huun", "khoomei", "throat"], "Japanese taiko": ["taiko", "kodo"],
  "Vodun Benin": ["voodoo", "vodou", "vodun"], "Candomblé": ["candomble", "orixa"], "Orisha": ["orisa", "yoruba", "ifa"],
  "Fado": ["amalia"], "Psytrance": ["psychedelic trance", "goa trance", "psy trance"], "Afrobeat Fela": ["fela", "afrobeat"],
  "Hip hop history": ["hip-hop"], "History of hip hop culture": ["hip-hop", "hip hop"], "Bronx 1970s": ["bronx"],
  "Detroit techno": ["techno"], "Berlin techno Berghain": ["berghain", "berlin", "techno"], "Chicago house scene": ["house music", "chicago"],
  "Ballroom culture Paris is Burning": ["ballroom", "vogue", "voguing", "paris is burning"], "Vogue ballroom": ["vogue", "voguing", "ballroom"],
  "Haka": ["haka", "māori", "maori"], "Hula kahiko": ["hula"], "Native American powwow dance": ["powwow", "pow wow", "pow-wow"],
  "Tibetan cham dance": ["cham"], "Peking opera": ["beijing opera", "jingju", "chinese opera"],
  "Gotipua": ["gotipua"], "Chau mask dance Purulia": ["chhau", "chau", "purulia"], "Chhau dance": ["chhau", "chau", "chhou"],
  "Theyyam": ["theyyam", "theyyattam"], "Theyyam ritual": ["theyyam"],
  "Rajasthani folk music Manganiyar": ["manganiyar", "rajasthan", "langa"], "Baul music": ["baul"],
  "Victor Turner ritual": ["turner", "liminal", "ritual"], "Rites of passage": ["rite of passage", "initiation"],
  "Laban movement analysis": ["laban", "effort shape"], "Labanotation": ["laban", "notation"],
  "Dance movement therapy": ["dance therapy", "dmt", "movement therapy"], "Neuroscience of dance": ["brain", "neuro"],
  "Motor learning": ["motor skill", "skill acquisition"], "Proprioception": ["propriocept", "balance"],
  "Fascia": ["fascial", "myofascial"], "Pranayama": ["breath", "breathing"], "Meditation": ["mindful"],
  "Ido Portal movement culture": ["ido portal", "movement culture"], "Gaga movement Ohad Naharin": ["gaga", "naharin", "batsheva"],
  "Pina Bausch Tanztheater": ["pina", "bausch", "tanztheater"], "Postmodern dance Judson": ["judson", "postmodern", "trisha brown", "yvonne rainer"],
  "Contact improvisation": ["contact improv", "steve paxton"], "Mime Marcel Marceau": ["mime", "marceau"],
  "Performance art Marina Abramović": ["abramovic", "abramović", "performance art"], "Stanislavski method acting": ["stanislavsk", "method acting"],
  "Natyashastra": ["natya shastra", "natyasastra", "bharata"], "Abhinaya navarasa": ["abhinaya", "navarasa", "rasa", "bhava"],
  "Indian film music history": ["bollywood music", "film music", "playback", "r.d. burman", "rd burman", "lata mangeshkar", "kishore kumar", "a.r. rahman"],
  "Musicality for dancers": ["musicality"], "Counting music for dance": ["count", "8 count", "eight count", "musicality", "beat"],
  "Musical instruments of the world": ["instrument"], "Rhythm polyrhythm": ["polyrhythm", "rhythm"],
  "Temple sculpture Khajuraho": ["khajuraho", "temple"], "Architecture of temples": ["temple"],
  "Strength training for dancers": ["dancer"], "Dance injury prevention": ["injur"], "Hip anatomy dancers": ["hip"],
  "Turnout anatomy": ["turnout", "turn out", "external rotation"], "Breathing diaphragm anatomy": ["diaphragm", "breath"],
  "Biomechanics of movement": ["biomechanic"], "Functional anatomy": ["anatomy", "muscle", "joint", "skeleton", "bone"],
  "Musculoskeletal system": ["muscle", "skelet", "bone", "joint"], "Nervous system": ["nerv", "neuro", "brain"],
  "Body-Mind Centering": ["bmc", "bonnie bainbridge", "body mind centering"],
  "Commercial heels dance": ["heels"], "Fosse style": ["fosse"], "Tap dance": ["tap"],
  "Romantic ballet Giselle": ["giselle", "sylphide", "romantic ballet"], "Classical ballet": ["ballet"], "Vaganova method": ["vaganova"],
  "Balanchine": ["balanchine", "nycb", "new york city ballet"], "Akram Khan": ["akram"], "William Forsythe": ["forsythe"],
  "Crystal Pite": ["pite", "kidd pivot"], "Russian folk dance Moiseyev": ["moiseyev", "моисеев", "russian folk"],
  "Georgian dance Sukhishvili": ["sukhishvili", "georgian"], "Greek folk dance Syrtos": ["greek", "syrtos", "sirtaki"],
  "Dance battle Juste Debout": ["juste debout", "battle"], "Red Bull Dance Your Style": ["dance your style", "red bull"],
  "Dance film screendance": ["dance film", "screendance", "dance on film", "dance for camera"],
  "Choreography process": ["choreograph"], "Costume design for dance": ["costume"], "Mask making": ["mask"],
  "Indian handloom": ["handloom", "weav", "saree", "sari"], "Textile weaving traditions": ["weav", "textile", "loom"],
  "Islamic geometric art": ["islamic", "geometric", "girih"], "Japanese woodblock ukiyo-e": ["ukiyo", "woodblock", "hokusai", "hiroshige"],
  "Chinese ink painting": ["ink", "shan shui", "brush"], "Renaissance art": ["renaissance", "michelangelo", "leonardo", "raphael"],
  "African art masks": ["mask", "african art"], "Aboriginal dot painting": ["aboriginal", "dot painting", "dreaming"],
  "Street art graffiti": ["graffiti", "street art", "mural"], "Indian miniature painting": ["miniature", "mughal painting", "pahari", "rajput painting"],
  "Wayang kulit puppetry": ["wayang", "shadow puppet"], "Bunraku": ["bunraku", "puppet"], "Cabaret": ["cabaret", "burlesque"],
  "Ethnomusicology": ["ethnomusicolog"], "Ethnomusicology fieldwork": ["ethnomusicolog", "field record"],
  "Embodiment anthropology": ["embodi"], "Intangible cultural heritage UNESCO": ["intangible", "heritage"],
  "Oral tradition": ["oral", "storytell", "griot"], "Kora griot": ["kora", "griot", "toumani"], "Mbira": ["mbira", "kalimba"],
  "Gnawa": ["gnaoua", "gnawa"], "Celtic music": ["celtic", "irish", "scottish", "trad"], "Klezmer": ["klezmer", "yiddish"],
  "Persian classical music": ["persian", "iranian", "setar", "tar ", "dastgah", "santur"], "Arabic maqam oud": ["maqam", "oud", "arabic"],
  "Turkish makam": ["makam", "ney", "turkish"], "Flamenco guitar cante jondo": ["flamenco", "paco de lucia", "camarón", "cante"],
  "Gamelan": ["gamelan"], "Andean music": ["andean", "andes", "quechua", "charango", "peru", "bolivia"],
  "Synthesizer history": ["synth", "moog"], "Modular synth": ["modular", "moog", "eurorack", "buchla"],
  "DJ culture": ["dj ", "djing", "turntabl", "deejay"], "Dub music": ["dub", "lee scratch", "king tubby"],
  "Western Art Music": [], "Stravinsky Rite of Spring": ["stravinsky", "rite of spring", "sacre"],
  "Minimalism Steve Reich": ["reich", "minimalis"], "Contemporary classical composition": ["composer", "composition", "contemporary music"],
  "Hindustani classical raga": ["raag", "raga", "hindustani", "khayal"], "Carnatic music": ["carnatic", "karnatic", "kriti", "raga"],
  "Holi festival": ["holi"], "Kumbh Mela": ["kumbh"], "Durga Puja": ["durga"], "Day of the Dead": ["día de muertos", "dia de los muertos", "dia de muertos"],
  "Carnival Rio": ["carnaval", "carnival", "samba school"], "Notting Hill carnival": ["notting hill"], "Egungun masquerade": ["egungun", "masquerade"],
  "Shinto festival matsuri": ["matsuri", "shinto"], "Tibetan Buddhism ritual": ["tibet", "lama", "monk"], "Sufism": ["sufi", "rumi"],
  "Shamanism trance": ["shaman", "trance"], "Ritual and performance": ["ritual"], "Dance anthropology": ["anthropolog", "ethnochoreolog"],
  "Cultural anthropology": ["anthropolog"], "Colonialism and dance": ["coloni"], "Diaspora identity": ["diaspora"],
  "Mughal court culture": ["mughal"], "Silk Road history": ["silk road"], "Harlem Renaissance": ["harlem"],
  "Rave culture history": ["rave", "acid house"], "Disco era": ["disco", "studio 54"],
  "Northeast India tribes": ["nagaland", "naga", "manipur", "mizoram", "arunachal", "meghalaya", "assam", "tripura", "northeast"],
  "Pacific islands navigation": ["wayfinding", "polynesian", "voyag", "navigat"], "Mongolia nomads": ["mongol", "nomad"],
  "Sami people": ["sámi", "sami", "joik", "yoik", "lapland"], "West Africa culture": ["ghana", "senegal", "mali", "nigeria", "benin", "guinea", "west africa"],
  "Andes culture": ["andes", "andean", "quechua", "peru", "bolivia", "inca"], "Bali culture": ["bali"], "Kerala culture": ["kerala"],
  "Rajasthan culture": ["rajasthan"], "Japanese culture": ["japan"], "Cuba culture": ["cuba", "havana"], "Brazil culture": ["brazil", "brasil"],
  "Feldenkrais": ["feldenkrais", "awareness through movement"], "Alexander technique": ["alexander technique"],
  "Somatic movement": ["somatic"], "Authentic movement": ["authentic movement"], "Ideokinesis": ["ideokinesis", "imagery"],
  "Animal flow": ["animal flow", "animal movement"], "Floorwork technique": ["floorwork", "floor work"], "Aikido": ["aikido"],
  "Hatha yoga": ["yoga", "asana"], "Tai chi": ["tai chi", "taiji", "tai-chi"], "Qigong": ["qigong", "chi kung", "qi gong"],
  "Mobility training": ["mobility"], "Flexibility science": ["flexib", "stretch"], "Plyometrics": ["plyo", "jump"],
  "Dance medicine": ["dance medicine", "dancer", "injur"], "Spine anatomy": ["spine", "vertebra", "spinal"], "Pelvis anatomy": ["pelvi"],
  "Shoulder anatomy": ["shoulder"], "Foot and ankle anatomy": ["foot", "ankle", "feet"],
  "Footwork Chicago": ["footwork", "juke"], "Memphis jookin": ["jookin", "gangsta walk"], "Flexn": ["flexn", "flex n", "bone breaking"],
  "Litefeet": ["lite feet", "litefeet"], "Tutting": ["tut", "tutting"], "Animation dance": ["animation", "robot"],
  "Hip hop freestyle": ["freestyle", "hip hop", "hip-hop"], "Hip hop choreography": ["choreo", "hip hop", "hip-hop"],
  "Urban dance choreography": ["choreo", "urban"], "Shuffle dance": ["shuffle"], "Jerkin": ["jerk"], "Turfing": ["turf"],
  "Musical theatre dance": ["musical theatre", "broadway", "musical theater"], "Ballroom dance": ["ballroom", "waltz", "foxtrot", "quickstep", "tango"],
  "Swing dance": ["swing", "lindy", "balboa", "shag"], "Jazz dance": ["jazz"],
  "Irish step dance": ["irish dance", "riverdance", "irish dancing"], "Scottish highland dance": ["highland"],
  "Basque dance": ["basque", "euskal", "dantza"], "Morris dance": ["morris"], "Hora dance": ["hora"], "Schuhplattler": ["schuhplattler", "plattler"],
  "Baroque dance": ["baroque"], "Balfolk": ["balfolk", "bal folk", "folkbal"],
  "Argentine tango": ["tango"], "Salsa dance": ["salsa"], "Rumba Cuban": ["rumba", "guaguancó", "guaguanco"], "Son Jarocho": ["jarocho", "fandango"],
  "Danza de los Diablos": ["diablos", "devil"], "Bomba Puerto Rico": ["bomba"], "Dancehall": ["dancehall"], "Joropo": ["joropo"],
  "Marinera": ["marinera"], "Frevo": ["frevo"], "Forró": ["forro", "forró"], "Capoeira": ["capoeira", "roda"],
  "West African dance Sabar": ["sabar", "senegal"], "Djembe dance Guinea": ["djembe", "guinea", "dundun"], "Zulu dance Indlamu": ["zulu", "indlamu"],
  "Gumboot dance": ["gumboot"], "Pantsula": ["pantsula"], "Azonto": ["azonto"], "Coupé-décalé": ["coupe decale", "coupé décalé", "coupé-décalé"],
  "Ndombolo": ["ndombolo", "congo"], "Adumu Maasai jumping": ["maasai", "masai", "adumu"], "Eskista Ethiopian dance": ["eskista", "ethiopia"],
  "Afrobeats dance": ["afro", "afrobeats"], "Kwassa kwassa": ["kwassa"], "Amapiano dance": ["amapiano"], "Amapiano": ["amapiano"],
  "Dabke": ["dabke", "debke", "dabka"], "Belly dance Raqs Sharqi": ["belly", "raqs", "oriental dance"], "Persian classical dance": ["persian", "iranian"],
  "Attan Afghan dance": ["attan", "afghan"], "Uzbek dance": ["uzbek"], "Tanoura Egyptian": ["tanoura", "tannoura"],
  "Kabuki": ["kabuki"], "Butoh": ["butoh", "hijikata", "ohno"], "Noh theatre": ["noh"], "Korean traditional dance": ["korean"],
  "Chinese classical dance": ["chinese"], "Balinese dance Legong": ["legong", "balinese", "bali"], "Javanese court dance": ["javanese", "bedhaya", "srimpi", "java"],
  "Khmer classical dance Apsara": ["apsara", "khmer", "cambodia"], "Thai classical dance Khon": ["khon", "thai"], "Lion dance": ["lion dance"],
  "Philippine Tinikling": ["tinikling"], "Aboriginal Australian dance": ["aboriginal", "indigenous", "bangarra"],
  "Siva Samoa": ["samoa", "siva"], "Tahitian Ori": ["tahiti", "ori tahiti"], "Hoop dance": ["hoop dance", "hoop dancer"], "Inuit drum dance": ["inuit", "drum dance"],
  "Bharatanatyam": ["bharatnatyam", "bharata natyam", "bharathanatyam"], "Kuchipudi": ["kuchipudi"], "Odissi": ["odissi"],
  "Kathakali": ["kathakali"], "Manipuri dance": ["manipuri", "ras lila", "raas leela"], "Sattriya": ["sattriya", "satriya", "xattriya"],
  "Yakshagana": ["yakshagana"], "Bhangra": ["bhangra"], "Ghoomar": ["ghoomar", "ghumar"], "Bihu dance": ["bihu"],
  "Dollu Kunitha": ["dollu"], "Koli dance": ["koli"],
  "Kathak": ["kathak"], "House dance": ["house"], "Waacking": ["waack", "whack", "punking"], "Popping": ["popping", "popper", "boogaloo"],
  "Locking": ["locking", "locker"], "Krump": ["krump"], "Physical theatre": ["physical theatre", "physical theater"],
  "Jacques Lecoq": ["lecoq"], "Grotowski": ["grotowski"], "Commedia dell'arte": ["commedia"], "Clowning": ["clown"], "Kutiyattam": ["koodiyattam", "kutiyattam"],
}

STOP = set("""the of and de los la las el dance dances dancing music basics tutorial history origins traditional technique
culture style art arts method movement for in to on with a an by""".split())

def _tokens(topic):
    return [w for w in re.findall(r"[a-z0-9'éóúíáàçõãü]+", topic.lower()) if w not in STOP and len(w) > 2]

def _load_lines(name):
    p = DATA / name
    if not p.exists(): return set()
    return {l.split("#")[0].strip().lower() for l in p.read_text().splitlines() if l.split("#")[0].strip()}

BLOCKLIST = _load_lines("blocklist.txt")
_review_path = DATA / "review.json"
REVIEW = json.loads(_review_path.read_text()) if _review_path.exists() else {}

def verdict(e, topic, curated=False, category=""):
    """Return (keep: bool, reason: str)."""
    vid, title = e.get("id", ""), e.get("title") or ""
    ch = (e.get("channel") or e.get("uploader") or "").strip()
    if vid.lower() in BLOCKLIST or ch.lower() in BLOCKLIST: return False, "blocklist"
    if ch.lower() in BLOCK_CHANNELS: return False, "blocked-channel"
    r = REVIEW.get(vid)
    if r == "drop": return False, "review"
    if r == "keep": return True, "review"
    if not curated:
        m = JUNK.search(title) or (category != "Music" and NON_MUSIC_JUNK.search(title))
        if m: return False, "junk:" + m.group(0).strip().lower()
    if curated: return True, "curated"
    if ch.lower() in TRUSTED_CHANNELS: return True, "trusted"
    hay = (title + " " + ch).lower()
    words = _tokens(topic) + [a.lower() for a in ALIASES.get(topic, [])]
    if any(w in hay for w in words): return True, "match"
    return False, "unreviewed"
