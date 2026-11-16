# KURWA LANG v1.7 EXT — rozszerzalność runtime

KURWA LANG v1.7 nie tworzy drugiego interpretera, nie tworzy bytecode ani osobnej maszyny wirtualnej. Działa dalej w tym samym tree-walk runtime, ale dodaje kontrolowaną warstwę rozszerzeń Python-backed, która pozwala rozszerzać język bez rozbijania jądra interpretera.

## Zasada projektowa

- `plugin`, `extension`, `register`, `hook`, `callback` to nazwy techniczne Pythona, nie publiczne API KURWA LANG,
- publiczne API pozostaje w stylu KURWA LANG: `zaladuj_rozszerzenie`, `wywal_rozszerzenie`, `rozszerzenia_kurwa`, `metadane`,
- moduły, PACK i stdlib nadal są warstwami tego samego runtime, a nie niezależnymi systemami,
- każda funkcja rozszerzenia musi przejść przez bezpieczną granicę typu i błędu runtime.

## Publiczne API

### `zaladuj_rozszerzenie("nazwa")`

Ładuje rozszerzenie o podanej nazwie z katalogów projektu:

- `extensions/`
- `.kurwa_extensions/`
- bieżącego katalogu projektu

Trzeba podać nazwę pliku bez `.py`, np. `demo_ext` dla `demo_ext.py`.

Przykład:

```text
program {
    kurwa ext = zaladuj_rozszerzenie("demo_ext")
    pierdol ext.dodaj(2, 3)
}
```

### `wywal_rozszerzenie("nazwa")`

Usuwa rozszerzenie z rejestru.

```text
program {
    wywal_rozszerzenie("demo_ext")
}
```

### `rozszerzenia_kurwa()`

Zwraca listę nazw zarejestrowanych rozszerzeń.

```text
program {
    pierdol rozszerzenia_kurwa()
}
```

### `metadane`

Każde załadowane rozszerzenie ma mapę `metadane`:

```text
program {
    kurwa ext = zaladuj_rozszerzenie("demo_ext")
    pierdol ext.metadane["wersja_kurwa"]
}
```

## Python side: `Extension`

Rozszerzenie jest zdefiniowane jako obiekt `Extension` w Pythonie:

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

Metadane rozszerzenia są automatycznie przekładane na KURWA mapy i dostępne pod `metadane`.

## Granica typów

Rozszerzenia mogą bezpiecznie zwracać:

- liczby
- stringi
- booleany
- listy
- mapy runtime
- `brak_wyniku` / no-value

Każdy inny Python object jest odrzucany jako błąd runtime. Nie ma pochłaniania niebezpiecznych obiektów z Python runtime do KURWA języka.

## Błędy

Błędy rozszerzenia są przechwytywane i zamieniane na standardowy model KURWA LANG:

- `typ_kurwa`
- `wiadomosc_kurwa`
- `zrodlo_kurwa`

Dodatkowo runtime blokuje:

- zduplikowane nazwy rozszerzeń,
- próby zastąpienia zarezerwowanych built-inów,
- path traversal / niedozwolone ścieżki,
- niepoprawny format `EXTENSION`.

## Integracja z modułami i PACK

v1.7 EXT nie tworzy osobnego systemu importów. Rozszerzenia są ładowane i rejestrowane przez ten sam runtime, a moduły i PACK pozostają aktywnymi warstwami projektu. Pakiet może dostarczać rozszerzenia, jeśli ma odpowiedni moduł Pythonowy w swoim katalogu pakietu, ale cały model importów pozostaje spójny.

## Przykłady

- [examples/extensions/basic.kurwa](../examples/extensions/basic.kurwa)
- [examples/extensions/metadata.kurwa](../examples/extensions/metadata.kurwa)
- [examples/extensions/functions.kurwa](../examples/extensions/functions.kurwa)
