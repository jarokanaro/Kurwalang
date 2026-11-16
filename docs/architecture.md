# Architektura

Przepływ programu w v1.12 ANALYZE nadal używa jednego lexer/parsera i istniejącego AST:

```text
KURWA source
    ↓
Lexer
    ↓
Parser
    ↓
AST
        └─> Static checks
            ├─> LINT (K... diagnostics)
            ├─> TYPE (T... diagnostics)
            └─> Flow pass (A... diagnostics, internal AST walk)
    ↓
Interpreter
    ↓
Runtime
    ↓
Structured Runtime Error
    ↓
wjebaj / zlap_kurwa / wyczysc_kurwa
    ↓
handled or propagated
```

- `src/lexer.py` rozpoznaje słowa kluczowe, operatory i delimitery.
- `src/parser.py` buduje AST dla istniejącego języka i parsuje nowe wyrażenia `wjebaj` oraz `wyrzuc_kurwa`.
- `src/ast.py` zawiera węzły instrukcji i wyrażeń w tym `TryStatement` i `ThrowStatement`.
- `src/interpreter.py` wykonuje AST przez środowiska `Environment(parent)` i dodaje kontrolowanie błędów runtime.
- `src/main.py` pozostaje punktem wejścia CLI do skryptów i pack commands bez osobnej warstwy błędów.
- `src/package_manager.py` nadal jest zintegrowany z `ModuleLoader` i ten sam model importów jest używany dla modułów i pakietów.
- `src/linter.py` scala reguły jakości, typów i wewnętrzne fakty przepływu w tym samym formacie diagnostycznym; analiza nie przekazuje AST do interpretera.
- Statyczny resolver używa czystej funkcji ścieżek `ModuleLoader._resolve`, parsuje lokalne źródła do AST i nigdy nie tworzy `Interpreter` ani `Environment` runtime.
- `sprawdz_kurwa` analizuje wskazane pliki osobno oraz statycznie odwiedza rozwiązywalne importy `.kurwa`; nie uruchamia modułów, nie instaluje PACK i nie ładuje rozszerzeń.

## v1.6 ASYNC runtime

v1.6 nie tworzy osobnej maszyny wirtualnej ani nowego interpretera. Dodaje warstwę asynchroniczną do tego samego tree-walk runtime. Internally Python współdzieli wątek wykonania z prostym event-loop style scheduler poprzez `threading` i `Event`; publiczne słowa KURWA LANG są wyłącznie polskie/slangowe i nie eksponują `async`/`await`/`task`.

Najważniejsze elementy:

- `odpierdol_kurwicznie funkcja` definiuje funkcję, która zwraca `AsyncTask` zamiast natychmiastowego wyniku,
- `czekaj_kurwa(...)` blokuje bieżące wykonanie tasku do momentu uzyskania wartości, ale nie zatrzymuje innych tasków,
- `wyjeb_task(...)` uruchamia zadanie współbieżnie,
- `czekaj_wiele_kurwa(...)` czeka na wiele zadań i zwraca listę wyników,
- `kurwa_pauza(...)` zatrzymuje tylko aktywne zadanie na wskazany czas,
- błędy z tasków są zamieniane na tę samą strukturę z `typ_kurwa`, `wiadomosc_kurwa` i `zrodlo_kurwa`.

W praktyce to jest rozszerzenie obecnego interpretera, a nie zastąpienie go.

## Przepływ błędów runtime

Błąd w KURWA LANG jest najpierw zgłaszany przez interpreter jako `InterpreterError` lub jako użytkownika przez `wyrzuc_kurwa`. `wjebaj` przechwytuje wyjątek i zamienia go do strukturalnej mapy z kluczami:

- `typ_kurwa`
- `wiadomosc_kurwa`
- `zrodlo_kurwa`

Dla błędów użytkownika `typ_kurwa` ma wartość `user_error`. Dla błędów runtime ma wartość `runtime_error` albo `arithmetic_error`, jeśli błąd wynika z dzielenia przez zero lub podobnego przypadku.

`zlap_kurwa` ma dostęp do tej mapy jako zmienna w bloku przechwytywania, np. `blad["typ_kurwa"]`.

## Cleanup semantics

`wyczysc_kurwa` wykonuje się po zakończeniu sukcesu albo po przechwyceniu błędu. Jeżeli błąd nie zostanie przechwycony przez `zlap_kurwa`, bloki cleanup nadal są wykonywane przed ponownym propagowaniem błędu.

W praktyce implementacja zachowuje następujące reguły:

- `spierdalaj` nie przechwyca błędu i nie wykonuje cleanup,
- `wypierdalaj` nie przechwyca błędu i nie wykonuje cleanup,
- `oddaj` w funkcji nie przechwyca błędu i nie wykonuje cleanup w `wjebaj` otaczającym funkcję, jeśli zwrot nastąpił w obrębie try,
- błąd wywołany w funkcji rozprzestrzenia się do zewnętrznego `wjebaj` i może zostać przechwycony tam.

## Moduły, pakiety, pliki, JSON i HTTP

Błędy z tych obszarów są nadal wprowadzane przez ten sam mechanizm runtime. Moduł `plik`, `dane` i `siec` nie tworzą osobnej architektury błędów. Zamiast tego wywołują kontrolowane wyjątki interpretera, które można przechwycić w `wjebaj` i odczytać w strukturze błędu.

Nie ma osobnego VM, bytecode, ani drugiego interpretera. To jest ten sam tree-walk interpreter, tylko z dodatkowymi kilkoma syntaktycznymi i runtime’owymi konstrukcjami.
