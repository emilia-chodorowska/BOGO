"""Wspólne liczenie dla generuj.py i dodatki.py."""


def podzial(cena_zestawu, wartosci):
    """Proporcjonalny podział ceny zestawu na pozycje o podanych wartościach, suma co do grosza."""
    if any(v is None for v in wartosci):
        return [None] * len(wartosci)
    total = sum(wartosci)
    grosze = round(cena_zestawu * 100)
    surowe = [grosze * v / total for v in wartosci]
    czesci = [int(s) for s in surowe]
    reszta = grosze - sum(czesci)
    for i in sorted(range(len(wartosci)), key=lambda i: surowe[i] - czesci[i], reverse=True)[:reszta]:
        czesci[i] += 1
    return [c / 100 for c in czesci]
