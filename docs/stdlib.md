# KURWA LANG Standard Library v1.5 ERROR

Standard library jest publicznym API języka. Moduły są ładowane przez istniejący `ModuleLoader`, a lokalne paczki PACK instalowane w `.kurwa_packages/` korzystają z tego samego mechanizmu importu. Nie trzeba instalować zewnętrznych paczek.

## Obsługa błędów runtime w standard library

v1.5 ERROR nie tworzy osobnego systemu błędów dla standard library. Moduły takie jak `plik`, `dane`, `siec` i importy modułów nadal zgłaszają kontrolowane błędy `InterpreterError`, które mogą zostać przechwycone przez `wjebaj` i odczytane z mapy błędu.

Przykład:

```text
program {
    wjebaj {
        kurwa txt = plik.czytaj("nie-ma.txt")
    } zlap_kurwa blad {
        pierdol blad["typ_kurwa"]
        pierdol blad["wiadomosc_kurwa"]
    }
}
```

Dla oferty technicznej standard library zachowuje się tak samo jak w v1.4: `File I/O`, `JSON`, `HTTP`, `moduły` i `pakiety` są integralną częścią tego samego interfejsu runtime.

## PACK / local packages

Manifest paczki:

```yaml
nazwa: mathz
wersja: 1.2.0
wymagana_wersja_kurwa: 1.4.0
zależności:
  helper: >=1.0.0
```

Pakiety są instalowane do `.kurwa_packages/<nazwa>/<wersja>/src/` i importowane przez istniejący system `zajeb_moduł`.

```text
program {
    zajeb_moduł "mathz"
    pierdol mathz.wynik
}
```

Wersja finalna `kurwa.pack` i `kurwa.lock` musi być zgodna z projektem i zapewniać poprawne rozwiązywanie zależności, konfliktów oraz cykli.

Import:

```text
zajeb_moduł "matematyka"
```

Nazwy standardowe są rozwiązywane przed modułami użytkownika. Lokalny plik `matematyka.kurwa` nie przesłoni standardowego modułu `matematyka`. Import tego samego modułu wiele razy korzysta z cache.

## `siec`

```text
zajeb_moduł "siec"
```

Moduł HTTP obsługuje wywołania sieciowe z użyciem protokołów `http://` i `https://`.

### `siec.wjeb(url, params?, headers?, timeout?)`

- Argumenty: `url: string`, opcjonalnie `params: map`, `headers: map`, `timeout: number`
- Zwraca: `map` response
- Działa: `GET`
- Query parameters są serializowane z mapy do form `?a=1&b=2`
- Błędy: zły URL, timeout, DNS, brak połączenia, TLS, złe parametry i nagłówki

### `siec.wyślij(url, body?, headers?, timeout?)`

- Argumenty: `url: string`, opcjonalnie `body: string|map|list|number|boolean|brak_wyniku`, `headers: map`, `timeout: number`
- Zwraca: `map` response
- Działa: `POST`
- `string` jest wysyłany jako text/plain; inne typy są serializowane przez `dane.skurw`

### `siec.wrzuć(url, body?, headers?, timeout?)`

- Argumenty: `url: string`, opcjonalnie `body`, `headers`, `timeout`
- Zwraca: `map` response
- Działa: `PUT`

### `siec.wyjeb(url, body?, headers?, timeout?)`

- Argumenty: `url: string`, opcjonalnie `body`, `headers`, `timeout`
- Zwraca: `map` response
- Działa: `DELETE`

### `siec.zjeb(method, url, body?, headers?, timeout?)`

- Argumenty: `method: string`, `url: string`, opcjonalnie `body`, `headers`, `timeout`
- Zwraca: `map` response
- Działa: dowolna metoda HTTP (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`, itd.)

### Response `siec.*`

Każda funkcja zwraca mapę z polami:

- `status_kurwa`: `number` z kodem HTTP
- `tekst_kurwa`: `string` z ciałem odpowiedzi UTF-8
- `naglowki_kurwa`: `map` z nagłówkami odpowiedzi
- `adres_kurwa`: `string` z finalnym URL
- `udalo_sie_kurwa`: `boolean`
- `json_kurwa`: `map`/`list`/`value` jeśli Content-Type wskazuje JSON; inaczej `brak_wyniku`

### Przykład

```text
zajeb_moduł "siec"

kurwa query = {"q": "żółć", "limit": 2}
kurwa naglowki = {"Accept": "application/json"}
kurwa odp = siec.wjeb("https://example.com/api", query, naglowki, 5)

pierdol odp["status_kurwa"]
pierdol odp["tekst_kurwa"]
```

## `matematyka`

```text
zajeb_moduł "matematyka"
```

### `matematyka.abs_kurwa(x)`

- Argumenty: jeden `number`.
- Zwraca: `number` bez znaku.
- Błąd: argument innego typu.

### `matematyka.potega_kurwa(x, y)`

- Argumenty: dwa `number`.
- Zwraca: `number` będący `x` podniesionym do `y`.
- Błąd: argument innego typu.

### `matematyka.pierwiastek_kurwa(x)`

- Argumenty: jeden nieujemny `number`.
- Zwraca: `number`, dla pierwiastka może być `float`.
- Błąd: zły typ albo liczba ujemna.

### `matematyka.minimum_kurwa(...)` i `matematyka.maksimum_kurwa(...)`

- Argumenty: co najmniej jeden `number`.
- Zwraca: najmniejszy/największy `number`.
- Błąd: brak argumentów albo zły typ.

### `matematyka.zaokraglij_kurwa(x)`

- Argumenty: jeden `number`.
- Zwraca: zaokrąglony `number`, zgodnie z regułą `round` backendu.

### `matematyka.PI` i `matematyka.E`

Stałe typu `number` o wartościach `math.pi` i `math.e`.

## `losuj`

```text
zajeb_moduł "losuj"
```

### `losuj.liczba(min, max)`

- Argumenty: dwie liczby całkowite.
- Zwraca: losową liczbę całkowitą z zakresu domkniętego `[min, max]`.
- Błąd: zły typ albo `min > max`.

### `losuj.ulamek(min, max)`

- Argumenty: dwa `number`.
- Zwraca: losowy `number` zmiennoprzecinkowy w zakresie backendu.
- Błąd: zły typ albo `min > max`.

### `losuj.element(lista)`

- Argumenty: niepusta `list`.
- Zwraca: jeden element listy.
- Błąd: zły typ albo pusta lista.

## `tekst`

```text
zajeb_moduł "tekst"
```

### `tekst.oczysc(tekst)`

Usuwa białe znaki z początku i końca stringa. Zwraca `string`.

### `tekst.zaczyna_sie(tekst, prefiks)` i `tekst.konczy_sie(tekst, sufiks)`

Przyjmują dwa stringi i zwracają `boolean`. Błąd powstaje dla innych typów.

### `tekst.rozdziel(tekst, separator)`

Dzieli string na `list` stringów. Separator musi być niepustym stringiem.

### `tekst.polacz(lista, separator)`

Łączy listę stringów w jeden `string`. Separator musi być stringiem.

### `tekst.powtorz(tekst, ile)`

Zwraca string powtórzony `ile` razy. `ile` musi być nieujemną liczbą całkowitą.

## `czas`

```text
zajeb_moduł "czas"
```

### `czas.teraz()`

Zwraca aktualny timestamp jako `number` zmiennoprzecinkowy.

### `czas.data()`

Zwraca aktualną datę i czas jako string w formacie ISO-like `YYYY-MM-DD HH:MM:SS`.

### `czas.uspij(milisekundy)`

Wstrzymuje program na podaną liczbę milisekund i zwraca `brak_wyniku`. Argument musi być nieujemną liczbą całkowitą.

## `system`

```text
zajeb_moduł "system"
```

### `system.argumenty()`

Zwraca listę argumentów przekazanych po ścieżce programu CLI.

### `system.operacyjny()`

Zwraca nazwę systemu operacyjnego jako string.

### `system.katalog()`

Zwraca bieżący katalog roboczy jako string.

### `system.wersja()`

Zwraca oficjalną wersję języka jako string. W v1.3 jest to `1.3.0`, zdefiniowane raz w `src/version.py`.

## `dane`

```text
zajeb_moduł "dane"
```

Moduł JSON używa istniejących typów KURWA LANG: map, list, string, number, boolean i `brak_wyniku` dla JSON `null`.

### `dane.skurw(wartość)`

Serializuje wartość do kompaktowego JSON stringa. Obsługuje mapy, listy, stringi, liczby, booleany i `brak_wyniku`. Wykrywa cykliczne struktury i odrzuca funkcje oraz moduły.

### `dane.odkurw(tekst)`

Parsuje JSON string. Obiekt JSON staje się mapą, tablica listą, `true`/`false` booleanem, liczba numberem, a `null` wartością `brak_wyniku`. Błędny JSON i argument innego typu powodują kontrolowany błąd.

### `dane.ładnie_skurw(wartość)`

Jak `dane.skurw`, ale zwraca JSON z wcięciami i nowymi liniami.

### `dane.zapisz(ścieżka, wartość)`

Serializuje wartość jako czytelny JSON UTF-8 i zapisuje ją przez istniejący system plików. Zwraca `prawda` po sukcesie.

### `dane.czytaj(ścieżka)`

Odczytuje plik UTF-8 przez istniejące File I/O i deserializuje jego zawartość do wartości KURWA LANG.

JSON używa nazw publicznych `skurw` i `odkurw`; backendowe `json.dumps` i `json.loads` nie są częścią składni KURWA LANG.

## `plik`

```text
zajeb_moduł "plik"
```

### `plik.czy_jest(path)`

- Argumenty: jeden `string` 
- Zwraca: `boolean` wskazujący, czy plik istnieje.
- Błąd: zły typ argumentu.

### `plik.czytaj(path)`

- Argumenty: jeden `string`.
- Zwraca: `string` z pełną treścią pliku UTF-8.
- Błąd: brak pliku, katalog zamiast pliku, brak uprawnień.

### `plik.zapisz(path, tekst)`

- Argumenty: `string` i `string`.
- Zwraca: `boolean` `prawda` po pomyślnym zapisie.
- Błąd: zapis do katalogu lub zły typ.

### `plik.dopisz(path, tekst)`

- Argumenty: `string` i `string`.
- Zwraca: `boolean` `prawda` po dopisaniu.
- Błąd: zły typ, katalog zamiast pliku.

### `plik.usun(path)`

- Argumenty: jeden `string`.
- Zwraca: `boolean` `prawda` po usunięciu.
- Błąd: brak pliku, katalog zamiast pliku.

### `plik.info(path)`

- Argumenty: jeden `string`.
- Zwraca: `map` z polami `rozmiar`, `istnieje`, `czy_plik`, `czy_katalog`.
- Błąd: zły typ argumentu.

## `katalog`

```text
zajeb_moduł "katalog"
```

### `katalog.czy_jest(path)`

- Argumenty: jeden `string`.
- Zwraca: `boolean`.

### `katalog.utworz(path)`

- Argumenty: jeden `string`.
- Zwraca: `boolean` `prawda` po utworzeniu katalogu.
- Błąd: zły typ, gdy podano plik zamiast katalogu.

### `katalog.lista(path)`

- Argumenty: jeden `string`.
- Zwraca: `list` nazw elementów katalogu.
- Błąd: brak katalogu lub plik zamiast katalogu.

## `sciezka`

```text
zajeb_moduł "sciezka"
```

### `sciezka.polacz(a, b)`

- Argumenty: dwa `string`.
- Zwraca: `string` z poprawnie połączoną ścieżką.

### `sciezka.nazwa(path)`

- Argumenty: jeden `string`.
- Zwraca: nazwę pliku lub katalogu na końcu ścieżki.

### `sciezka.rozszerzenie(path)`

- Argumenty: jeden `string`.
- Zwraca: rozszerzenie, np. `.txt`.

### `sciezka.katalog(path)`

- Argumenty: jeden `string`.
- Zwraca: katalog nadrzędny ścieżki.

### `sciezka.absolutna(path)`

- Argumenty: jeden `string`.
- Zwraca: absolutną ścieżkę.

## Typy i błędy

Standard library korzysta z typów `number`, `string`, `boolean`, `list`, `map`, `function`, `module` i `no-value`. Każda funkcja sprawdza kontrakt argumentów i zgłasza `InterpreterError` z komunikatem KURWA LANG; nie ujawnia surowych wyjątków Pythonowych jako głównego API.

HTTP dodatkowo kontroluje:

- timeout: `KURWA ERROR: timeout połączenia HTTP po X s`
- URL: `KURWA ERROR: niepoprawny URL: ...`
- DNS / połączenie: `KURWA ERROR: błąd DNS/połączenia sieciowego: ...`
- TLS: `KURWA ERROR: błąd HTTPS/TLS: ...`
- parametry / nagłówki: `KURWA ERROR: parametry URL muszą być mapą` / `KURWA ERROR: nagłówki HTTP muszą być mapą`
