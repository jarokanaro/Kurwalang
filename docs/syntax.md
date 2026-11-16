# Składnia

Program zaczyna się od `program` i bloku klamrowego:

```text
program {
    kurwa x = 10
    pierdol x
}
```

## Zmienne i instrukcje

```text
kurwa nazwa = wyrażenie
zajeb nazwa 1
wypierdol wyrażenie
pierdol wyrażenie
spierdalaj
```

Warunki i pętle:

```text
jeśli warunek { ... } inaczej { ... }
dopóki warunek { ... }
wypierdalaj
```

Funkcje:

```text
odpierdol funkcja dodaj(a, b) {
    oddaj a + b
}
kurwa wynik = dodaj(2, 3)
```

Mapy używają stringowych kluczy i dwukropka:

```text
kurwa osoba = {"imie": "Jaro", "wiek": 19}
osoba["wiek"] = 20
pierdol osoba["wiek"]
```

## Moduły

```text
zajeb_moduł "matematyka"
kurwa wynik = matematyka.dodaj(10, 20)
```

Nazwa bez rozszerzenia szuka pliku `matematyka.kurwa`. Nazwa z innym rozszerzeniem jest błędem. Moduły mogą zawierać `program { ... }` albo instrukcje top-level.
