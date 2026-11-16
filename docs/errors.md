# Błędy i handling runtime v1.5

KURWA LANG nie dodaje osobnej, niezależnej warstwy błędów. Wszelkie runtime błędy są nadal zgłaszane przez ten sam interpreter, a v1.5 ERROR dodaje tylko kontrolowany mechanizm `wjebaj` / `zlap_kurwa` / `wyczysc_kurwa`.

## Składnia

```text
program {
    wjebaj {
        wyrzuc_kurwa "dupa"
    } zlap_kurwa blad {
        pierdol blad["typ_kurwa"]
        pierdol blad["wiadomosc_kurwa"]
    } wyczysc_kurwa {
        wypierdol "cleanup"
    }
}
```

W praktyce:

- `wyrzuc_kurwa "tekst"` tworzy błąd użytkownika,
- `wjebaj { ... }` tworzy blok zabezpieczający,
- `zlap_kurwa nazwa` definiuje zmienną przechwyconego błędu,
- `wyczysc_kurwa { ... }` wykonuje się zawsze po odbiciu błędu lub sukcesie,
- jeśli wyjątek nie zostanie przechwycony, jest ponownie propagowany po cleanup.

## Struktura błędu

Błąd przechwycony w `zlap_kurwa` jest mapą runtime z następującymi polami:

- `typ_kurwa`
- `wiadomosc_kurwa`
- `zrodlo_kurwa`

Przykładowy wynik:

```text
user_error
dupa
cleanup
```

Dla błędu arytmetycznego `typ_kurwa` może być `arithmetic_error`, a `zrodlo_kurwa` jest ustawione na `runtime`.

## Błędy nieprzechwycone

Jeżeli program kończy się błędem bez `zlap_kurwa`, interpreter podnosi `InterpreterError` i CLI zwraca status 1 z napisem `Error:`. To jest nadal ten sam model błędów języka, tylko z przechwytywaniem w block `wjebaj`.

## Przykłady realnych środowisk

- błędy użytkownika: `wyrzuc_kurwa "..."`
- runtime arytmetyka: `1 / 0`
- brak pliku: `plik.czytaj("nie_ma.txt")`
- zły JSON: `dane.odkurw("{bad")`
- http/network: `siec.wjeb("http://127.0.0.1:65535")`

Surowe wyjątki Pythona nie są częścią publicznego interfejsu KURWA LANG i nie są wystawiane użytkownikowi jako API języka.
