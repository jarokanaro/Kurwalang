# KURWA LANG v1.9 TEST

KURWA LANG v1.9 dostarcza natywne testy w tej samej składni co reszta języka. Nie tworzy osobnego frameworku, nie dodaje angielskiego publicznego API i nie tworzy drugiego runtime.

## Publiczna składnia

```text
program {
    testuj_kurwa "dodawanie" {
        sprawdz_kurwa 2 + 2 == 4
        sprawdz_kurwa 5 > 3
        sprawdz_kurwa 1 != 2
    }

    testuj_kurwa "błąd oczekiwany" {
        oczekuj_blad_kurwa {
            wyrzuc_kurwa "kurwa"
        }
    }

    testuj_kurwa "pominięty" {
        pomin_kurwa "tymczasowo wyłączone"
    }
}
```

## Konstrukcje

- `testuj_kurwa "nazwa" { ... }` — deklaracja testu
- `sprawdz_kurwa wyrażenie` — asercja logiczna
- `oczekuj_blad_kurwa { ... }` — blok, który ma zakończyć się błędem
- `pomin_kurwa "powód"` — pominięcie testu z komunikatem

## CLI

```bash
python3 src/main.py testuj_kurwa tests/kurwa
python3 src/main.py testuj_kurwa tests/kurwa/demo.kurwa
python3 src/main.py testuj_kurwa tests/kurwa --filter "dodawanie"
```

## Test discovery

CLI rozpoznaje plik `.kurwa` albo katalog i automatycznie wyszukuje wszystkie pliki `*.kurwa` w poddrzewie katalogu. Filtr `--filter "nazwa"` ogranicza wykonanie do konkretnego testu.

## Status wyjścia

- `0` — wszyscy uruchomieni testy przeszli
- `1` — co najmniej jeden test nie przeszedł
- `2` — nie znaleziono plików testowych lub brak komendy

## Public naming audit

Publiczne API testów pozostaje w stylu KURWA LANG. Nie używa się angielskich nazw typu `assert`, `it`, `describe`, `expect`, `test` jako publicznej składni użytkownika.
