# KURWA LANG v1.10 LINT + v1.11 TYPE + v1.12 ANALYZE

KURWA LANG v1.10 dodaje warstwę statycznej analizy bez uruchamiania programu. v1.11 rozszerza ją o inferencję typów, a v1.12 o konserwatywną analizę przepływu. Jedno polecenie parsuje źródło do istniejącego AST, a następnie uruchamia reguły LINT, TYPE i ANALYZE.

## Publiczne CLI

```bash
python3 src/main.py sprawdz_kurwa plik.kurwa
python3 src/main.py sprawdz_kurwa katalog
python3 src/main.py sprawdz_kurwa katalog --quiet
python3 src/main.py sprawdz_kurwa katalog --verbose
```

Publiczna komenda jest KURWA-native: `sprawdz_kurwa`.

## Zasada bezpieczeństwa

Analiza NIE wykonuje programu. Nie wywołuje interpretera runtime ani funkcji KURWA, nie zapisuje plików, nie wysyła HTTP, nie uruchamia zadań, nie ładuje modułów ani rozszerzeń i nie instaluje paczek.

## Diagnostyka

Każda uwaga ma stabilny kod. Lint i typowanie są rozdzielone, ale współdzielą ten sam format diagnostyczny:

- `T010` — niezgodność operatora / nieobsługiwany typ
- `T020` — warunek logiczny ma nieprawidłowy typ
- `T030` — niezgodność typu zwrotu z funkcji
- `T040` — nieprawidłowy typ indeksu lub kolekcji

Diagnostyka typów i przepływu współdzieli ten sam format i CLI; nie powstaje osobny parser ani runtime.

- `K000` — błąd składniowy
- `K001` — zmienna zadeklarowana, ale nieużywana
- `K010` — niezdefiniowana zmienna
- `K020` — nieosiągalny kod po wyjściu
- `K030` — stały warunek
- `K031` — stały fałsz / zły warunek
- `K040` — statyczne dzielenie przez zero
- `K050` — zduplikowany klucz mapy
- `K060` — zduplikowany import

Kody przepływu v1.12:

- `A001` — nieosiągalna ścieżka
- `A010` — zmienna może nie być dostępna na każdej ścieżce
- `A020` — gałąź lub pętla niemożliwa przy znanym warunku
- `A031` — funkcja zwraca wartość tylko na części ścieżek
- `A012` — nazwa jest zasłonięta przez deklarację lokalną lub parametr
- `A040` — brakujący symbol lokalnego modułu / niedozwolone rozszerzenie ścieżki
- `A041` — cykl lokalnych importów
- `A042` — istniejący lock nie spełnia lokalnych wymogów manifestu
- `A043` — bezpośredni konflikt deklaracji funkcji w module

## Poziomy

- `warning` — ostrzeżenie, zwykle exit code 0
- `error` — błąd lintu, exit code 1

## Exit codes

- `0` — brak błędów lintu
- `1` — co najmniej jeden błąd lintu
- `2` — brak plików do sprawdzenia lub błędna komenda

## Limitacje

Analiza pozostaje konserwatywna: nie rozstrzyga dowolnych wywołań, pełnych zależności między modułami ani efektów rozszerzeń. Szczegółowe reguły i ograniczenia v1.12 opisuje [static_analysis.md](static_analysis.md).
