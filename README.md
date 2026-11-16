
# KURWA LANG

KURWA LANG to interpreter z polską, slangową składnią. Aktualna warstwa statyczna v1.12 ANALYZE rozszerza lint i inferencję typów o konserwatywne fakty przepływu, bez uruchamiania kodu. Zachowuje ten sam model `Lexer -> Parser -> AST -> Interpreter` bez drugiego parsera ani runtime.

## v1.12 ANALYZE — statyczna analiza przepływu

- `sprawdz_kurwa <plik.kurwa|katalog>` pozostaje jedynym wejściem CLI do statycznej analizy,
- analiza rozpoznaje nieosiągalne ścieżki, warunki stałe i zmienne dostępne tylko na części ścieżek,
- bezpiecznie propaguje proste stałe i zachowuje relacje wywołań oraz przybliżone skutki funkcji,
- parsuje istniejący AST i współdzieli diagnostykę z LINT (`K...`) i TYPE (`T...`), dodając kody przepływu `A...`,
- importy, paczki i rozszerzenia nie są ładowane; nierozstrzygnięte zachowanie pozostaje nieznane.

Szczegóły, granice dowodzenia i przykłady: [docs/static_analysis.md](docs/static_analysis.md).

## v1.11 TYPE — statyczne typowanie

- `sprawdz_kurwa <plik.kurwa>` pozostaje głównym wejściem do analizy statycznej,
- analiza działa wyłącznie na AST i nie wykonuje programu,
- rozpoznawane są typy podstawowe: `liczba`, `tekst`, `boolean`, `lista`, `mapa`, `funkcja`, `brak_wyniku`,
- w razie niepewności używany jest stan `nieznane` zamiast fałszywego ostrzeżenia,
- typy są generowane przez inferencję, nie przez składnię adnotacji,
- `TYPE ANNOTATIONS: NOT IMPLEMENTED` w publicznym API KURWA LANG.

## v1.5 ERROR — przykład

## v1.5 ERROR — przykład

```text
program {
    wjebaj {
        wyrzuc_kurwa "co ty odpierdalasz"
    } zlap_kurwa blad {
        pierdol blad["typ_kurwa"]
        pierdol blad["wiadomosc_kurwa"]
    } wyczysc_kurwa {
        wypierdol "cleanup"
    }
}
```

Powyższy kod wykonuje się poprawnie i dostarcza zmapowany błąd runtime z polami:

- `typ_kurwa`
- `wiadomosc_kurwa`
- `zrodlo_kurwa`

## v1.6 ASYNC — przykład

```text
program {
    odpierdol_kurwicznie funkcja slow() {
        kurwa_pauza(0.05)
        oddaj "gotowe"
    }

    kurwa wynik = czekaj_kurwa(slow())
    pierdol wynik
}
```

To jest w praktyce realny model współbieżności z zadaniami i oczekiwaniem na wynik, ale publiczne API pozostaje w stylu KURWA LANG, bez `async`/`await`/`task`.

Dla osób, które chcą zobaczyć pełny opis i szczegóły, patrz [docs/errors.md](docs/errors.md), [docs/async.md](docs/async.md), [docs/language_reference.md](docs/language_reference.md) i [docs/architecture.md](docs/architecture.md).

## Uruchomienie

```bash
python3 src/main.py examples/test.kurwa
python3 src/main.py --version
python3 src/main.py init
python3 src/main.py install examples/packages/mathz
python3 src/main.py list
python3 src/main.py update
python3 src/main.py uninstall mathz
```

## Pakiet i moduły

- `zajeb_moduł "nazwa"` nadal jest głównym mechanizmem importu,
- `ModuleLoader` integruje lokalne moduły, standard library i pakiety projektowe,
- `kurwa.pack` / `kurwa.lock` i `.kurwa_packages/` są nadal częścią tego samego systemu importów.

## Przykłady

- [examples/modules](examples/modules)
- [examples/file_io](examples/file_io)
- [examples/json](examples/json)
- [examples/stdlib](examples/stdlib)
- [examples/errors](examples/errors)

## Testy i budowa

```bash
python3 -m unittest discover -s tests -q
python3 -m compileall src
```

## v1.9 TEST — native KURWA test syntax

```text
program {
    testuj_kurwa "dodawanie" {
        sprawdz_kurwa 2 + 2 == 4
        sprawdz_kurwa 5 > 3
        sprawdz_kurwa 1 != 2
    }

    testuj_kurwa "błąd oczekiwany" {
        oczekuj_blad_kurwa {
            wyrzuc_kurwa "to ma się wydarzyć"
        }
    }
}
```

Uruchomienie z CLI:

```bash
python3 src/main.py testuj_kurwa tests/kurwa
python3 src/main.py testuj_kurwa tests/kurwa/demo.kurwa
python3 src/main.py testuj_kurwa tests/kurwa --filter "dodawanie"
```

Publiczne testowe konstrukcje to `testuj_kurwa`, `sprawdz_kurwa`, `oczekuj_blad_kurwa` i `pomin_kurwa`. Nie dodaje się angielskiego publicznego API typu `assert`/`it`/`describe`.

Status projektu jest stabilny dla v1.5 ERROR i nie dodaje osobnej, niezależnej architektury błędów czy VM.
