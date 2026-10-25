"""Deliberate provider aliases; unmatched clubs must never borrow another club's history."""
import re
import unicodedata


def identity_key(name: str) -> str:
    words = re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower())
    while words and words[0] in {"fc", "cf", "afc", "sc", "ac"}:
        words.pop(0)
    while words and words[-1] in {"fc", "cf", "afc", "sc", "ac", "cfc"}:
        words.pop()
    key = "".join(words)
    return ALIASES.get(key, key)


ALIASES = {
    "manchestercity": "mancity", "manchesterunited": "manunited", "manutd": "manunited",
    "leedsunited": "leeds", "newcastleunited": "newcastle", "nottinghamforest": "nottmforest",
    "tottenhamhotspur": "tottenham", "brightonhovealbion": "brighton", "westhamunited": "westham",
    "wolverhamptonwanderers": "wolves", "ipswichtown": "ipswich", "hullcity": "hull",
    "leicestercity": "leicester", "norwichcity": "norwich",
    "stokecity": "stoke", "swanseacity": "swansea", "cardiffcity": "cardiff",
    "birminghamcity": "birmingham", "blackburnrovers": "blackburn", "boltonwanderers": "bolton",
    "charltonathletic": "charlton", "derbycounty": "derby", "prestonnorthend": "preston",
    "queensparkrangers": "qpr", "westbromwichalbion": "westbrom", "coventrycity": "coventry",
    "sheffieldwednesday": "sheffieldweds", "huddersfieldtown": "huddersfield",
    "lutontown": "luton", "rotherhamunited": "rotherham", "bristolcity": "bristolcity",
    "1fsvmainz05": "mainz", "bayer04leverkusen": "leverkusen", "borussiadortmund": "dortmund",
    "borussiamonchengladbach": "mgladbach", "hamburgersv": "hamburg", "tsg1899hoffenheim": "hoffenheim",
    "bayernmunchen": "bayernmunich", "1fckoln": "fckoln", "1fcunionberlin": "unionberlin",
    "eintrachtfrankfurt": "einfrankfurt", "vfbstuttgart": "stuttgart",
    "vflwolfsburg": "wolfsburg", "scfreiburg": "freiburg", "werderbremen": "werderbremen",
    "fctwente65": "twente", "feyenoordrotterdam": "feyenoord", "psv": "psveindhoven",
    "az": "azalkmaar", "nec": "nijmegen", "fortunasittard": "forsittard",
    "asmonaco": "monaco", "estroyes": "troyes", "lilleosc": "lille", "ogcnice": "nice",
    "olympiquelyonnais": "lyon", "olympiquedemarseille": "marseille", "parissaintgermain": "parissg",
    "rcstrasbourgalsace": "strasbourg", "racingclubdelens": "lens", "stadebrestois29": "brest",
    "staderennaisfc1901": "rennes", "staderennais": "rennes", "asstetienne": "stetienne",
    "athleticclub": "athbilbao", "clubatleticodemadrid": "athmadrid", "atleticomadrid": "athmadrid",
    "deportivoalaves": "alaves", "rcceltadevigo": "celta", "rcdeportivolacoruna": "lacoruna",
    "rcdespanyoldebarcelona": "espanol", "rayovallecanodemadrid": "vallecano", "realbetisbalompie": "betis",
    "realracingclubdesantander": "santander", "realsociedaddefutbol": "sociedad",
    "sportlisboaebenfica": "benfica", "sportingclubedebraga": "spbraga", "sportingclubedeportugal": "splisbon",
    "gdestorilpraia": "estoril", "vitoriasc": "guimaraes", "csmaritimo": "maritimo",
    "casapiaac": "casapia", "fcarouca": "arouca", "cfestreladaamadora": "estrela",
    "bolognafc1909": "bologna", "cagliaricalcio": "cagliari", "como1907": "como",
    "internazionalemilano": "inter", "frosinonecalcio": "frosinone", "parmacalcio1913": "parma",
    "ussassuolocalcio": "sassuolo", "udinesecalcio": "udinese", "sscnapoli": "napoli",
    "asroma": "roma", "sslazio": "lazio", "hellasverona": "verona",
    "uslecce": "lecce", "ussalernitana1919": "salernitana",
    "koln": "fckoln", "scpaderborn07": "paderborn", "paderborn07": "paderborn", "sv07elversberg": "elversberg",
    "svwerderbremen": "werderbremen", "twente65": "twente", "peczwolle": "zwolle",
    "cambuurleeuwarden": "cambuur", "lincolncity": "lincoln", "ajauxerre": "auxerre",
    "angerssco": "angers", "caosasuna": "osasuna", "levanteud": "levante",
    "academicodeviseu": "academicoviseu", "cdnacional": "nacional", "cdsantaclara": "santaclara",
    "estreladaamadora": "estrela", "vitoria": "guimaraes", "acffiorentina": "fiorentina",
    "atalantabc": "atalanta",
}
