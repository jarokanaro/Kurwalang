# Changelog

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
