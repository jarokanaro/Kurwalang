# Statyczna analiza v1.12

`sprawdz_kurwa` uruchamia trzy statyczne warstwy na jednym AST: reguły LINT (`K...`), inferencję TYPE (`T...`) i wewnętrzną analizę przepływu (`A...`). Żadna z nich nie uruchamia interpretera.

## Co jest sprawdzane

- Kolejne instrukcje, zwroty, zakończenie programu, `wypierdalaj`, rozgałęzienia i pętle.
- Proste warunki stałe oraz ścieżki nieosiągalne po znanym bezwarunkowym zakończeniu.
- Dostępność zmiennych po rozgałęzieniach i pętlach; wartość nieznana jest odróżniona od zmiennej dostępnej tylko na części ścieżek. Analiza używa tych samych ramek `Scope` co istniejący lint, uwzględnia przypisanie przez `zajeb`, lokalność funkcji/testów oraz zasłanianie nazw.
- Bezpieczne stałe prymitywne: liczby, teksty, booleany, operatory arytmetyczne, porównania i logika.
- Znane deklaracje funkcji, bezpośrednie relacje wywołań, rekurencja, częściowe zwroty oraz proste kategorie efektów.
- Mutacje list/map i jawne granice modułów standardowych, dla których efekt może być zewnętrzny.
- Bezpośrednie relacje warunków: zgodność `==`/`!=`, wzajemne wykluczanie równości oraz proste przedziały liczbowe dla porównań `<`, `<=`, `>` i `>=`. Fakty obowiązują tylko wewnątrz ścieżki i są unieważniane po zmianie wartości.
- Lokalne importy `.kurwa` rozwiązywane tą samą regułą ścieżek co runtime: najpierw względem pliku importującego, potem lokalne źródła PACK. Pliki są parsowane i cache’owane jako AST; ich LINT, TYPE i ANALYZE są uruchamiane statycznie.
- Dostępność top-level nazw modułu, brakujący statycznie widoczny członek i bezpośrednie cykle importów.
- Lokalne `kurwa.pack` oraz `kurwa.lock`: istniejący lock jest porównywany z ograniczeniami zależności manifestu bez instalacji ani rozwiązywania z siecią.
- Bloki błędów, deklaracje testów i funkcje asynchroniczne są odwiedzane jako AST; ich zawartość nie jest wykonywana.

Przykład ścieżki z warunkową deklaracją:

```text
program {
    odpierdol funkcja sprawdz(warunek) {
        jeśli warunek {
            kurwa wynik = 10
        }
        pierdol wynik
    }
}
```

`A010` ostrzega, że `wynik` istnieje tylko wtedy, gdy warunek jest prawdziwy. Jeśli obie gałęzie deklarują tę samą stałą, analiza może zachować tę wartość po scaleniu.

## Kody

- `A001` — instrukcja jest nieosiągalna po bezwarunkowym zakończeniu analizowanej ścieżki.
- `A010` — zmienna może nie być dostępna na każdej ścieżce.
- `A020` — gałąź albo pętla nie wykona się przy znanym warunku.
- `A031` — funkcja zwraca wartość tylko na części ścieżek.
- `A012` — deklaracja lokalna lub parametr zasłania nazwę zewnętrzną.
- `A040` — brakujący symbol lokalnego modułu albo import ze ścieżką o niedozwolonym rozszerzeniu.
- `A041` — wykryty cykl lokalnych importów.
- `A042` — wersja w istniejącym locku nie spełnia zależności manifestu.
- `A043` — konflikt dwóch bezpośrednich deklaracji funkcji w tym samym module.

Diagnostyki zachowują wspólny format `Diagnostic`: poziom, kod, komunikat, plik, pozycję i opcjonalną sugestię. Występują w tym samym wyniku CLI co LINT i TYPE.

`A010`, `A012`, `A020` i `A031` są ostrzeżeniami. Pewny brak symbolu, cykl lokalnych importów, sprzeczny istniejący lock i bezpośredni konflikt deklaracji funkcji (`A040`-`A043`) są błędami.

## Granice i bezpieczeństwo

Analiza jest celowo konserwatywna, nie jest dowodzeniem poprawności programu. Nie ocenia dowolnych wywołań, nie wykonuje funkcji w celu poznania wyniku i nie zakłada efektu jako czystego, jeśli AST tego nie uzasadnia. Mutacje i wywołania o nieznanym działaniu unieważniają stałe, na które mogą wpływać.

Pliki katalogu wskazanego w CLI są sprawdzane niezależnie, a importowane lokalne pliki są dodatkowo odwiedzane przez cache analizy. Nierozwiązywalny import pozostaje nieznany; brak pliku sam w sobie nie jest diagnozowany. Nie rozwiązuje się zależności przez instalację, nie weryfikuje się semver poza porównaniem istniejącego locka z lokalnym manifestem i nie ładuje EXT. Standardowe namespace’y pozostają nieprzezroczyste dla sprawdzania eksportów. Zachowanie zewnętrznych wywołań pozostaje `external` albo `unknown`.

Analiza nie uruchamia KURWA, nie wywołuje funkcji, nie wykonuje testów, nie inicjuje zadań asynchronicznych, nie wysyła HTTP, nie czyta ani nie zapisuje plików przez runtime i nie wywołuje poleceń systemowych. Rozszerzenia są nieprzezroczyste.

Złożone kontradykcje, dowolna algebra, pełne scalanie stanu przy zagnieżdżonych pętlach, dynamiczne ścieżki importu, introspekcja standardowych namespace’ów/EXT oraz dokładne zachowanie wyjątków pozostają nierozstrzygnięte. Konflikt nazw wykrywany jest dla bezpośrednich deklaracji funkcji w jednym bloku, nie dla dowolnych możliwych kolizji warunkowych. W razie niepewności wynik jest nieznany, zamiast zgadywania.