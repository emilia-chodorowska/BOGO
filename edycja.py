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
DATA_CEN = {"pln": "17.10.2026", "eur": "18.10.2026"}

# Produkty promocji. Nazwa = polska z aroma_product_localizations / broszury.
#   pln, eur  — cena hurtowa brutto (PL: wholesale_gross z bazy; DE: „EK-Preis”), None = brak ceny
#   en        — nazwa angielska do doterra-image.py
#   slug      — slug Canvy (canva/materialy/<slug>/, canva/hasla/output/<slug>.html)
#   krotko    — nazwa na stronie rejestracji (new-client-offer)
#   foto      — packshot PNG w ../new-client-offer/<folder>/images/
PRODUKTY = {
    "Kozłek lekarski (waleriana)": dict(pln=290.00, eur=63.75, en="Valerian", slug="valerian", krotko="Waleriana", foto="waleriana.png"),
    "dōTERRA Serenity™": dict(pln=221.74, eur=48.75, en="Serenity", slug="serenity", krotko="dōTERRA Serenity™", foto="serenity.png"),
    "On Guard™": dict(pln=205.75, eur=45.26, en="On Guard", slug="on-guard", krotko="On Guard™", foto="onguard.png"),
    "Oregano": dict(pln=162.50, eur=35.75, en="Oregano", slug="oregano", krotko="Oregano", foto="oregano.png"),
    "Air-X™": dict(pln=179.75, eur=39.50, en="Air-X", slug="air-x", krotko="Air-X™", foto="airx.png"),
    "Eukaliptus": dict(pln=107.00, eur=23.50, en="Eucalyptus", slug="eucalyptus", krotko="Eukaliptus", foto="eukaliptus.png"),
    "Rumianek rzymski": dict(pln=273.99, eur=60.25, en="Roman Chamomile", slug="roman-chamomile", krotko="Rumianek rzymski", foto="rumianek.png"),
    # szacunek, EUR = 115 zł / 4,547
    "Olejek do kąpieli dōTERRA Adaptiv™": dict(pln=115.00, eur=25.29, en="Adaptiv Calming Bath Oil", slug="adaptiv", krotko="Olejek do kąpieli Adaptiv™", foto="adaptiv.png"),
    "Sandałowiec": dict(pln=489.00, eur=107.50, en="Sandalwood", slug="sandalwood", krotko="Sandałowiec", foto="sandalowiec.png"),
    "Grejpfrut": dict(pln=105.76, eur=23.25, en="Grapefruit", slug="grapefruit", krotko="Grejpfrut", foto="grejpfrut.png"),
    "dōTERRA SuperMint™": dict(pln=168.25, eur=37.00, en="SuperMint", slug="supermint", krotko="dōTERRA SuperMint™", foto="supermint.png"),
    "dōTERRA Shinrin-Yoku™ Touch": dict(pln=119.49, eur=26.25, en="Shinrin-Yoku Touch", slug="shinrin-yoku", krotko="dōTERRA Shinrin-Yoku™ Touch", foto="shinrin-yoku.png"),
    "Daglezja zielona (Douglas Fir)": dict(pln=129.49, eur=28.50, en="Douglas Fir", slug="douglas-fir", krotko="Daglezja zielona", foto="daglezja.png"),
    # gratisy miesięcznej promocji rejestracji (200 PV) — tylko na stronie rejestracji
    "Wild Orange": dict(pln=76.25, eur=None, en="Wild Orange", slug="wild-orange", krotko="Wild Orange", foto="wild-orange.png"),
    "dōTERRA Balance™": dict(pln=137.50, eur=None, en="Balance", slug="balance", krotko="dōTERRA Balance™", foto="balance.png"),
}

# pozycja: (nazwa z PRODUKTY, pojemność, PV albo None, ilość)
# Cena i PV zestawu = cena i PV produktu kupowanego. `krotko` tylko dla zestawu z ceną None.
ZESTAWY = [
    {
        "foto": "images/2026-10-zestaw1-waleriana-serenity.jpg",
        "kup": ("Kozłek lekarski (waleriana)", "15 ml", 56.0, 1),
        "gratis": [("dōTERRA Serenity™", "15 ml", 47.0, 1)],
        "tytul": "Waleriana <span>+</span> dōTERRA Serenity™",
    },
    {
        "foto": "images/2026-10-zestaw2-onguard-oregano.jpg",
        "kup": ("On Guard™", "15 ml", 43.5, 1),
        "gratis": [("Oregano", "15 ml", 34.5, 1)],
        "tytul": "On Guard™ <span>+</span> Oregano",
    },
    {
        "foto": "images/2026-10-zestaw3-airx-eukaliptus.jpg",
        "kup": ("Air-X™", "15 ml", 38.0, 1),
        "gratis": [("Eukaliptus", "15 ml", 22.5, 1)],
        "tytul": "Air-X™ <span>+</span> Eukaliptus",
    },
    {
        "foto": "images/2026-10-zestaw4-rumianek-adaptiv-kapiel.jpg",
        "kup": ("Rumianek rzymski", "5 ml", 58.0, 1),
        "gratis": [("Olejek do kąpieli dōTERRA Adaptiv™", "118 ml", None, 2)],
        "tytul": "Rumianek rzymski <span>+</span> 2 × olejek do kąpieli Adaptiv™",
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
    },
]
# ceny przyjęte szacunkowo (produktu nie ma jeszcze w cenniku PL)
SZACUNKOWE = {"Olejek do kąpieli dōTERRA Adaptiv™"}
PREZENT = ("Daglezja zielona (Douglas Fir)", "5 ml")  # gratis do całego pakietu
FOTO_PAKIET = "images/2026-10-pakiet.jpg"
FOTO_PREZENT = "images/2026-10-gratis-daglezja.jpg"

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
