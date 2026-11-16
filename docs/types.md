# Typy runtime i statyczne typowanie v1.11

Interpreter rozróżnia następujące wartości runtime:

- `liczba` - liczba całkowita albo zmiennoprzecinkowa,
- `tekst` - tekst w cudzysłowie,
- `boolean` - `prawda` albo `fałsz`,
- `lista` - uporządkowana kolekcja wartości,
- `mapa` - kolekcja stringowych kluczy i dowolnych wartości KURWA LANG,
- `funkcja` - funkcja użytkownika albo built-in,
- `moduł` - namespace załadowanego pliku `.kurwa`,
- `brak_wyniku` - wynik zwracany przez funkcję bez `oddaj`,
- `task` / `async` - wartość asynchroniczna rozpoznawana tylko na poziomie obecnej implementacji, bez wykonywania zadań w analizatorze.

## Statyczna inferencja v1.11

`sprawdz_kurwa` wykonuje analizę AST bez uruchamiania programu. W praktyce:

- literały są inferowane do podstawowych typów,
- zmienne są śledzone w zakresie lokalnym,
- operacje arytmetyczne sprawdzają zgodność typu w znanych przypadkach,
- warunki logiczne są sprawdzane jako `boolean`,
- listy i mapy są rozpoznawane jako kolekcje z typowymi elementami,
- wywołania funkcji używają podstawowej inferencji zwrotów,
- przy niepewności używany jest stan `nieznane` zamiast fałszywej diagnozy.

## Diagnostyka typu

Typy używają kodów `T...` i współdzielą format diagnostyczny z lintem:

- `T010` — nieobsługiwany operator lub niezgodność operandów,
- `T020` — warunek ma typ inny niż `boolean`,
- `T030` — zwrot z funkcji nie zgadza się z typem funkcji,
- `T040` — nieprawidłowy typ indeksu, kolekcji albo slicingu.

## Ograniczenia v1.11

- nie ma publicznej składni adnotacji typu,
- `TYPE ANNOTATIONS: NOT IMPLEMENTED`,
- analiza nie wykonuje modułów, pakietów, rozszerzeń ani zadań asynchronicznych,
- nie ma pełnego systemu generycznego ani pełnej analizy zależności dla całego projektu.

## Zasada bezpieczeństwa

`sprawdz_kurwa` nie wykonuje programu. Nie wywołuje funkcji, nie ładuje rozszerzeń, nie uruchamia zadań, nie wysyła HTTP i nie zapisuje plików. To jest czysta analiza statyczna na AST.
