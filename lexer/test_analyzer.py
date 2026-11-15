import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import draft
from gui import interpreterGUI


class WidgetStub:
    def __init__(self, source=""):
        self.source = source
        self.rows = []

    def get(self, *args):
        return self.source

    def get_children(self):
        return list(self.rows)

    def delete(self, row):
        self.rows.remove(row)

    def insert(self, *args, **kwargs):
        item = str(len(self.rows))
        self.rows.append(item)
        return item


class AnalyzerTests(unittest.TestCase):
    def test_lexes_visible_operators_without_spaces(self):
        tokens, errors = draft.lex('HAI\nVISIBLE left+right!\nKTHXBYE')

        self.assertEqual(errors, [])
        self.assertIn(("+", "Concatenation Operator", 2), tokens)
        self.assertIn(("!", "Output Suppressor", 2), tokens)

    def test_valid_bundled_samples_pass_syntax_analysis(self):
        examples = Path(__file__).parent / "example"
        for name in ("sample.lol", "sample3.lol", "sample4.lol"):
            with self.subTest(sample=name):
                result = draft.analyze((examples / name).read_text(encoding="utf-8-sig"))
                self.assertEqual(result[1], [])
                self.assertEqual(result[3], [])

    def test_error_samples_fail_in_the_expected_analyzer(self):
        examples = Path(__file__).parent / "example"
        expected = {
            "error_lex_unknown_lexeme.lol": ("lex", "unknown lexeme"),
            "error_lex_unclosed_string.lol": ("lex", "missing its closing quote"),
            "error_syntax_missing_expression.lol": ("syntax", "expected an expression"),
            "error_syntax_unmatched_block.lol": ("syntax", "has no matching"),
        }

        for name, (phase, message) in expected.items():
            with self.subTest(sample=name):
                source = (examples / name).read_text(encoding="utf-8-sig")
                _, lexical_errors, _, syntax_errors = draft.analyze(source)
                self.assertEqual(bool(lexical_errors), phase == "lex")
                errors = lexical_errors if phase == "lex" else syntax_errors
                self.assertTrue(any(message in error for error in errors), errors)

    def test_multiple_error_sample_has_several_parser_errors(self):
        examples = Path(__file__).parent / "example"
        source = (examples / "error_syntax_multiple_errors.lol").read_text(
            encoding="utf-8-sig"
        )
        _, lexical_errors, _, syntax_errors = draft.analyze(source)

        self.assertEqual(lexical_errors, [])
        self.assertGreaterEqual(len(syntax_errors), 2)

    def test_gui_displays_only_the_first_syntax_error(self):
        app = object.__new__(interpreterGUI)
        app.editor = WidgetStub("HAI\nVISIBLE\nVISIBLE\nKTHXBYE")
        app.table = WidgetStub()
        app.symbol_table = WidgetStub()
        app.token_info = {}
        app.clear_highlight = lambda: None
        console = []
        app.console_clear = console.clear
        app.console_write = lambda text, tag=None: console.append((text, tag))
        executed = []
        app.run_program = lambda tokens: executed.append(tokens)

        app.execute()

        errors = [text for text, tag in console if tag == "error"]
        self.assertEqual(len(errors), 1)
        self.assertIn("Line 2:", errors[0])
        self.assertEqual(executed, [])


if __name__ == "__main__":
    unittest.main()
