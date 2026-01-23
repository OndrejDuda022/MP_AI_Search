import sys
import os
from dotenv import load_dotenv

#prepare environment
load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from src.local_db import add_document, get_db_stats

# === ZÁKLADNÍ INFORMACE ===

# Kontaktní údaje školy - adresa
add_document(
    "Střední průmyslová škola a Vyšší odborná škola Liberec, Masarykova 460/3, Liberec I-Staré Město, PSČ 460 01. IČ: 46747991. Budova Tyršova: Tyršova 82, Liberec.",
    metadata={"kategorie": "kontakt", "typ": "adresa", "priorita": "vysoka"},
    doc_id="cnt_001"
)

# Kontaktní údaje - komunikace
add_document(
    "Sekretariát školy: email sekretariat@pslib.cz, telefon +420 487 989 611. Oficiální název: Střední průmyslová škola a Vyšší odborná škola, Liberec, příspěvková organizace. REDIZO: 600 020 398.",
    metadata={"kategorie": "kontakt", "typ": "komunikace", "priorita": "vysoka"},
    doc_id="cnt_002"
)

# Historie školy
add_document(
    "Průmyslová škola Liberec slaví 150 let existence. Jsme moderní škola, která připravuje studenty do života s důrazem na technické obory a jejich praktické uplatnění.",
    metadata={"kategorie": "o_skole", "typ": "historie"},
    doc_id="about_001"
)

# === STUDIJNÍ OBORY ===

# Přehled oborů
add_document(
    "Škola nabízí pět maturitních oborů: Informační technologie, Elektrotechnika, Strojírenství, Technické lyceum a Oděvnictví. Všechny obory poskytují pevný základ pro uplatnění po škole i možnost dalšího studia na vysoké škole.",
    metadata={"kategorie": "obory", "typ": "prehled", "priorita": "vysoka"},
    doc_id="edu_001"
)

# Informační technologie - základní info
add_document(
    "Obor Informační technologie se zaměřuje na návrh, vývoj, použití, podporu a správu všech informačních systémů založených na elektronických počítačích. Důraz na počítačový hardware, aplikační software a mobilní zařízení.",
    metadata={"kategorie": "obory", "obor": "IT", "kod": "18-20-M/01"},
    doc_id="edu_it_001"
)

# Informační technologie - specializace
add_document(
    "Specializace oboru Informační technologie: 1) Desktopové, mobilní a webové aplikace a multimédia, 2) Kybernetická bezpečnost, administrace systémů a internet věcí (IoT).",
    metadata={"kategorie": "obory", "obor": "IT", "typ": "specializace"},
    doc_id="edu_it_002"
)

# Informační technologie - ideální student
add_document(
    "Ideální student IT oboru má dobré známky z matematiky a angličtiny, baví ho řešit logické hádanky, zúčastňuje se soutěže Bobřík informatiky, provozuje vlastní webové stránky nebo blog, sestavil si nebo nakonfiguroval počítač, vytváří jednoduché programy nebo hry.",
    metadata={"kategorie": "obory", "obor": "IT", "typ": "pozadavky"},
    doc_id="edu_it_003"
)

# Elektrotechnika - základní info
add_document(
    "Obor Elektrotechnika se zaměřuje na elektrickou energii jako zdroj veškeré energie kolem nás. Studium zahrnuje mikroelektroniku, robotiku, řídicí jednotky PLC, energetiku nebo internet věcí (IoT).",
    metadata={"kategorie": "obory", "obor": "elektro", "kod": "26-41-M/01"},
    doc_id="edu_el_001"
)

# Elektrotechnika - specializace
add_document(
    "Specializace oboru Elektrotechnika: 1) Elektronické systémy, automatizace a sdělovací technika, 2) Průmyslová elektrotechnika, výkonová elektronika a řídicí systémy, 3) Robotika, internet věcí a průmyslové řídicí systémy.",
    metadata={"kategorie": "obory", "obor": "elektro", "typ": "specializace"},
    doc_id="edu_el_002"
)

# Elektrotechnika - odborná způsobilost
add_document(
    "V průběhu studia elektrotechniky může žák získat odbornou způsobilost podle §6 nařízení vlády č. 194/2022 Sb. pro práci s elektrickými zařízeními.",
    metadata={"kategorie": "obory", "obor": "elektro", "typ": "certifikace"},
    doc_id="edu_el_003"
)

# Vyšší odborná škola
add_document(
    "VOŠ Liberec nabízí studium v programu Počítačové systémy, které je zakončeno titulem DiS. (diplomovaný specialista). Vyšší odborné vzdělání je alternativou k vysokoškolskému studiu s větším důrazem na praxi.",
    metadata={"kategorie": "obory", "uroven": "vos", "priorita": "vysoka"},
    doc_id="edu_vos_001"
)

# === PŘIJÍMACÍ ŘÍZENÍ ===

# Přijímací řízení 2026/2027
add_document(
    "Přijímací řízení pro školní rok 2026/2027 - kritéria byla vyhlášena. Přijímací řízení ke studiu na střední škole se řídí výsledky jednotné přijímací zkoušky z českého jazyka a matematiky.",
    metadata={"kategorie": "prijimacky", "rok": 2026, "priorita": "vysoka"},
    doc_id="adm_001"
)

# === PROJEKTY A AKTIVITY ===

# Erasmus+
add_document(
    "Studenti 3. a 4. ročníku se mohou zúčastnit krátkodobých i dlouhodobých zahraničních pracovních stáží v rámci mezinárodního projektu Erasmus+. Projektu se škola pravidelně účastní od školního roku 2018/2019.",
    metadata={"kategorie": "projekty", "typ": "erasmus", "priorita": "stredni"},
    doc_id="proj_erasmus"
)

# Školní parlament
add_document(
    "Školní parlament slouží jako prostředník mezi vedením školy a studenty. Je to demokratický orgán, který reprezentuje zájmy žáků.",
    metadata={"kategorie": "projekty", "typ": "parlament"},
    doc_id="proj_parlament"
)

# Soboty s technikou
add_document(
    "Každý rok škola organizuje technicky zaměřené kurzy 'Soboty s technikou' pro žáky 8. a 9. tříd základních škol. Účastníci si mohou vyzkoušet práci v technických oborech.",
    metadata={"kategorie": "projekty", "typ": "kurzy", "cilova_skupina": "zs"},
    doc_id="proj_soboty"
)

# Školní časopis Zkrat
add_document(
    "Škola vydává školní časopis Zkrat, ve kterém se studenti mohou dočíst o dění ve škole i mimo ni. Časopis vytváří žáci a píšou o aktuálních událostech.",
    metadata={"kategorie": "projekty", "typ": "casopis"},
    doc_id="proj_zkrat"
)

# Burza firem
add_document(
    "Naši studenti se na Burze firem pravidelně mohou seznámit s významnými firmami v regionu. Jde o networking událost spojující školu s praxí.",
    metadata={"kategorie": "projekty", "typ": "burza"},
    doc_id="proj_burza"
)

# Boříme mýty - technika pro holky
add_document(
    "Škola realizuje projekt 'Boříme mýty! Technika je i pro holky!'. Ukazujeme, že technické obory jsou opravdu pro každého a všichni si u nás najdou přesně to, co je baví.",
    metadata={"kategorie": "projekty", "typ": "rovnost", "cilova_skupina": "dívky"},
    doc_id="proj_myty"
)

# === PARTNEŘI ===

# Partnerské firmy
add_document(
    "Mezi partnery školy patří významné firmy: ČEPS, Skupina ČEZ, Magna Liberec, Applic, Aries, Kopos a STAP a.s. Škola je partnerskou školou 'ČEZ čistá energie zítřka'.",
    metadata={"kategorie": "partnerstvi", "typ": "firmy"},
    doc_id="partner_001"
)

# === SLUŽBY PRO STUDENTY ===

# Den otevřených dveří
add_document(
    "Škola pravidelně pořádá Dny otevřených dveří pro zájemce o studium. Poslední se konal 17. ledna 2025, kde se mohli budoucí studenti seznámit se školou a obory.",
    metadata={"kategorie": "udalosti", "typ": "dod"},
    doc_id="event_dod"
)

# Zřizovatel
add_document(
    "Zřizovatelem školy je Liberecký kraj. Škola je příspěvková organizace zřízená krajem pro poskytování středního a vyššího odborného vzdělávání.",
    metadata={"kategorie": "o_skole", "typ": "zrizovatel"},
    doc_id="about_zrizovatel"
)

# Print database stats
stats = get_db_stats()
print(f"[*] Local database populated with {stats.get('count', 0)} documents.")