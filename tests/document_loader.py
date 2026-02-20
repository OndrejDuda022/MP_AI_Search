"""
Seed script – loads school knowledge-base documents into the local vector DB.
Run from the project root:
    python tests/document_loader.py
"""
import sys
import os
import logging
from dotenv import load_dotenv

# ── Environment setup ───────────────────────────────────────────────────────────
load_dotenv()
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.local_db import add_document_to_db, get_db_stats

# ── Logging ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Document definitions ────────────────────────────────────────────────────────
DOCUMENTS = [
    # ── ZÁKLADNÍ INFORMACE ──────────────────────────────────────────────────────
    {
        "doc_id": "cnt_001",
        "content": "Střední průmyslová škola a Vyšší odborná škola Liberec, Masarykova 460/3, Liberec I-Staré Město, PSČ 460 01. IČ: 46747991. Budova Tyršova: Tyršova 82, Liberec.",
        "metadata": {"kategorie": "kontakt", "typ": "adresa", "priorita": "vysoka"},
    },
    {
        "doc_id": "cnt_002",
        "content": "Sekretariát školy: email sekretariat@pslib.cz, telefon +420 487 989 611. Oficiální název: Střední průmyslová škola a Vyšší odborná škola, Liberec, příspěvková organizace. REDIZO: 600 020 398.",
        "metadata": {"kategorie": "kontakt", "typ": "komunikace", "priorita": "vysoka"},
    },
    {
        "doc_id": "about_001",
        "content": "Průmyslová škola Liberec slaví 150 let existence. Jsme moderní škola, která připravuje studenty do života s důrazem na technické obory a jejich praktické uplatnění.",
        "metadata": {"kategorie": "o_skole", "typ": "historie"},
    },
    # ── STUDIJNÍ OBORY ───────────────────────────────────────────────────────────
    {
        "doc_id": "edu_001",
        "content": "Škola nabízí pět maturitních oborů: Informační technologie, Elektrotechnika, Strojírenství, Technické lyceum a Oděvnictví. Všechny obory poskytují pevný základ pro uplatnění po škole i možnost dalšího studia na vysoké škole.",
        "metadata": {"kategorie": "obory", "typ": "prehled", "priorita": "vysoka"},
    },
    {
        "doc_id": "edu_it_001",
        "content": "Obor Informační technologie se zaměřuje na návrh, vývoj, použití, podporu a správu všech informačních systémů založených na elektronických počítačích. Důraz na počítačový hardware, aplikační software a mobilní zařízení.",
        "metadata": {"kategorie": "obory", "obor": "IT", "kod": "18-20-M/01"},
    },
    {
        "doc_id": "edu_it_002",
        "content": "Specializace oboru Informační technologie: 1) Desktopové, mobilní a webové aplikace a multimédia, 2) Kybernetická bezpečnost, administrace systémů a internet věcí (IoT).",
        "metadata": {"kategorie": "obory", "obor": "IT", "typ": "specializace"},
    },
    {
        "doc_id": "edu_it_003",
        "content": "Ideální student IT oboru má dobré známky z matematiky a angličtiny, baví ho řešit logické hádanky, zúčastňuje se soutěže Bobřík informatiky, provozuje vlastní webové stránky nebo blog, sestavil si nebo nakonfiguroval počítač, vytváří jednoduché programy nebo hry.",
        "metadata": {"kategorie": "obory", "obor": "IT", "typ": "pozadavky"},
    },
    {
        "doc_id": "edu_el_001",
        "content": "Obor Elektrotechnika se zaměřuje na elektrickou energii jako zdroj veškeré energie kolem nás. Studium zahrnuje mikroelektroniku, robotiku, řídicí jednotky PLC, energetiku nebo internet věcí (IoT).",
        "metadata": {"kategorie": "obory", "obor": "elektro", "kod": "26-41-M/01"},
    },
    {
        "doc_id": "edu_el_002",
        "content": "Specializace oboru Elektrotechnika: 1) Elektronické systémy, automatizace a sdělovací technika, 2) Průmyslová elektrotechnika, výkonová elektronika a řídicí systémy, 3) Robotika, internet věcí a průmyslové řídicí systémy.",
        "metadata": {"kategorie": "obory", "obor": "elektro", "typ": "specializace"},
    },
    {
        "doc_id": "edu_el_003",
        "content": "V průběhu studia elektrotechniky může žák získat odbornou způsobilost podle §6 nařízení vlády č. 194/2022 Sb. pro práci s elektrickými zařízeními.",
        "metadata": {"kategorie": "obory", "obor": "elektro", "typ": "certifikace"},
    },
    {
        "doc_id": "edu_vos_001",
        "content": "VOŠ Liberec nabízí studium v programu Počítačové systémy, které je zakončeno titulem DiS. (diplomovaný specialista). Vyšší odborné vzdělání je alternativou k vysokoškolskému studiu s větším důrazem na praxi.",
        "metadata": {"kategorie": "obory", "uroven": "vos", "priorita": "vysoka"},
    },
    # ── PŘIJÍMACÍ ŘÍZENÍ ──────────────────────────────────────────────────────────
    {
        "doc_id": "adm_001",
        "content": "Přijímací řízení pro školní rok 2026/2027 - kritéria byla vyhlášena. Přijímací řízení ke studiu na střední škole se řídí výsledky jednotné přijímací zkoušky z českého jazyka a matematiky.",
        "metadata": {"kategorie": "prijimacky", "rok": 2026, "priorita": "vysoka"},
    },
    # ── PROJEKTY A AKTIVITY ──────────────────────────────────────────────────────
    {
        "doc_id": "proj_erasmus",
        "content": "Studenti 3. a 4. ročníku se mohou zúčastnit krátkodobých i dlouhodobých zahraničních pracovních stáží v rámci mezinárodního projektu Erasmus+. Projektu se škola pravidelně účastní od školního roku 2018/2019.",
        "metadata": {"kategorie": "projekty", "typ": "erasmus", "priorita": "stredni"},
    },
    {
        "doc_id": "proj_parlament",
        "content": "Školní parlament slouží jako prostředník mezi vedením školy a studenty. Je to demokratický orgán, který reprezentuje zájmy žáků.",
        "metadata": {"kategorie": "projekty", "typ": "parlament"},
    },
    {
        "doc_id": "proj_soboty",
        "content": "Každý rok škola organizuje technicky zaměřené kurzy 'Soboty s technikou' pro žáky 8. a 9. tříd základních škol. Účastníci si mohou vyzkoušet práci v technických oborech.",
        "metadata": {"kategorie": "projekty", "typ": "kurzy", "cilova_skupina": "zs"},
    },
    {
        "doc_id": "proj_zkrat",
        "content": "Škola vydává školní časopis Zkrat, ve kterém se studenti mohou dočíst o dění ve škole i mimo ni. Časopis vytváří žáci a píšou o aktuálních událostech.",
        "metadata": {"kategorie": "projekty", "typ": "casopis"},
    },
    {
        "doc_id": "proj_burza",
        "content": "Naši studenti se na Burze firem pravidelně mohou seznámit s významnými firmami v regionu. Jde o networking událost spojující školu s praxí.",
        "metadata": {"kategorie": "projekty", "typ": "burza"},
    },
    {
        "doc_id": "proj_myty",
        "content": "Škola realizuje projekt 'Boříme mýty! Technika je i pro holky!'. Ukazujeme, že technické obory jsou opravdu pro každého a všichni si u nás najdou přesně to, co je baví.",
        "metadata": {"kategorie": "projekty", "typ": "rovnost", "cilova_skupina": "dívky"},
    },
    # ── PARTNEŘI ──────────────────────────────────────────────────────────────────
    {
        "doc_id": "partner_001",
        "content": "Mezi partnery školy patří významné firmy: ČEPS, Skupina ČEZ, Magna Liberec, Applic, Aries, Kopos a STAP a.s. Škola je partnerskou školou 'ČEZ čistá energie zítřka'.",
        "metadata": {"kategorie": "partnerstvi", "typ": "firmy"},
    },
    # ── SLUŽBY PRO STUDENTY ──────────────────────────────────────────────────────
    {
        "doc_id": "event_dod",
        "content": "Škola pravidelně pořádá Dny otevřených dveří pro zájemce o studium. Poslední se konal 17. ledna 2025, kde se mohli budoucí studenti seznámit se školou a obory.",
        "metadata": {"kategorie": "udalosti", "typ": "dod"},
    },
    {
        "doc_id": "about_zrizovatel",
        "content": "Zřizovatelem školy je Liberecký kraj. Škola je příspěvková organizace zřízená krajem pro poskytování středního a vyššího odborného vzdělávání.",
        "metadata": {"kategorie": "o_skole", "typ": "zrizovatel"},
    },
]


# ── Loader ──────────────────────────────────────────────────────────────────────
def load_documents() -> None:
    added = 0
    failed = 0

    for entry in DOCUMENTS:
        try:
            issued_id = add_document_to_db(
                content=entry["content"],
                metadata=entry.get("metadata"),
                doc_id=entry.get("doc_id"),
            )
            logger.info(f"Loaded document '{issued_id}'")
            added += 1
        except Exception as exc:
            logger.error(f"Failed to load document '{entry.get('doc_id')}': {exc}")
            failed += 1

    stats = get_db_stats()
    logger.info(
        f"Done - added/updated: {added}, failed: {failed}. "
        f"DB total: {stats.get('count', '?')} documents."
    )


if __name__ == "__main__":
    load_documents()
