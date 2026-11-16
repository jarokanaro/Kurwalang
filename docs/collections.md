# Kolekcje

## Listy

```text
kurwa lista = [10, 20, 30]
pierdol lista[0]
lista[1] = 99
wpierdol lista 40
kurwa ostatnia = wypierdol_z_listy lista
pierdol ile_kurwa(lista)
```

Indeksy list zaczynają się od zera i muszą być liczbami w zakresie listy.

## Mapy

```text
kurwa osoba = {
    "imie": "Jaro",
    "wiek": 19,
    "aktywny": prawda
}

pierdol osoba["imie"]
osoba["wiek"] = 20
osoba["miasto"] = "Opole"
wypierdol_z_mapy osoba "wiek"

jeśli jest_kurwa(osoba, "imie") {
    wypierdol "Jest imie"
}
```

Mapy można zagnieżdżać i przechowywać w listach. Klucze literalów map muszą być stringami. `ile_kurwa` zwraca liczbę elementów listy albo mapy.

Stringi są również indeksowalnymi kolekcjami znaków: `tekst[0]` zwraca znak, a `tekst[0:3]` fragment `[0, 3)`. Indeksy są nieujemne.
