# Changelog

## v1.12 ANALYZE - konserwatywna analiza przepływu

- rozszerzono wspólną ścieżkę `sprawdz_kurwa` o analizę AST ścieżek sterowania i stanów zmiennych,
- dodano stałe propagowane przez proste wyrażenia, diagnozę niemożliwych gałęzi i wybranych nieosiągalnych instrukcji,
- dodano relacje wywołań, wykrywanie rekurencji oraz konserwatywne podsumowania mutacji i efektów zewnętrznych,
- dodano kody `A001`, `A010`, `A020` i `A031` we współdzielonym formacie diagnostycznym,
- utrzymano brak wykonania programu, ładowania importów, rozszerzeń i paczek podczas analizy,
- dodano testy przepływu, gałęzi, pętli, funkcji, efektów, CLI i gwarancji braku wykonania.

## v1.11 TYPE - static analysis without execution

- dodano prostą inferencję typu w `src/linter.py` opartej na AST,
- dodano diagnostykę `T010`/`T020`/`T030`/`T040` w tej samej warstwie statycznej,
- zachowano brak wykonania kodu użytkownika podczas `sprawdz_kurwa`,
- pozostawiono publiczne API bez funkcji typu/typowania/annotation syntax,
- dodano testy no-execution i podstawowej inferencji dla list/map/logic/return paths,
- zaktualizowano dokumentację `docs/types.md`, `docs/linting.md` i `README.md`.

## v1.5 ERROR - runtime error handling

- dodano składnię `wjebaj { ... } zlap_kurwa zmienna { ... } wyczysc_kurwa { ... }`,
- dodano `wyrzuc_kurwa "tekst"` jako użytkownikowo generowany runtime error,
- dodano strukturalne błędy runtime z polami `typ_kurwa`, `wiadomosc_kurwa` i `zrodlo_kurwa`,
- dodano propagację błędów przez funkcje, moduły, standard library i pakiety,
- dodano cleanup semantics i obsługę przechwycenia błędów bez rozbijania reszty języka,
- dodano testy regresyjne i przykłady w `examples/errors/`,
- zaktualizowano dokumentację publicznego API, architekturę i konwencje nazewnictwa.

## v1.4.0 - PACK / package manager

- dodano projektowe manifesty `kurwa.pack` i lockfile `kurwa.lock`,
- dodano katalog instalacyjny `.kurwa_packages/` i integrację z `ModuleLoader`,
- dodano CLI `init`, `install`, `uninstall`, `list`, `update`,
- dodano walidację zależności, konfliktów wersji i cykli,
- dodano bezpieczeństwo ścieżek i blokadę path traversal,
- dodano przykłady pakietów w `examples/packages/`,
- zaktualizowano dokumentację architektury, roadmapy i publicznego API.

## v1.3.0 - HTTP / networking

- dodano moduł `siec` z obsługą `GET`, `POST`, `PUT`, `DELETE` i generic request,
- dodano `query parameters`, `headers`, `body`, `timeout`, `http://` i `https://`,
- dodano kontrolowane błędy timeout, DNS, połączenia, TLS, URL i nieprawidłowych parametrów/nagłówków,
- dodano response z `status_kurwa`, `tekst_kurwa`, `naglowki_kurwa`, `adres_kurwa`, `udalo_sie_kurwa` i `json_kurwa`,
- dodano testy lokalnego serwera HTTP i pełne przykłady `examples/http/`,
- zaktualizowano dokumentację publicznego API i konwencje nazewnictwa KURWA LANG.

## v1.2.0 - JSON i polonizacja API

- dodano serializację i deserializację JSON przez `dane.skurw` i `dane.odkurw`,
- dodano pretty JSON przez `dane.ładnie_skurw`,
- dodano zapis i odczyt JSON UTF-8 przez istniejący moduł `plik`,
- dodano obsługę map, list, wartości `brak_wyniku`, Unicode, escaping i wykrywanie cykli,
- odrzucono niepoprawne JSON oraz niestandardowe wartości `NaN` i `Infinity`,
- ujednolicono publiczne API jako polskie, slangowe lub charakterystyczne dla KURWA LANG.

## v1.1.0 - File I/O

- dodano moduły `plik`, `katalog` i `sciezka`,
- dodano odczyt, zapis, dopisywanie, usuwanie plików oraz operacje katalogowe,
- dodano UTF-8 i bezpieczne błędy dla braków plików, katalogów i typów,
- dodano przykłady `examples/file_io/` i aktualizację dokumentacji `docs/stdlib.md`.

## v1.0.0 - Standard Library

- dodano moduły `matematyka`, `losuj`, `tekst`, `czas` i `system`,
- dodano API matematyczne, tekstowe, losowe, czasowe i systemowe,
- dodano liczby zmiennoprzecinkowe,
- dodano jedno źródło wersji w `src/version.py`, CLI `--version` i `system.wersja()`,
- dodano dokumentację `docs/stdlib.md` i przykład `examples/stdlib/`.

## v0.9 - Modules & Imports

- dodano składnię `zajeb_moduł "nazwa"`,
- dodano namespace modułów przez `moduł.wartość`,
- dodano lokalne importy plików `.kurwa`,
- dodano własny scope modułów,
- dodano cache modułów i wykrywanie cyklicznych importów,
- dodano importy względne względem modułu importującego,
- dodano błędy z nazwą pliku modułu,
- dodano przykład `examples/modules/`.

## v0.8 - String 2.0

- dodano konkatenację, indeksowanie, slicing i built-iny tekstowe.
