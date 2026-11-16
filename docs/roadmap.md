# Roadmapa

## Ukończone

- v0.1: lexer, AST, parser i interpreter
- v0.2: arytmetyka i porównania
- v0.3: `jeśli`, `inaczej`, `dopóki`, `wypierdalaj`
- v0.4: funkcje, zakresy, `oddaj`, rekurencja
- v0.5: listy, indeksowanie i operacje listowe
- v0.6: booleany, `i`, `albo`, `nie`, short-circuit
- v0.7: mapy, nested kolekcje, `jest_kurwa`
- v0.8: String 2.0, indeksowanie, slicing, funkcje tekstowe i konwersje
- v0.9: moduły, importy, namespace, scope modułów, cache i cykle
- v1.0.0: standard library `matematyka`, `losuj`, `tekst`, `czas`, `system`
- v1.1.0: file I/O (`plik`, `katalog`, `sciezka`), UTF-8 i bezpieczny dostęp do systemu plików
- v1.2.0: JSON (`dane`), JSON File I/O, Unicode, escaping i audyt publicznego API
- v1.3.0: HTTP/networking (`siec`), timeout, statusy, headers, query params, body, JSON request/response i testy lokalne
- v1.4.0: PACK / package manager (`kurwa.pack`, `kurwa.lock`, `.kurwa_packages`), init/install/uninstall/list/update, integracja modułów, walidacja zależności i bezpieczeństwo ścieżek
- v1.5 ERROR: `wjebaj`, `zlap_kurwa`, `wyczysc_kurwa`, `wyrzuc_kurwa`, strukturalne runtime błędy, propagacja, cleanup i integracja z modułami, JSON, plikami i HTTP
- v1.6 ASYNC: `odpierdol_kurwicznie`, `czekaj_kurwa`, `wyjeb_task`, `czekaj_wiele_kurwa`, `kurwa_pauza`, współbieżne zadania i integracja z błędami runtime
- v1.10 LINT: statyczny lint AST bez uruchamiania kodu
- v1.11 TYPE: prosty static type inference na tym samym AST, bez adnotacji i bez wykonania programu
- v1.12 ANALYZE: konserwatywna analiza przepływu, dostępności zmiennych, stałych, wywołań i skutków na istniejącym AST

## Kolejne etapy

- v1.13 STD2: dalsza rozbudowa biblioteki standardowej
- rozszerzenie VS Code
- debugger i narzędzia rozwoju
- v2.x: dalszy rozwój języka bez zmiany obecnej architektury

v1.5 ERROR jest już zaimplementowane i zweryfikowane przez testy oraz kompilację. Nie zaczynamy nowej linii rozwoju bez pełnej weryfikacji obecnej wersji.
