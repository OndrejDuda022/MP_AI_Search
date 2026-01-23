import sys
import os
from dotenv import load_dotenv

#prepare environment
load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from src.local_db import add_document, get_db_stats

# Kontaktní údaje školy
add_document(
    "Střední průmyslová škola strojní a elektrotechnická a Vyšší odborná škola, Liberec, Masarykova 3, příspěvková organizace. PSČ 460 01.",
    metadata={"kategorie": "kontakt", "typ": "adresa"},
    doc_id="cnt_001"
)

# Nabízené studijní obory (SŠ)
add_document(
    "Škola nabízí čtyři maturitní obory: Informační technologie, Elektrotechnika, Strojírenství a Technické lyceum.",
    metadata={"kategorie": "studium", "uroven": "stredni"},
    doc_id="edu_001"
)

# Informace o jídelně
add_document(
    "Školní jídelna a výdej Stravenka. Obědy se objednávají přes portál www.strava.cz, číslo jídelny 0256.",
    metadata={"kategorie": "sluzby", "sekce": "jidelna"},
    doc_id="srv_001"
)

# Informace o přijímacím řízení
add_document(
    "Přijímací řízení ke studiu na střední škole se řídí výsledky jednotné přijímací zkoušky z českého jazyka a matematiky.",
    metadata={"kategorie": "prijimacky", "rok": 2026},
    doc_id="adm_001"
)

# Detail oboru IT
add_document(
    "Obor Informační technologie (IT) se zaměřuje na programování, databáze, počítačové sítě Cisco a kybernetickou bezpečnost.",
    metadata={"kategorie": "obory", "kod": "18-20-M/01", "stitky": "it, cisco, kodovani"},
    doc_id="edu_002"
)

# Vyšší odborná škola (VOŠ)
add_document(
    "VOŠ Liberec nabízí studium v programu Počítačové systémy, které je zakončeno titulem DiS. (diplomovaný specialista).",
    metadata={"kategorie": "studium", "uroven": "vos"},
    doc_id="edu_003"
)

# Ubytování (Domov mládeže)
add_document(
    "Domov mládeže v ulici Zeyerova nabízí ubytování pro mimoliberecké studenty. K dispozici je Wi-Fi a celodenní strava.",
    metadata={"kategorie": "sluzby", "typ": "ubytovani"},
    doc_id="srv_002"
)

# Technické vybavení
add_document(
    "Škola disponuje moderními dílnami pro strojírenství, laboratořemi elektrotechniky a specializovanými učebnami pro výuku robotiky a 3D tisku.",
    metadata={"kategorie": "skola", "vybaveni": "technicke"},
    doc_id="fac_001"
)

# Erasmus+ a zahraničí
add_document(
    "Studenti se mohou účastnit zahraničních stáží v rámci programu Erasmus+, například v Irsku, Německu nebo Španělsku.",
    metadata={"kategorie": "skola", "aktivity": "zahranici"},
    doc_id="act_001"
)

# Vedení školy
add_document(
    "Ing. Jaroslav Semerád, ředitel školy. Kontakt: jaroslav.semerad@pslib.cz. Konzultační hodiny: Čtvrtek 14:00–15:00.",
    metadata={"sekce": "vedeni", "role": "ředitel"},
    doc_id="staff_001"
)

# Sekretariát
add_document(
    "Sekretariát a podatelna: Jaroslava Kubátová. Tel: +420 485 100 113, email: info@pslib.cz. Úřední hodiny: Po–Pá 7:30–15:30.",
    metadata={"sekce": "administrativa", "typ": "kontakt"},
    doc_id="staff_002"
)

# Výchovný poradce
add_document(
    "Výchovné poradenství: Mgr. Jana Svobodová. Konzultace pro žáky a rodiče: Středa 10:00–11:40 (kabinet 112).",
    metadata={"sekce": "poradenstvi", "role": "vychovny_poradce"},
    doc_id="staff_003"
)

# Ukázka učitele (odborné předměty IT)
add_document(
    "Ing. Jan Novák (Informatika, Sítě). Email: jan.novak@pslib.cz. Konzultace: Úterý 14:35–15:20 v laboratoři L304.",
    metadata={"sekce": "ucitele", "odbor": "IT"},
    doc_id="staff_004"
)

# Ukázka učitele (strojírenství)
add_document(
    "Ing. Petr Kolář (Strojnictví, CAD). Email: petr.kolar@pslib.cz. Konzultace: Pondělí 7:10–7:55 (kabinet 405).",
    metadata={"sekce": "ucitele", "odbor": "strojirenstvi"},
    doc_id="staff_005"
)

# Print database stats
stats = get_db_stats()
print(f"[*] Local database populated with {stats.get('count', 0)} documents.")