"""Dane jednej edycji BOGO — jedyny plik zmieniany co promocję.

Z tych danych `python3 generuj.py` robi: index.html (PLN), index-eur.html (EUR), og.html
(+ render podglądu linku) i stronę rejestracji z pakietem w ../new-client-offer/<OFERTA["folder"]>/.
"""

MIESIAC = "2026-10"  # RRRR-MM: prefiks zdjęć w images/, nazwa grafiki podglądu linku
OKRES = "20–27 października 2026"
OKRES_KROTKO = "20–27.10.2026"
OKRES_WARUNKI = "20 do 27 października 2026 r."
KONIEC = "27 października"
POPRZEDNIA = ("2026-07", "BOGO lipiec 2026")  # (folder archiwum, podpis linku w stopce)
PREZENT_NAZWA = "olejek z daglezji zielonej"  # mianownik, małą literą
PREZENT_KROTKO = "daglezja zielona"  # do pilla na grafice podglądu linku
# dodatkowe punkty w „Warunkach promocji” (np. produkty z oferty ograniczonej czasowo)
WARUNKI_EXTRA = ["Waleriana (15 ml) i olejek do kąpieli Adaptiv to produkty z oferty ograniczonej czasowo."]
# przypis do cen szacunkowych: dopełniacz nazwy produktu („… nie ma jeszcze w cenniku”)
SZACUNEK_DOPELNIACZ = "olejku do kąpieli Adaptiv"
DATA_CEN = {"pln": "27.10.2026", "eur": "27.10.2026"}  # baza aroma-pricing (PL i DE)

# Produkty promocji. Nazwa = polska z aroma_product_localizations / broszury.
#   pln, eur  — cena hurtowa brutto (PL: wholesale_gross z bazy; DE: „EK-Preis”), None = brak ceny
#   en        — nazwa angielska do doterra-image.py
#   slug      — slug Canvy (canva/materialy/<slug>/, canva/hasla/output/<slug>.html)
#   krotko    — nazwa na stronie rejestracji (new-client-offer)
#   foto      — packshot PNG w ../new-client-offer/<folder>/images/ i zrodla-<MIESIAC>/produkty/
#   ig        — (opcjonalnie) nazwa na grafice Instagram, gdy inna niż `krotko` bez „dōTERRA” i „™”
PRODUKTY = {
    "Kozłek lekarski (waleriana)": dict(pln=290.00, eur=63.75, en="Valerian", slug="valerian", krotko="Waleriana", foto="waleriana.png"),
    "dōTERRA Serenity™": dict(pln=221.74, eur=48.75, en="Serenity", slug="serenity", krotko="dōTERRA Serenity™", foto="serenity.png"),
    "On Guard™": dict(pln=205.75, eur=45.26, en="On Guard", slug="on-guard", krotko="On Guard™", foto="onguard.png"),
    "Oregano": dict(pln=162.50, eur=35.75, en="Oregano", slug="oregano", krotko="Oregano", foto="oregano.png"),
    "Air-X™": dict(pln=179.75, eur=39.50, en="Air-X", slug="air-x", krotko="Air-X™", foto="airx.png"),
    "Eukaliptus": dict(pln=107.00, eur=23.50, en="Eucalyptus", slug="eucalyptus", krotko="Eukaliptus", foto="eukaliptus.png"),
    "Rumianek rzymski": dict(pln=273.99, eur=60.25, en="Roman Chamomile", slug="roman-chamomile", krotko="Rumianek rzymski", foto="rumianek.png"),
    # do 27.10 szacunek 115 zł / 25,29 €; cena z cennika od 27.10 (baza aroma-pricing, item 60213519)
    "Olejek do kąpieli dōTERRA Adaptiv™": dict(pln=100.00, eur=22.00, en="Adaptiv Calming Bath Oil", slug="adaptiv-bath-oil", krotko="Olejek do kąpieli Adaptiv™", foto="adaptiv.png", ig="Adaptiv do kąpieli"),
    "Sandałowiec": dict(pln=489.00, eur=107.50, en="Sandalwood", slug="sandalwood", krotko="Sandałowiec", foto="sandalowiec.png"),
    "Grejpfrut": dict(pln=105.76, eur=23.25, en="Grapefruit", slug="grapefruit", krotko="Grejpfrut", foto="grejpfrut.png"),
    "dōTERRA SuperMint™": dict(pln=168.25, eur=37.00, en="SuperMint", slug="supermint", krotko="dōTERRA SuperMint™", foto="supermint.png"),
    "dōTERRA Shinrin-Yoku™ Touch": dict(pln=119.49, eur=26.25, en="Shinrin-Yoku Touch", slug="shinrin-yoku", krotko="dōTERRA Shinrin-Yoku™ Touch", foto="shinrin-yoku.png"),
    "Daglezja zielona (Douglas Fir)": dict(pln=129.49, eur=28.50, en="Douglas Fir", slug="douglas-fir", krotko="Daglezja zielona", foto="daglezja.png"),
    # gratisy miesięcznej promocji rejestracji (200 PV) — tylko na stronie rejestracji
    "Wild Orange": dict(pln=76.25, eur=16.76, en="Wild Orange", slug="wild-orange", krotko="Wild Orange", foto="wild-orange.png", ig="Dzika pomarańcza"),
    "dōTERRA Balance™": dict(pln=137.50, eur=30.25, en="Balance", slug="balance", krotko="dōTERRA Balance™", foto="balance.png"),
}

# pozycja: (nazwa z PRODUKTY, pojemność, PV albo None, ilość)
# Cena i PV zestawu = cena i PV produktu kupowanego. `krotko` tylko dla zestawu z ceną None.
ZESTAWY = [
    {
        "foto": "images/2026-10-zestaw1-waleriana-serenity.jpg",
        "kup": ("Kozłek lekarski (waleriana)", "15 ml", 56.0, 1),
        "gratis": [("dōTERRA Serenity™", "15 ml", 47.0, 1)],
        "tytul": "Waleriana <span>+</span> dōTERRA Serenity™",
        "tytul_en": "Valerian <span>+</span> dōTERRA Serenity™",
        "tytul_de": "Baldrian <span>+</span> dōTERRA Serenity™",
    },
    {
        "foto": "images/2026-10-zestaw2-onguard-oregano.jpg",
        "kup": ("On Guard™", "15 ml", 43.5, 1),
        "gratis": [("Oregano", "15 ml", 34.5, 1)],
        "tytul": "On Guard™ <span>+</span> Oregano",
        "tytul_en": "On Guard™ <span>+</span> Oregano",
        "tytul_de": "On Guard™ <span>+</span> Oregano",
    },
    {
        "foto": "images/2026-10-zestaw3-airx-eukaliptus.jpg",
        "kup": ("Air-X™", "15 ml", 38.0, 1),
        "gratis": [("Eukaliptus", "15 ml", 22.5, 1)],
        "tytul": "Air-X™ <span>+</span> Eukaliptus",
        "tytul_en": "Air-X™ <span>+</span> Eucalyptus",
        "tytul_de": "Air-X™ <span>+</span> Eukalyptus",
    },
    {
        "foto": "images/2026-10-zestaw4-rumianek-adaptiv-kapiel.jpg",
        "kup": ("Rumianek rzymski", "5 ml", 58.0, 1),
        "gratis": [("Olejek do kąpieli dōTERRA Adaptiv™", "118 ml", None, 2)],
        "tytul": "Rumianek rzymski <span>+</span> 2 × olejek do kąpieli Adaptiv™",
        "tytul_en": "Roman Chamomile <span>+</span> 2 × Adaptiv™ Calming Bath Oil",
        "tytul_de": "Römische Kamille <span>+</span> 2 × Adaptiv™ Beruhigendes Badeöl",
        "krotko": "2 × olejek do kąpieli Adaptiv",
    },
    {
        "foto": "images/2026-10-zestaw5-sandalowiec.jpg",
        "kup": ("Sandałowiec", "5 ml", 97.0, 1),
        "gratis": [
            ("Grejpfrut", "15 ml", 22.5, 1),
            ("dōTERRA SuperMint™", "15 ml", 36.0, 1),
            ("dōTERRA Shinrin-Yoku™ Touch", "10 ml", 25.5, 1),
        ],
        "tytul": "Sandałowiec <span>+</span> Grejpfrut, SuperMint™, Shinrin-Yoku™ Touch",
        "tytul_en": "Sandalwood <span>+</span> Grapefruit, SuperMint™, Shinrin-Yoku™ Touch",
        "tytul_de": "Sandelholz <span>+</span> Grapefruit, SuperMint™, Shinrin-Yoku™ Touch",
    },
]
# ceny przyjęte szacunkowo (produktu nie ma jeszcze w cenniku PL)
SZACUNKOWE = set()
PREZENT = ("Daglezja zielona (Douglas Fir)", "5 ml")  # gratis do całego pakietu
FOTO_PAKIET = "images/2026-10-pakiet.jpg"
FOTO_PREZENT = "images/2026-10-gratis-daglezja.jpg"

# Wersja angielska strony (index-en.html, ceny EUR) — dla grupy WhatsApp „BOGO ENG od Claude”.
# Tytuły zestawów: "tytul_en" w ZESTAWY; nazwy produktów: NAZWY_EN, a gdy brak — pole `en` z PRODUKTY.
EN = dict(
    okres="20–27 October 2026",
    okres_warunki="20 to 27 October 2026",
    koniec="27 October",
    prezent_nazwa="Douglas Fir essential oil",
    prezent_krotko="Douglas Fir",
    poprzednia=None,  # (folder, podpis) poprzedniej edycji z index-en.html; None = bez linku
    warunki_extra=["Valerian (15 ml) and dōTERRA Adaptiv™ Calming Bath Oil are limited-time offer products."],
    szacunek="dōTERRA Adaptiv™ Calming Bath Oil",  # odpowiednik SZACUNEK_DOPELNIACZ
    # strona rejestracji EN (new-client-offer/<folder>/index-en.html, ceny EUR)
    miesiac="October 2026",
    rzeczownik_kup="oils",
    gratisy_opis="6 oils and 2 Adaptiv bath oils (BOGO), Douglas Fir (with the bundle), Wild Orange and Balance (enrollment from 200 PV)",
)
NAZWY_EN = {
    "dōTERRA Serenity™": "dōTERRA Serenity™",
    "On Guard™": "dōTERRA On Guard™",
    "Air-X™": "dōTERRA Air-X™",
    "Olejek do kąpieli dōTERRA Adaptiv™": "dōTERRA Adaptiv™ Calming Bath Oil",
    "dōTERRA SuperMint™": "dōTERRA SuperMint™",
    "dōTERRA Shinrin-Yoku™ Touch": "dōTERRA Shinrin-Yoku™ Touch",
    "dōTERRA Balance™": "dōTERRA Balance™",
}

# Wersja niemiecka (index-de.html, ceny EUR) — dla grupy WhatsApp „BOGO DE od Claude”. Forma „Sie” jak w doTERRA DE.
# Nazwy produktów: aroma_product_localizations dla cennika DE (price_list_id 24).
DE = dict(
    okres="20.–27. Oktober 2026",
    okres_warunki="20. bis 27. Oktober 2026",
    koniec="27. Oktober",
    prezent_nazwa="Douglasienöl",
    prezent_krotko="Douglasie",
    poprzednia=None,
    warunki_extra=["Baldrian (15 ml) und dōTERRA Adaptiv™ Beruhigendes Badeöl sind Produkte aus einem zeitlich begrenzten Angebot."],
    szacunek="dōTERRA Adaptiv™ Beruhigendes Badeöl",
    miesiac="Oktober 2026",
    rzeczownik_kup="Öle",
    gratisy_opis="6 Öle und 2 Adaptiv Badeöle (BOGO), Douglasie (zum Paket), Wild Orange und Balance (Einschreibung ab 200 PV)",
)
NAZWY_DE = {
    "Kozłek lekarski (waleriana)": "Baldrian",
    "dōTERRA Serenity™": "dōTERRA Serenity™",
    "On Guard™": "dōTERRA On Guard™",
    "Oregano": "Oregano",
    "Air-X™": "dōTERRA Air-X™",
    "Eukaliptus": "Eukalyptus",
    "Rumianek rzymski": "Römische Kamille",
    "Olejek do kąpieli dōTERRA Adaptiv™": "dōTERRA Adaptiv™ Beruhigendes Badeöl",
    "Sandałowiec": "Sandelholz",
    "Grejpfrut": "Grapefruit",
    "dōTERRA SuperMint™": "dōTERRA SuperMint™",
    "dōTERRA Shinrin-Yoku™ Touch": "dōTERRA Shinrin-Yoku™ Touch",
    "Daglezja zielona (Douglas Fir)": "Douglasie",
    "Wild Orange": "Wild Orange",
    "dōTERRA Balance™": "dōTERRA Balance™",
}
# wersje obcojęzyczne stron (ceny EUR): teksty edycji + nazwy produktów
WERSJE = {"en": dict(EN, nazwy=NAZWY_EN), "de": dict(DE, nazwy=NAZWY_DE)}

# Strona rejestracji z pakietem BOGO: ../new-client-offer/<folder>/
OFERTA = {
    "folder": "pazdziernik-bogo",
    "miesiac": "Październik 2026",
    "rzeczownik_kup": "olejków",  # „5 olejków” — zmień, gdy w pakiecie są nie tylko olejki
    # gratisy miesięcznej promocji rejestracji (z bieżącej oferty miesiąca, np. new-client-offer/pazdziernik/)
    "gratis_200pv": [("Wild Orange", "15 ml"), ("dōTERRA Balance™", "15 ml")],
    # opis gratisów słowami (og:description, karty w hubach) — liczby i kwoty wstawia generator
    "gratisy_opis": "6 olejków i 2 olejki do kąpieli Adaptiv (BOGO), daglezja zielona (do pakietu), Wild Orange i Balance (rejestracja od 200 PV)",
    "gratisy_hub": "BOGO, daglezja, Wild Orange, Balance",
}
