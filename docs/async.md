# Asynchroniczność v1.6

KURWA LANG v1.6 dodaje minimalny, ale realny model zadań asynchronicznych bez tworzenia osobnego języka, osobnej maszyny wirtualnej albo eksportu nazw Pythonowych do publicznego API.

## Zasada projektowa

- nie ma publicznego `async` / `await` / `task` / `future` / `asyncio` w języku,
- API pozostaje w stylu KURWA LANG i jest wyłącznie po polsku / slangowo,
- runtime nadal jest tym samym tree-walk interpreterem, tylko z warstwą zadań i oczekiwania,
- błędy runtime są nadal propagowane przez ten sam model `typ_kurwa` / `wiadomosc_kurwa` / `zrodlo_kurwa`.

## Słowa kluczowe

```text
odpierdol_kurwicznie funkcja nazwa(...) {
    ...
}

kurwa wynik = czekaj_kurwa(task)
kurwa task = wyjeb_task(funkcja, arg1, arg2)
kurwa wyniki = czekaj_wiele_kurwa(task1, task2, task3)
kurwa_pauza(0.25)
```

## Semantyka

### `odpierdol_kurwicznie`

Definiuje funkcję, która wykonuje się w osobnym zadaniu. Funkcja może zwracać zwykłą wartość, a runtime zamieni ją w wynik zadania.

```text
program {
    odpierdol_kurwicznie funkcja slow() {
        kurwa_pauza(0.05)
        oddaj "ok"
    }
}
```

### `czekaj_kurwa`

Blokuje bieżące wykonanie aż do uzyskania rezultatu zadania i zwraca wartość z tego zadania.

```text
program {
    kurwa wynik = czekaj_kurwa(slow())
    pierdol wynik
}
```

### `wyjeb_task`

Uruchamia zadanie współbieżnie i zwraca uchwyt taska, który można potem od razu przekazać do `czekaj_kurwa` albo `czekaj_wiele_kurwa`.

```text
program {
    kurwa a = wyjeb_task(robota, "a", 0.05)
    kurwa b = wyjeb_task(robota, "b", 0.01)
    pierdol czekaj_wiele_kurwa(a, b)
}
```

### `czekaj_wiele_kurwa`

Czeka na wiele zadań i zwraca listę wyników w tej samej kolejności, w jakiej zostały przekazane.

### `kurwa_pauza`

Zatrzymuje wykonanie obecnego zadania na określoną liczbę sekund.

```text
program {
    kurwa_pauza(0.2)
    wypierdol "po pauzie"
}
```

## Błędy w zadaniach

Błędy wyrzucone w zadaniu są nadal stabilnie propagowane przez interpreter i zamieniane na ten sam standardowy format błędu runtime:

- `typ_kurwa`
- `wiadomosc_kurwa`
- `zrodlo_kurwa`

To oznacza, że v1.6 nie wprowadza nowego systemu błędów — tylko rozszerza wykonanie współbieżne na istniejący model runtime.

## Przykład pełny

```text
program {
    odpierdol_kurwicznie funkcja robota(name, delay) {
        kurwa_pauza(delay)
        oddaj "zrobione: " + name
    }

    kurwa a = wyjeb_task(robota, "a", 0.05)
    kurwa b = wyjeb_task(robota, "b", 0.01)

    pierdol czekaj_wiele_kurwa(a, b)
}
```

W praktyce jest to realne zadanie równoległe z oczekiwaniem na wynik, ale zachowane są zasady KURWA LANG: publiczne API i nazewnictwo pozostają w języku projektu, a nie w style Pythonowym.
