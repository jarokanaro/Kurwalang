# KURWA LANG Language Reference

Wersja dokumentu: v1.12 ANALYZE. KURWA LANG jest interpretowanym językiem z polską, slangową składnią. Programy i moduły zapisuje się w plikach `.kurwa`, a paczki projektu korzystają z `kurwa.pack` i `kurwa.lock`.

## Szybki indeks

| Konstrukcja | Co robi |
|---|---|
| `program` | rozpoczyna program i jego blok |
| `kurwa` | deklaruje zmienną |
| `wypierdol` | wypisuje tekst lub liczbę |
| `pierdol` | wypisuje dowolną wartość |
| `zajeb` | zwiększa zmienną liczbową |
| `jeśli` | wykonuje blok dla prawdziwego warunku |
| `inaczej` | wykonuje alternatywny blok |
| `dopóki` | powtarza blok, dopóki warunek jest prawdziwy |
| `wypierdalaj` | przerywa najbliższą pętlę |
| `odpierdol funkcja` | definiuje funkcję |
| `oddaj` | zwraca wartość z funkcji |
| `wpierdol` | dodaje element do końca listy |
| `wypierdol_z_listy` | usuwa i zwraca ostatni element listy |
| `wypierdol_z_mapy` | usuwa klucz z mapy |
| `zajeb_moduł` | ładuje lokalny moduł `.kurwa` do namespace |
| `matematyka`, `losuj`, `tekst`, `czas`, `system`, `plik`, `katalog`, `sciezka`, `dane`, `siec` | standardowe namespace’y v1.x |
| `ile_kurwa` | zwraca długość stringa, listy lub mapy |
| `siec.wjeb`, `siec.wyślij`, `siec.wrzuć`, `siec.wyjeb`, `siec.zjeb` | HTTP GET/POST/PUT/DELETE/generic request |
| `jest_kurwa` | sprawdza klucz mapy |
| `wielkie_kurwa` / `male_kurwa` | zmienia wielkość liter |
| `zawiera_kurwa` | sprawdza zawieranie tekstu |
| `zamien_kurwa` | zamienia fragmenty tekstu |
| `znajdz_kurwa` | zwraca pozycję fragmentu |
| `tekst_kurwa` / `liczba_kurwa` | konwertuje podstawowe wartości |

## Statyczna analiza v1.12

`sprawdz_kurwa <plik.kurwa|katalog>` analizuje istniejący AST bez uruchamiania programu. Łączy dotychczasowe reguły lintowania i typów z konserwatywnym rozpoznawaniem przepływu, prostych stałych i dostępności zmiennych. Analiza nie ładuje importów ani rozszerzeń; pełne granice opisuje [static_analysis.md](static_analysis.md).

## Keywords i instrukcje

### `program`

**Składnia:** `program { instrukcje }`

Jest jedynym wymaganym korzeniem pliku i wykonuje instrukcje w kolejności.

### `kurwa`

**Składnia:** `kurwa nazwa = wyrażenie`

Tworzy zmienną w bieżącym środowisku. Wartością może być number, string, boolean, list, map, function albo no-value.

```text
kurwa kasa = 500
kurwa tekst = "Jaro"
```

### `wypierdol`, `pierdol`, `co_jest_kurwa`

`wypierdol wyrażenie` wypisuje tekst lub liczbę. `pierdol wyrażenie` wypisuje dowolną wartość runtime, a `co_jest_kurwa wyrażenie` zachowuje kompatybilną składnię wypisywania.

```text
wypierdol "Stan konta:"
pierdol 700
```

### `zajeb`

**Składnia:** `zajeb nazwa liczba`

Dodaje drugą wartość do istniejącej zmiennej number. Błąd powstaje, gdy zmienna lub kwota nie jest liczbą.

### `wpierdol`, `wypierdol_z_listy` i `wypierdol_z_mapy`

`wpierdol lista wartość` dodaje wartość na końcu listy. `wypierdol_z_listy lista` zwraca i usuwa ostatni element listy. `wypierdol_z_mapy mapa "klucz"` usuwa wskazany stringowy klucz i nie zwraca wartości. Operacje na złym typie, pustej liście, nieistniejącym kluczu lub złym kluczu są błędami.

### `jeśli` i `inaczej`

**Składnia:** `jeśli warunek { ... } inaczej { ... }`

Warunek musi zwracać boolean. `inaczej` jest opcjonalne.

### `dopóki` i `wypierdalaj`

**Składnia:** `dopóki warunek { ... }`

Wykonuje blok, sprawdzając warunek przed każdą iteracją. `wypierdalaj` przerywa najbliższą pętlę; poza pętlą jest błędem.

### `spierdalaj`

Natychmiast kończy całe wykonywanie programu, także z wnętrza bloków.

### `wjebaj`, `zlap_kurwa`, `wyczysc_kurwa`, `wyrzuc_kurwa`

**Składnia:**

```text
wjebaj {
    ... blok z kodem, który może rzucić błąd ...
} zlap_kurwa nazwa_błędu {
    ... blok przechwytywania ...
} wyczysc_kurwa {
    ... blok cleanup ...
}
```

`wyrzuc_kurwa "tekst"` generuje błąd użytkownika. Błąd przechwycony w `zlap_kurwa` jest mapą z polami `typ_kurwa`, `wiadomosc_kurwa` i `zrodlo_kurwa`. `wyczysc_kurwa` wykonuje się zawsze, niezależnie od tego, czy błąd wystąpił, czy nie.

Jeżeli błąd nie zostanie przechwycony, zostaje ponownie propagowany po wykonaniu cleanup.

### `odpierdol funkcja` i `oddaj`

**Składnia:**

```text
odpierdol funkcja dodaj(a, b) {
    oddaj a + b
}
```

Funkcja może mieć zero lub więcej parametrów, przyjmować wyrażenia jako argumenty i wywoływać samą siebie. `oddaj wyrażenie` kończy funkcję natychmiast. Funkcja bez `oddaj` zwraca `brak_wyniku`.

Funkcje mają lokalne środowisko i mogą modyfikować przekazane listy/mapy. Błędy obejmują nieznaną funkcję, złą liczbę argumentów, duplikat definicji, nieprawidłowe parametry i `oddaj` poza funkcją.

## Wartości logiczne

`prawda` i `fałsz` są runtime booleanami, nie stringami. `jeśli` i `dopóki` przyjmują wyłącznie boolean; liczba, string, lista i mapa użyte bez porównania powodują błąd.

Operatory logiczne to `nie`, `i`, `albo`. `i` i `albo` używają short-circuit: prawa strona może nie zostać wykonana.

## v1.9 TEST — natywne testy KURWA

KURWA LANG v1.9 dodaje natywne testy do tego samego tree-walk runtime, bez osobnego frameworku testowego i bez angielskiego publicznego API. Publiczne konstrukcje są wyłącznie w stylu KURWA.

### Składnia

```text
program {
    testuj_kurwa "dodawanie" {
        sprawdz_kurwa 2 + 2 == 4
        sprawdz_kurwa 5 > 3
        sprawdz_kurwa 1 != 2
    }

    testuj_kurwa "brak_bledu" {
        oczekuj_blad_kurwa {
            wyrzuc_kurwa "kurwa"
        }
    }

    testuj_kurwa "pominiete" {
        pomin_kurwa "docelowo nie uruchomione"
    }
}
```

### Semantyka

- `testuj_kurwa "nazwa" { ... }` tworzy test o podanej nazwie,
- `sprawdz_kurwa wyrażenie` ocenia warunek i kończy test niepowodzeniem, gdy wartość nie jest `prawda`,
- `oczekuj_blad_kurwa { ... }` gwarantuje, że blok zakończy się błędem runtime,
- `pomin_kurwa "powód"` oznacza pominięcie testu i zwraca powód pominięcia,
- CLI akceptuje `testuj_kurwa <plik|katalog> [--filter "nazwa"]` i zwraca niezerowy status, gdy którykolwiek test nie przejdzie.

### CLI

```bash
python3 src/main.py testuj_kurwa tests/kurwa
python3 src/main.py testuj_kurwa tests/kurwa/demo.kurwa
python3 src/main.py testuj_kurwa tests/kurwa --filter "dodawanie"
```

### Public naming audit

Publiczne API testów pozostaje wyłącznie po polsku i w stylu KURWA. Wejście typu `test`, `assert`, `assertEqual`, `assertTrue`, `describe`, `it` nie jest częścią publicznej składni KURWA LANG.

## v1.7 EXT — rozszerzalność runtime

KURWA LANG v1.7 dodaje kontrolowany system rozszerzeń runtime bez tworzenia drugiego interpretera, bytecode ani osobnej maszynie wirtualnej. Rozszerzenie jest małą, zaufaną warstwą Pythonową, która jest ładowana w ten sam tree-walk runtime i exposes KURWA-style public functions.

### Publiczne API v1.7

- `zaladuj_rozszerzenie("nazwa")` — ładuje rozszerzenie z katalogu `extensions/` albo `.kurwa_extensions/` w bieżącym projekcie,
- `wywal_rozszerzenie("nazwa")` — usuwa zarejestrowane rozszerzenie,
- `rozszerzenia_kurwa` — lista nazw zarejestrowanych rozszerzeń,
- `metadane` — mapa z metadany rozszerzenia, np. `nazwa_kurwa`, `wersja_kurwa`, `opis_kurwa`.

### Definicja rozszerzenia

Rozszerzenie jest Pythonowym obiektem typu `Extension` z metadany i funkcjami do ekspozycji:

```python
from src.extensions import Extension


def dodaj(a, b):
    return a + b

EXTENSION = Extension(
    name="demo_ext",
    version="1.0.0",
    description="demo extension",
    functions={"dodaj": dodaj},
)
```

Po załadowaniu w KURWA LANG:

```text
program {
    kurwa ext = zaladuj_rozszerzenie("demo_ext")
    pierdol ext.dodaj(2, 3)
    pierdol ext.metadane["wersja_kurwa"]
}
```

### Semantyka

- nazwa pliku musi odpowiadać nazwie rozszerzenia, np. `demo_ext.py`,
- nazwa rozszerzenia nie może kolidować z istniejącymi built-inami runtime,
- nie można zarejestrować krotnego tego samego rozszerzenia,
- każda wartość zwracana z funkcji rozszerzenia musi być konwertowana do bezpiecznego typu KURWA,
- funkcje rozszerzeń nie mogą wprowadzać niebezpiecznych Pythonowych obiektów do runtime,
- wyjątki z rozszerzenia są zamieniane na kontrolowane błędy KURWA LANG.

### Bezpieczna granica typów

Rozszerzenia mogą bezpiecznie zwracać:

- liczby
- stringi
- boolean
- listy
- mapy (`RuntimeMap`)
- brak_wyniku / `NO_VALUE`

Niebezpieczne obiekty Pythonowe są odrzucane jako kontrolowany błąd runtime.

### Bezpieczeństwo i lokalizacja

v1.7 EXT nie tworzy nowego systemu importów. Rozszerzenia są ładowane z sytemu katalogów projektu:

- `extensions/`
- `.kurwa_extensions/`
- `packages/*/src/`
- `.kurwa_packages/*/*/src/`

To jest trwałe, deterministyczne i przewidywalne. Nie ma auto-scan dla dowolnej części systemu plików.

### Integracja z PACK i modułami

Rozszerzenia nie zastępują modułów ani PACK. Są warstwą runtime przydatną dla lokalnie zainstalowanych rozszerzeń, pakietów i modułów. Pakiet może dostarczać rozszerzenia, ale nadal istnieje jeden model importów, jeden runtime i jeden system błędów KURWA LANG.

## PACK / package manager

v1.4 wprowadza lokalny system paczek bez tworzenia niezależnego rozwiązania od modułów. Projekt może mieć manifest `kurwa.pack` oraz lockfile `kurwa.lock`, a katalog `.kurwa_packages/` jest wpisywany do tego samego systemu importów co lokalne pliki `.kurwa`. To zachowanie pozostaje niezmienione po dodaniu v1.5 ERROR.

```yaml
nazwa: mathz
wersja: 1.2.0
wymagana_wersja_kurwa: 1.4.0
zależności:
  helper: >=1.0.0
```

Po instalacji paczka jest dostępna jak zwykły moduł:

```text
program {
    zajeb_moduł "mathz"
    pierdol mathz.wynik
}
```

### `init`

```bash
python3 src/main.py init demo_app
```

Tworzy projekt z `kurwa.pack`, `kurwa.lock` i katalogiem `src/`.

### `install`

```bash
python3 src/main.py install packages/mathz
```

Instaluje paczkę do `.kurwa_packages/` i zapisuje jej wersję do lockfile.

### `list`, `update`, `uninstall`

```bash
python3 src/main.py list
python3 src/main.py update
python3 src/main.py uninstall mathz
```

Obsługują listowanie, odświeżanie i usuwanie paczek.

## Modules and Imports

### `zajeb_moduł`

**Składnia:** `zajeb_moduł "nazwa"`

Ładuje lokalny moduł KURWA LANG. Rozszerzenie `.kurwa` jest dodawane automatycznie, więc `zajeb_moduł "matematyka"` szuka `matematyka.kurwa`. Można również podać `"matematyka.kurwa"`. Inne rozszerzenia są odrzucane.

Moduł musi znajdować się w katalogu programu albo w ścieżce względnej względem pliku, który go importuje. Import z modułu `lib/auto.kurwa` dla `zajeb_moduł "silnik"` szuka `lib/silnik.kurwa`. Moduł może zawierać pełny `program { ... }` albo instrukcje top-level bez nagłówka `program`.

```text
zajeb_moduł "matematyka"
kurwa wynik = matematyka.dodaj(10, 20)
pierdol wynik
```

### Namespace i scope

Każdy moduł ma własny `Environment`. Jego top-level zmienne i funkcje są dostępne przez namespace o nazwie pliku, np. `matematyka.dodaj` i `matematyka.tajna`. Nie są kopiowane do scope programu głównego. Moduł ma dostęp do built-inów, a funkcje zachowują zamknięcie nad scope modułu.

Moduł jest runtime type `module` i przechowuje nazwę, ścieżkę oraz własny scope. Dostęp przez kropkę do nieistniejącej wartości jest błędem.

### Cache i cykle

Loader cache'uje moduły po kanonicznej ścieżce, więc wielokrotny import w jednym uruchomieniu wykonuje plik tylko raz. Aktywny stos importów wykrywa cykle i zgłasza np. `a -> b -> a`.

Brak modułu, niedozwolone rozszerzenie, błąd parsera lub błąd runtime modułu są kontrolowanymi błędami KURWA LANG. Błędy modułu zawierają jego ścieżkę, np. `auto.kurwa: ...`.

## Built-in functions

### `ile_kurwa(wartość)`

Zwraca number: długość stringa w znakach, liczbę elementów listy albo liczbę kluczy mapy. Inne typy powodują błąd.

### `jest_kurwa(mapa, klucz)`

Zwraca boolean informujący, czy mapa zawiera stringowy klucz. Pierwszy argument musi być mapą, drugi stringiem.

### `wielkie_kurwa(tekst)` i `male_kurwa(tekst)`

Zwracają nowy string odpowiednio wielkimi lub małymi literami. Przyjmują dokładnie jeden string.

### `zawiera_kurwa(tekst, szukany)`

Zwraca boolean. Pusty szukany fragment jest dozwolony i jest znajdowany w każdym stringu.

### `zamien_kurwa(tekst, stary, nowy)`

Zwraca nowy string, zamieniając wszystkie wystąpienia `stary` na `nowy`. Brak wystąpień pozostawia tekst bez zmian. Pusty `stary` jest błędem.

### `znajdz_kurwa(tekst, szukany)`

Zwraca number z pozycją pierwszego wystąpienia, a `-1`, gdy fragmentu nie znaleziono. Przyjmuje dwa stringi.

### `tekst_kurwa(wartość)`

Zwraca string dla liczby, stringa, booleana, listy, mapy albo `brak_wyniku`. Inne wartości są błędem.

### `liczba_kurwa(wartość)`

Zwraca number dla liczby albo stringa zawierającego poprawną liczbę całkowitą. Błędny tekst i inne typy powodują błąd KURWA LANG.

## Standard Library

Standard library jest ładowana przez istniejący `ModuleLoader` i używa tej samej składni co moduły użytkownika:

```text
zajeb_moduł "matematyka"
pierdol matematyka.pierwiastek_kurwa(9)
```

Dostępne namespace’y to `matematyka`, `losuj`, `tekst`, `czas`, `system`, `plik`, `katalog`, `sciezka`, `dane` i `siec`. Lokalny plik `.kurwa` o tej samej nazwie ma pierwszeństwo przed standardowym modułem; pozostałe nazwy są cache’owane podczas jednego uruchomienia. Pełne kontrakty argumentów, typów, zwracanych wartości i błędów opisuje [docs/stdlib.md](stdlib.md).

## HTTP przez `siec`

```text
zajeb_moduł "siec"

kurwa query = {"q": "żółć", "limit": 2}
kurwa naglowki = {"X-Client": "kurwa-demo", "Accept": "application/json"}
kurwa odp = siec.wjeb("https://example.com/api", query, naglowki, 5)

pierdol odp["status_kurwa"]
pierdol odp["tekst_kurwa"]
pierdol odp["json_kurwa"]["status"]
```

### `siec.wjeb(url, params?, headers?, timeout?)`

- **Argumenty:** `url: string`, opcjonalnie `params: map`, `headers: map`, `timeout: number`
- **Zwraca:** mapę odpowiedzi HTTP
- **Działa:** `GET`
- **Parametry:** `params` jest serializowany do query stringa; `headers` to mapa nagłówków
- **Błędy:** niepoprawny URL, timeout, DNS, połączenie odrzucone, TLS, zły typ `params`, zły typ `headers`

### `siec.wyślij(url, body?, headers?, timeout?)`

- **Argumenty:** `url: string`, `body: string|map|list|number|boolean|brak_wyniku`, opcjonalnie `headers: map`, `timeout: number`
- **Zwraca:** mapę odpowiedzi HTTP
- **Działa:** `POST`
- **Body:** `string` jest wysyłany jako text/plain; pozostałe typy są serializowane do JSON

### `siec.wrzuć(url, body?, headers?, timeout?)`

- **Argumenty:** takie same jak w `siec.wyślij`
- **Zwraca:** mapę odpowiedzi HTTP
- **Działa:** `PUT`

### `siec.wyjeb(url, body?, headers?, timeout?)`

- **Argumenty:** takie same jak w `siec.wyślij`
- **Zwraca:** mapę odpowiedzi HTTP
- **Działa:** `DELETE`

### `siec.zjeb(method, url, body?, headers?, timeout?)`

- **Argumenty:** `method: string`, `url: string`, opcjonalnie `body`, `headers`, `timeout`
- **Zwraca:** mapę odpowiedzi HTTP
- **Działa:** dowolna metoda, w tym `PATCH`, `OPTIONS` i inne standardowe metody HTTP

### Response HTTP

Mapa odpowiedzi ma następujące pola:

- `status_kurwa`: kod HTTP jako `number`
- `tekst_kurwa`: treść odpowiedzi jako `string` UTF-8
- `naglowki_kurwa`: mapę nagłówków odpowiedzi
- `adres_kurwa`: finalny URL, po ewentualnym dodaniu parametrów query
- `udalo_sie_kurwa`: `boolean` wskazujący success status (`< 400`)
- `json_kurwa`: zdekodowany JSON, gdy odpowiedź ma `Content-Type` zawierający `json`; inaczej `brak_wyniku`

## JSON przez `dane`

```text
zajeb_moduł "dane"
kurwa dane_we = {"imie": "Jaro", "aktywny": prawda, "wyniki": [10, 3.14]}
kurwa tekst = dane.skurw(dane_we)
kurwa dane_wy = dane.odkurw(tekst)
pierdol dane_wy["imie"]
```

### `dane.skurw(wartość)`

- **Argumenty:** jedna wartość KURWA LANG: `map`, `list`, `string`, `number`, `boolean` albo `brak_wyniku`.
- **Zwraca:** kompaktowy tekst JSON w UTF-8.
- **Błędy:** funkcja, moduł, inny obiekt runtime, cykliczna struktura, `NaN`, nieskończoność lub liczba spoza JSON.

### `dane.odkurw(tekst)`

- **Argumenty:** jeden `string` zawierający JSON.
- **Zwraca:** mapę dla obiektu, listę dla tablicy, odpowiednią wartość dla stringa/liczby/booleana oraz `brak_wyniku` dla `null`.
- **Błędy:** zły typ argumentu albo niepoprawny JSON; komunikat zawiera linię i kolumnę, gdy zna je parser.

### `dane.ładnie_skurw(wartość)`

- **Argumenty:** takie same jak `dane.skurw`.
- **Zwraca:** JSON z nowymi liniami i wcięciem dwóch spacji.
- **Błędy:** takie same jak `dane.skurw`.

### `dane.zapisz(ścieżka, wartość)` i `dane.czytaj(ścieżka)`

- **Argumenty:** `dane.zapisz` przyjmuje ścieżkę `string` i wartość JSON; `dane.czytaj` przyjmuje ścieżkę `string`.
- **Zwraca:** `prawda` po zapisie albo zdeserializowaną wartość po odczycie.
- **Błędy:** brak pliku, katalog zamiast pliku, błąd dostępu, zły typ argumentu, niepoprawny JSON i błędy serializacji.

## Operatory

| Operator | Działanie | Typy |
|---|---|---|
| `+` | dodawanie lub łączenie | number+number, string+string |
| `-` | odejmowanie | number |
| `*` | mnożenie | number |
| `/` | dzielenie całkowite | number, dzielnik różny od zera |
| `<`, `>`, `<=`, `>=` | porównanie porządkowe | number |
| `==`, `!=` | porównanie równości | wartości tego samego typu |
| `nie` | negacja | boolean |
| `i` | AND short-circuit | boolean |
| `albo` | OR short-circuit | boolean |

Priorytet od najwyższego: nawiasy, postfixowe wywołania/indeksy, `nie`, `*`/`/`, `+`/`-`, porównania, `i`, `albo`.

Mieszanie number i string przez `+` jest błędem; nie ma niejawnej konwersji.

## Typy danych

- **number** - liczba całkowita albo zmiennoprzecinkowa, np. `19` albo `3.14`.
- **string** - tekst w cudzysłowie, np. `"Audi"`.
- **boolean** - `prawda` albo `fałsz`.
- **list** - uporządkowana kolekcja, np. `[1, "A", prawda]`.
- **map** - kolekcja stringowych kluczy i wartości, np. `{"wiek": 19}`.
- **function** - funkcja użytkownika albo built-in.
- **no-value** - `brak_wyniku` z funkcji bez `oddaj`.

## Collections

### Listy

```text
kurwa lista = [10, 20]
pierdol lista[0]
lista[1] = 99
wpierdol lista 30
kurwa ostatnia = wypierdol_z_listy lista
```

Indeksy list zaczynają się od zera i są nieujemnymi liczbami. `wypierdol_z_listy` usuwa ostatni element i go zwraca.

### Mapy

```text
kurwa osoba = {"imie": "Jaro", "wiek": 19}
pierdol osoba["imie"]
osoba["wiek"] = 20
wypierdol_z_mapy osoba "wiek"
```

Klucze literalów map muszą być stringami. Przypisanie nowego klucza dodaje go automatycznie. Listy, mapy i stringi mogą być zagnieżdżane przez indeksowanie, np. `dane["auta"][0]`.

### String indexing i slicing

`tekst[0]` zwraca jeden znak. Indeksy są nieujemne. `tekst[start:stop]` zwraca fragment z zakresem półotwartym, czyli bez znaku `stop`.

```text
kurwa tekst = "KURWALANG"
pierdol tekst[0]
pierdol tekst[5:9]
```

Wyjście poza zakres, indeks niebędący numberem, slicing wartości innej niż string albo odwrócony zakres powodują błąd.

## Błędy

Parser zgłasza błędy składni z linią i kolumną. Runtime zgłasza `InterpreterError`, a CLI pokazuje komunikat zamiast surowego tracebacka. Typowe błędy obejmują niezdefiniowane zmienne/funkcje, złą liczbę argumentów, niedozwolone typy operatorów, dzielenie przez zero, indeks poza zakresem, brak klucza mapy, błędne konwersje i nieprawidłowe argumenty built-inów.
