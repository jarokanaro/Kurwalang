# Funkcje

Definicja funkcji używa przeklętej składni:

```text
odpierdol funkcja stworz_osobe(imie, wiek) {
    kurwa osoba = {"imie": imie, "wiek": wiek}
    oddaj osoba
}
```

Funkcje mają lokalne środowisko z dostępem do zakresu, w którym zostały zdefiniowane. Parametry są lokalne. Funkcje mogą wywoływać same siebie i przyjmować lub zwracać listy, mapy oraz booleany.

Funkcja bez `oddaj` zwraca `brak_wyniku`. Dostępne built-iny to:

- `ile_kurwa(kolekcja)` - długość listy lub mapy,
- `jest_kurwa(mapa, klucz)` - sprawdzenie istnienia stringowego klucza.
