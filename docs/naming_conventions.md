# Konwencje nazewnictwa KURWA LANG

Publiczne API KURWA LANG jest częścią języka i używa polskich, slangowych albo charakterystycznych nazw. Backend Pythona może używać nazw technicznych po angielsku, ale nie są one widoczne w programach `.kurwa`.

## Keywordy v1.5, v1.6, v1.7 EXT i v1.11 TYPE

Nowe słowa użyte w v1.5, v1.6 i v1.7 zachowują tę samą zasadę i nie wprowadzają angielskich aliasów:

- `wjebaj`
- `zlap_kurwa`
- `wyczysc_kurwa`
- `wyrzuc_kurwa`
- `typ_kurwa`
- `wiadomosc_kurwa`
- `zrodlo_kurwa`
- `odpierdol_kurwicznie`
- `czekaj_kurwa`
- `wyjeb_task`
- `czekaj_wiele_kurwa`
- `kurwa_pauza`
- `zaladuj_rozszerzenie`
- `wywal_rozszerzenie`
- `rozszerzenia_kurwa`
- `metadane`

To są publiczne słowa języka KURWA LANG. Ich nazwy opisują wykonanie, przechwycenie, strukturę błędu, asynchroniczność i rozszerzalność po polsku i w stylu projektu. Nie ma angielskich odpowiedników w API języka. Nazwy takie jak `plugin`, `extension`, `register`, `hook` nie są publicznym API KURWA LANG i są zachowane wyłącznie wewnętrznie jako nazwy Pythonowe.

## Built-iny i runtime

Built-iny i runtime dalej utrzymują styl KURWA LANG, na przykład:

- `ile_kurwa`
- `jest_kurwa`
- `wielkie_kurwa`
- `tekst_kurwa`
- `dane.skurw`, `dane.odkurw`
- `siec.wjeb`, `siec.wyślij` itd.

Żaden z tych nazw nie ma angielskiego aliasu wspieranego jako interfejs publiczny.

## Przechwytywanie błędów

`zlap_kurwa` nie daje dostępu do angielskich nazw typu `error` lub `exception`. Zamiast tego runtime udostępnia mapę błędu z polami:

- `typ_kurwa`
- `wiadomosc_kurwa`
- `zrodlo_kurwa`

To zachowuje spójność z resztą API i nie tworzy konfliktu z zasadą: publiczne API = KURWA LANG.

## Moduły, pakiety i standard library

Konwencje z v1.4 nadal obowiązują:

- moduły są polskie, np. `matematyka`, `tekst`, `siec`, `plik`
- pakiety pozostają w tej samej hierarchii importów i nie tworzą osobnego systemu nazw
- projektowy manifest i lockfile nadal używają istniejących nazw oraz struktur

## Zasada projektowa

Przed dodaniem nowego API sprawdzamy:

1. czy nazwa pasuje do języka KURWA LANG,
2. czy nie wprowadzamy angielskiego aliasu,
3. czy nie tworzymy drugiego, niezależnego systemu importów albo błędów,
4. czy kontrakt jest zgodny z istniejącą implementacją,
5. czy nazwa jest spójna w dokumentacji, testach i przykładach.

v1.5 ERROR utrzymuje tę zasadę bez tworzenia osobnej, angielskiej warstwy publicznej.
