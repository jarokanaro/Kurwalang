import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.lexer import Lexer
from src.linter import Linter, _ProgramFlowAnalysis
from src.parser import Parser


class ProgramFlowAnalysisTestCase(unittest.TestCase):
    def lint(self, source):
        return Linter().lint_source(source, "memory.kurwa")

    def flow(self, source):
        program = Parser(Lexer(source).tokenize()).parse_module()
        analysis = _ProgramFlowAnalysis("memory.kurwa")
        diagnostics = analysis.analyze(program)
        return analysis, diagnostics

    def test_conditional_declaration_is_reported_as_maybe_unavailable(self):
        diagnostics = self.lint(
            "program { odpierdol funkcja sprawdz(warunek) { "
            "jeśli warunek { kurwa wynik = 7 } pierdol wynik } }"
        )
        maybe = [item for item in diagnostics if item.code == "A010"]
        self.assertEqual(len(maybe), 1)
        self.assertIn("każdej ścieżce", maybe[0].message)
        self.assertFalse(any(item.code == "K010" and item.line == maybe[0].line for item in diagnostics))

    def test_variable_is_defined_before_use(self):
        diagnostics = self.lint("program { kurwa x = 1 pierdol x }")
        self.assertFalse(any(item.code in {"K010", "A010"} for item in diagnostics))

    def test_use_before_definition_is_definitely_unavailable(self):
        diagnostics = self.lint("program { pierdol x kurwa x = 1 }")
        self.assertTrue(any(item.code == "K010" and '"x"' in item.message for item in diagnostics))

    def test_both_branches_define_variable_available_after_merge(self):
        diagnostics = self.lint(
            "program { odpierdol funkcja f(flag) { "
            "jeśli flag { kurwa value = 1 } inaczej { kurwa value = 2 } pierdol value } }"
        )
        self.assertFalse(any(item.code in {"K010", "A010"} for item in diagnostics))

    def test_returning_branch_does_not_make_else_only_binding_appear_missing(self):
        diagnostics = self.lint(
            "program { odpierdol funkcja f(flag) { jeśli flag { oddaj 0 } "
            "inaczej { kurwa result = 1 } pierdol result } }"
        )
        self.assertFalse(any(item.code in {"K010", "A010"} for item in diagnostics))

    def test_binding_on_only_terminated_branch_is_unavailable_after_merge(self):
        diagnostics = self.lint(
            "program { odpierdol funkcja f(flag) { jeśli flag { "
            "kurwa result = 1 oddaj 0 } pierdol result } }"
        )
        self.assertTrue(any(item.code == "K010" and '"result"' in item.message for item in diagnostics))

    def test_maybe_defined_warning_does_not_hide_another_missing_name(self):
        diagnostics = self.lint(
            "program { odpierdol funkcja f(flag) { "
            "jeśli flag { kurwa maybe = 1 } pierdol maybe pierdol absent } }"
        )
        self.assertTrue(any(item.code == "A010" and '"maybe"' in item.message for item in diagnostics))
        self.assertTrue(any(item.code == "K010" and '"absent"' in item.message for item in diagnostics))

    def test_nested_branch_declaration_uses_runtime_shared_scope(self):
        diagnostics = self.lint(
            "program { odpierdol funkcja f(outer, inner) { "
            "jeśli outer { jeśli inner { kurwa nested = 1 } } pierdol nested } }"
        )
        self.assertTrue(any(item.code == "A010" and '"nested"' in item.message for item in diagnostics))

    def test_function_shadowing_and_outer_lookup_follow_environment_frames(self):
        source = (
            "program { kurwa value = 1 odpierdol funkcja f() { "
            "kurwa value = 2 pierdol value } pierdol value }"
        )
        analysis, diagnostics = self.flow(source)
        self.assertIn("shadowed", analysis.variable_events["value"])
        self.assertTrue(any(item.code == "A012" for item in diagnostics))
        self.assertFalse(any(item.code in {"K010", "A010"} for item in diagnostics))

    def test_function_local_binding_does_not_leak_to_caller(self):
        diagnostics = self.lint(
            "program { odpierdol funkcja f() { kurwa private = 1 } pierdol private }"
        )
        self.assertTrue(any(item.code == "K010" and '"private"' in item.message for item in diagnostics))

    def test_outer_reassignment_inside_branch_updates_merged_state(self):
        source = (
            "program { odpierdol funkcja f(flag) { kurwa value = 1 "
            "jeśli flag { zajeb value 2 } jeśli value == 1 { pierdol 1 } } }"
        )
        analysis, diagnostics = self.flow(source)
        self.assertIn("reassigned", analysis.variable_events["value"])
        self.assertFalse(any(item.code == "A020" for item in diagnostics))

    def test_loop_created_variable_is_only_possibly_available_after_loop(self):
        diagnostics = self.lint(
            "program { odpierdol funkcja f(flag) { dopóki flag { kurwa inside = 1 } pierdol inside } }"
        )
        self.assertTrue(any(item.code == "A010" and '"inside"' in item.message for item in diagnostics))

    def test_reassignment_and_collection_mutation_are_tracked(self):
        source = (
            "program { kurwa value = 1 kurwa value = 2 kurwa items = [1] "
            "wpierdol items 2 }"
        )
        analysis, _ = self.flow(source)
        self.assertIn("reassigned", analysis.variable_events["value"])
        self.assertIn("mutated", analysis.variable_events["items"])

    def test_condition_facts_detect_equality_contradiction(self):
        _, diagnostics = self.flow(
            "program { odpierdol funkcja f(x) { "
            "jeśli x == 5 { jeśli x != 5 { pierdol 1 } } } }"
        )
        self.assertTrue(any(item.code == "A020" for item in diagnostics))

    def test_condition_facts_detect_inequality_contradiction(self):
        _, diagnostics = self.flow(
            "program { odpierdol funkcja f(x) { "
            "jeśli x != 5 { jeśli x == 5 { pierdol 1 } } } }"
        )
        self.assertTrue(any(item.code == "A020" for item in diagnostics))

    def test_condition_facts_detect_exclusive_numeric_ranges(self):
        _, diagnostics = self.flow(
            "program { odpierdol funkcja f(x) { "
            "jeśli x > 10 { jeśli x <= 10 { pierdol 1 } } } }"
        )
        self.assertTrue(any(item.code == "A020" for item in diagnostics))

    def test_repeated_condition_makes_only_opposite_branch_impossible(self):
        _, diagnostics = self.flow(
            "program { odpierdol funkcja f(x) { jeśli x == 5 { "
            "jeśli x == 5 { pierdol 1 } inaczej { pierdol 2 } } } }"
        )
        self.assertTrue(any(item.code == "A020" for item in diagnostics))

    def test_compatible_conditions_are_not_marked_impossible(self):
        _, diagnostics = self.flow(
            "program { odpierdol funkcja f(x) { jeśli x > 10 { "
            "jeśli x < 20 { pierdol 1 } } } }"
        )
        self.assertFalse(any(item.code == "A020" for item in diagnostics))

    def test_unrelated_unknown_conditions_do_not_create_false_warnings(self):
        _, diagnostics = self.flow(
            "program { odpierdol funkcja f(x, y) { jeśli x > 10 { "
            "jeśli y <= 10 { pierdol 1 } } } }"
        )
        self.assertFalse(any(item.code == "A020" for item in diagnostics))

    def test_reassignment_invalidates_path_condition_facts(self):
        _, diagnostics = self.flow(
            "program { odpierdol funkcja f(x) { jeśli x == 5 { "
            "zajeb x 1 jeśli x == 5 { pierdol 1 } } } }"
        )
        self.assertFalse(any(item.code == "A020" for item in diagnostics))

    def test_outer_condition_facts_do_not_leak_into_function_body(self):
        _, diagnostics = self.flow(
            "program { odpierdol funkcja outer(x) { jeśli x == 5 { "
            "odpierdol funkcja inner() { jeśli x != 5 { pierdol 1 } } } } }"
        )
        self.assertFalse(any(item.code == "A020" for item in diagnostics))

    def test_unknown_value_is_not_mistaken_for_maybe_defined(self):
        diagnostics = self.lint(
            'program { zajeb_moduł "dane" kurwa wynik = dane.wartosc pierdol wynik }'
        )
        self.assertFalse(any(item.code == "A010" for item in diagnostics))

    def test_constant_propagation_marks_impossible_branch(self):
        diagnostics = self.lint(
            "program { kurwa liczba = 1 + 2 jeśli liczba > 2 { pierdol 1 } "
            "inaczej { pierdol 2 } }"
        )
        self.assertTrue(any(item.code == "A020" and "gałąź" in item.message for item in diagnostics))

    def test_return_in_known_branch_makes_following_statement_unreachable(self):
        diagnostics = self.lint(
            "program { odpierdol funkcja wynik() { jeśli prawda { oddaj 1 } pierdol 2 } }"
        )
        self.assertTrue(any(item.code == "A001" for item in diagnostics))

    def test_direct_return_keeps_existing_unreachable_diagnostic_without_duplicate(self):
        diagnostics = self.lint(
            "program { odpierdol funkcja wynik() { oddaj 1 pierdol 2 } }"
        )
        self.assertTrue(any(item.code == "K020" for item in diagnostics))
        self.assertFalse(any(item.code == "A001" for item in diagnostics))

    def test_function_return_inference_does_not_poison_later_type_checks(self):
        self.lint("program { odpierdol funkcja liczba() { oddaj 1 } }")
        diagnostics = self.lint('program { kurwa tekst = "tekst" pierdol tekst + 1 }')
        self.assertTrue(any(item.code == "T010" for item in diagnostics))

    def test_false_loop_is_dead_but_breaking_true_loop_reaches_next_statement(self):
        diagnostics = self.lint(
            "program { dopóki fałsz { pierdol 1 } dopóki prawda { wypierdalaj } pierdol 2 }"
        )
        self.assertTrue(any(item.code == "A020" and "Pętla" in item.message for item in diagnostics))
        self.assertFalse(any(item.code == "A001" and item.message.endswith("ścieżki.") for item in diagnostics))

    def test_unbroken_constant_loop_makes_following_code_unreachable(self):
        diagnostics = self.lint("program { dopóki prawda { pierdol 1 } pierdol 2 }")
        self.assertTrue(any(item.code == "A001" for item in diagnostics))

    def test_branch_merge_retains_equal_constants(self):
        source = (
            "program { odpierdol funkcja sprawdz(warunek) { "
            "jeśli warunek { kurwa wynik = 4 } inaczej { kurwa wynik = 4 } "
            "jeśli wynik == 4 { pierdol 1 } inaczej { pierdol 2 } } }"
        )
        _, diagnostics = self.flow(source)
        self.assertTrue(any(item.code == "A020" and item.message.startswith("Ta gałąź") for item in diagnostics))

    def test_call_graph_finds_relationships_and_recursion(self):
        source = (
            "program { odpierdol funkcja alfa() { beta() } "
            "odpierdol funkcja beta() { alfa() } alfa() }"
        )
        analysis, _ = self.flow(source)
        self.assertEqual({"beta"}, analysis.function_calls["alfa"])
        self.assertEqual({"alfa"}, analysis.function_calls["beta"])
        self.assertEqual({"alfa"}, analysis.function_calls["<program>"])
        self.assertEqual({"alfa", "beta"}, analysis.recursive_functions)

    def test_mutation_and_external_effects_are_summarized_conservatively(self):
        source = (
            'program { odpierdol funkcja zmien(lista) { wpierdol lista 1 } '
            'odpierdol funkcja zapisz() { plik.zapisz("x", "y") } }'
        )
        analysis, _ = self.flow(source)
        self.assertEqual("mutation", analysis.function_effects["zmien"])
        self.assertEqual("external", analysis.function_effects["zapisz"])

    def test_async_and_error_blocks_are_walked_without_execution(self):
        source = (
            'program { odpierdol_kurwicznie funkcja pozniej() { oddaj 1 } '
            'wjebaj { wyrzuc_kurwa "blad" } zlap_kurwa blad { pierdol blad } }'
        )
        diagnostics = self.lint(source)
        self.assertFalse(any(item.code == "K000" for item in diagnostics))
        self.assertFalse(any(item.code == "A010" for item in diagnostics))

    def test_analysis_does_not_create_marker_file(self):
        with tempfile.TemporaryDirectory() as raw:
            marker = Path(raw) / "marker.txt"
            source = (
                f'program {{ zajeb_moduł "plik" '
                f'plik.zapisz("{marker}", "uruchomione") }}'
            )
            diagnostics = self.lint(source)
            self.assertFalse(marker.exists())
            self.assertFalse(any(item.code == "K000" for item in diagnostics))

    def test_pack_and_extension_boundaries_are_not_loaded(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            package_marker = root / "package-marker.txt"
            extension_marker = root / "extension-marker.txt"
            package_source = root / "packages" / "demo" / "src" / "demo.kurwa"
            package_source.parent.mkdir(parents=True)
            package_source.write_text(
                f'program {{ zajeb_moduł "plik" plik.zapisz("{package_marker}", "x") }}',
                encoding="utf-8",
            )
            extension_source = root / "extensions" / "demo.py"
            extension_source.parent.mkdir()
            extension_source.write_text(
                f'from pathlib import Path\nPath(r"{extension_marker}").write_text("loaded")\n',
                encoding="utf-8",
            )
            main_source = root / "main.kurwa"
            main_source.write_text(
                'program { zajeb_moduł "demo" kurwa ext = zaladuj_rozszerzenie("demo") }',
                encoding="utf-8",
            )

            Linter().lint_file(main_source)

            self.assertFalse(package_marker.exists())
            self.assertFalse(extension_marker.exists())

    def test_local_module_is_resolved_and_its_ast_is_analyzed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "lib.kurwa").write_text(
                'kurwa value = missing_inside\nodpierdol funkcja answer() { oddaj 42 }\n',
                encoding="utf-8",
            )
            main_source = root / "main.kurwa"
            main_source.write_text(
                'program { zajeb_moduł "lib" pierdol lib.answer() }',
                encoding="utf-8",
            )
            diagnostics = Linter().lint_file(main_source)
            self.assertTrue(any(item.code == "K010" and item.file == str(root / "lib.kurwa") for item in diagnostics))
            self.assertFalse(any(item.code == "A040" for item in diagnostics))

    def test_repeated_import_reuses_cached_module_diagnostics(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "lib.kurwa").write_text("kurwa value = 1", encoding="utf-8")
            main_source = root / "main.kurwa"
            main_source.write_text(
                'program { zajeb_moduł "lib" zajeb_moduł "lib" pierdol lib.missing }',
                encoding="utf-8",
            )
            diagnostics = Linter().lint_file(main_source)
            missing = [item for item in diagnostics if item.code == "A040" and "missing" in item.message]
            self.assertEqual(1, len(missing))

    def test_missing_module_symbol_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "lib.kurwa").write_text("kurwa available = 1", encoding="utf-8")
            main_source = root / "main.kurwa"
            main_source.write_text(
                'program { zajeb_moduł "lib" pierdol lib.missing }',
                encoding="utf-8",
            )
            diagnostics = Linter().lint_file(main_source)
            self.assertTrue(any(item.code == "A040" and "missing" in item.message for item in diagnostics))

    def test_shadowed_module_alias_is_not_checked_as_module(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "lib.kurwa").write_text("kurwa value = 1", encoding="utf-8")
            main_source = root / "main.kurwa"
            main_source.write_text(
                'program { zajeb_moduł "lib" odpierdol funkcja f(lib) { pierdol lib.missing } }',
                encoding="utf-8",
            )
            diagnostics = Linter().lint_file(main_source)
            self.assertFalse(any(item.code == "A040" for item in diagnostics))

    def test_cyclic_local_import_is_reported_without_recursion(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "a.kurwa").write_text('zajeb_moduł "b"\n', encoding="utf-8")
            (root / "b.kurwa").write_text('zajeb_moduł "a"\n', encoding="utf-8")
            main_source = root / "main.kurwa"
            main_source.write_text('program { zajeb_moduł "a" }', encoding="utf-8")
            diagnostics = Linter().lint_file(main_source)
            self.assertTrue(any(item.code == "A041" and "a -> b -> a" in item.message for item in diagnostics))

    def test_nested_module_import_uses_module_relative_path(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "lib").mkdir()
            (root / "lib" / "inner.kurwa").write_text("kurwa answer = 42", encoding="utf-8")
            (root / "lib" / "outer.kurwa").write_text(
                'zajeb_moduł "inner"\nodpierdol funkcja answer() { oddaj inner.answer }',
                encoding="utf-8",
            )
            main_source = root / "main.kurwa"
            main_source.write_text('program { zajeb_moduł "lib/outer" }', encoding="utf-8")
            diagnostics = Linter().lint_file(main_source)
            self.assertFalse(any(item.code == "A040" for item in diagnostics))
            self.assertFalse(any(item.code == "A041" for item in diagnostics))

    def test_unresolved_import_remains_unknown(self):
        with tempfile.TemporaryDirectory() as raw:
            main_source = Path(raw) / "main.kurwa"
            main_source.write_text('program { zajeb_moduł "not_here" }', encoding="utf-8")
            diagnostics = Linter().lint_file(main_source)
            self.assertFalse(any(item.code in {"A040", "A041"} for item in diagnostics))

    def test_resolved_module_with_invalid_syntax_reports_shared_parse_error(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            module = root / "broken.kurwa"
            module.write_text("kurwa value = [1, ]", encoding="utf-8")
            main_source = root / "main.kurwa"
            main_source.write_text('program { zajeb_moduł "broken" }', encoding="utf-8")
            diagnostics = Linter().lint_file(main_source)
            self.assertTrue(any(item.code == "K000" and item.file == str(module) for item in diagnostics))

    def test_package_lock_metadata_is_checked_without_loading_package(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            package = root / "packages" / "demo"
            src = package / "src"
            src.mkdir(parents=True)
            (package / "kurwa.pack").write_text(
                "nazwa: demo\nwersja: 1.0.0\nwymagana_wersja_kurwa: 1.12.0\nzależności:\n  helper: >=2.0.0\n",
                encoding="utf-8",
            )
            (package / "kurwa.lock").write_text('{"helper": "1.0.0"}', encoding="utf-8")
            (src / "demo.kurwa").write_text("kurwa value = 1", encoding="utf-8")
            main_source = root / "main.kurwa"
            main_source.write_text('program { zajeb_moduł "demo" }', encoding="utf-8")
            diagnostics = Linter().lint_file(main_source)
            self.assertTrue(any(item.code == "A042" for item in diagnostics))

    def test_project_package_metadata_is_checked_without_installing(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "kurwa.pack").write_text(
                "nazwa: app\nwersja: 1.0.0\nwymagana_wersja_kurwa: 1.12.0\nzależności:\n  helper: >=2.0.0\n",
                encoding="utf-8",
            )
            (root / "kurwa.lock").write_text('{"helper": "1.0.0"}', encoding="utf-8")
            source = root / "main.kurwa"
            source.write_text("program { pierdol 1 }", encoding="utf-8")
            diagnostics = Linter().lint_file(source)
            self.assertTrue(any(item.code == "A042" for item in diagnostics))

    def test_duplicate_module_function_definition_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            module = root / "lib.kurwa"
            module.write_text(
                "odpierdol funkcja same() { oddaj 1 }\nodpierdol funkcja same() { oddaj 2 }",
                encoding="utf-8",
            )
            main_source = root / "main.kurwa"
            main_source.write_text('program { zajeb_moduł "lib" }', encoding="utf-8")
            diagnostics = Linter().lint_file(main_source)
            self.assertTrue(any(item.code == "A043" and item.file == str(module) for item in diagnostics))

    def test_imported_module_marker_side_effect_is_never_executed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            marker = root / "marker.txt"
            (root / "danger.kurwa").write_text(
                f'plik.zapisz("{marker}", "executed")\nkurwa value = 1',
                encoding="utf-8",
            )
            main_source = root / "main.kurwa"
            main_source.write_text('program { zajeb_moduł "danger" }', encoding="utf-8")
            from src.main import main

            with redirect_stdout(io.StringIO()):
                exit_code = main(["sprawdz_kurwa", str(main_source), "--quiet"])
            self.assertFalse(marker.exists())
            self.assertEqual(1, exit_code)

    def test_shared_cli_still_accepts_sprawdz_kurwa(self):
        from src.main import main

        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "clean.kurwa"
            source.write_text("program { pierdol 1 + 2 }", encoding="utf-8")
            self.assertEqual(0, main(["sprawdz_kurwa", str(source), "--quiet"]))

    def test_cli_checks_all_kurwa_files_in_a_directory(self):
        from src.main import main

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "main.kurwa").write_text("program { pierdol 1 }", encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "helper.kurwa").write_text("kurwa wartosc = 2", encoding="utf-8")
            self.assertEqual(0, main(["sprawdz_kurwa", str(root), "--quiet"]))


if __name__ == "__main__":
    unittest.main()