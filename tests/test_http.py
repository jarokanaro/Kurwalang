import io
import json
import time
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlparse

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser


class HttpTestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _safe_write(self, payload: bytes) -> None:
        try:
            self.wfile.write(payload)
        except BrokenPipeError:
            pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/ping":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("X-Test", "kurwa")
            self.end_headers()
            self._safe_write(b"pong")
            return
        if parsed.path == "/json":
            payload = {"imie": "Jaro", "wiek": 19, "aktywny": True, "tekst": "żółć 😎"}
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self._safe_write(body)
            return
        if parsed.path == "/query":
            params = parse_qs(parsed.query)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self._safe_write(f"{params.get('q', [''])[0]}|{params.get('limit', [''])[0]}".encode("utf-8"))
            return
        if parsed.path == "/slow":
            time.sleep(0.5)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self._safe_write(b"za wolno")
            return
        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self._safe_write(b"brak")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        parsed = urlparse(self.path)
        if parsed.path == "/echo":
            payload = json.loads(body.decode("utf-8"))
            response = {
                "echo": payload,
                "header": self.headers.get("X-Test", ""),
                "method": "POST",
            }
            data = json.dumps(response, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self._safe_write(data)
            return
        if parsed.path == "/echo-text":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self._safe_write(body)
            return
        self.send_response(500)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self._safe_write(b"bad")

    def do_PUT(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        parsed = urlparse(self.path)
        self.send_response(201 if parsed.path == "/put" else 200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self._safe_write(body)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path == "/delete-empty":
            self.send_response(204)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self._safe_write(b"usuniete")

    def do_PATCH(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self._safe_write(b"patch")

    def log_message(self, fmt, *args):
        return


class HttpServerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), HttpTestHandler)
        cls.server_url = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def run_program(self, source: str) -> str:
        program = Parser(Lexer(source).tokenize()).parse()
        output = io.StringIO()
        with redirect_stdout(output):
            Interpreter().run(program, Path("/tmp/kurwa-http.kurwa"))
        return output.getvalue()

    def test_get_response_fields(self):
        source = f'''
        program {{
            zajeb_moduł "siec"
            kurwa odp = siec.wjeb("{self.server_url}/ping")
            pierdol odp["status_kurwa"]
            pierdol odp["tekst_kurwa"]
            pierdol odp["naglowki_kurwa"]["X-Test"]
        }}
        '''
        self.assertEqual(self.run_program(source), "200\npong\nkurwa\n")

    def test_get_query_parameters_and_json(self):
        source = f'''
        program {{
            zajeb_moduł "dane"
            zajeb_moduł "siec"
            kurwa query = {{"q": "żółć 😎", "limit": 2}}
            kurwa odp = siec.wjeb("{self.server_url}/query", query, {{"X-Test": "kurwa"}})
            pierdol odp["tekst_kurwa"]
            kurwa json_data = siec.wjeb("{self.server_url}/json")
            pierdol json_data["json_kurwa"]["imie"]
            pierdol json_data["json_kurwa"]["tekst"]
        }}
        '''
        self.assertEqual(self.run_program(source), "żółć 😎|2\nJaro\nżółć 😎\n")

    def test_post_json_and_headers(self):
        source = f'''
        program {{
            zajeb_moduł "siec"
            kurwa dane = {{"imie": "Jaro", "wiek": 19}}
            kurwa odp = siec.wyślij("{self.server_url}/echo", dane, {{"X-Test": "kurwa"}})
            pierdol odp["status_kurwa"]
            pierdol odp["json_kurwa"]["echo"]["imie"]
            pierdol odp["json_kurwa"]["header"]
        }}
        '''
        self.assertEqual(self.run_program(source), "200\nJaro\nkurwa\n")

    def test_put_delete_and_generic_request(self):
        source = f'''
        program {{
            zajeb_moduł "siec"
            kurwa put_resp = siec.wrzuć("{self.server_url}/put", "dupa")
            pierdol put_resp["status_kurwa"]
            pierdol put_resp["tekst_kurwa"]
            kurwa del_resp = siec.wyjeb("{self.server_url}/delete")
            pierdol del_resp["status_kurwa"]
            pierdol del_resp["tekst_kurwa"]
            kurwa empty_resp = siec.wyjeb("{self.server_url}/delete-empty")
            pierdol empty_resp["status_kurwa"]
            pierdol empty_resp["tekst_kurwa"]
            kurwa generic = siec.zjeb("PATCH", "{self.server_url}/ping", "cokolwiek")
            pierdol generic["status_kurwa"]
        }}
        '''
        self.assertEqual(self.run_program(source), "201\ndupa\n200\nusuniete\n204\n\n200\n")

    def test_http_errors_and_status(self):
        source = f'''
        program {{
            zajeb_moduł "siec"
            kurwa missing = siec.wjeb("{self.server_url}/missing")
            pierdol missing["status_kurwa"]
            kurwa invalid = siec.wjeb("brak")
        }}
        '''
        with self.assertRaisesRegex(InterpreterError, "niepoprawny URL|URL"):
            self.run_program(source)

    def test_invalid_url_rejected(self):
        with self.assertRaisesRegex(InterpreterError, "niepoprawny URL"):
            self.run_program('program { zajeb_moduł "siec" pierdol siec.wjeb("nope") }')

    def test_timeout_is_reported_as_http_error(self):
        source = f'''
        program {{
            zajeb_moduł "siec"
            kurwa odp = siec.wjeb("{self.server_url}/slow", {{}}, {{}}, 0.05)
        }}
        '''
        with self.assertRaisesRegex(InterpreterError, "timeout|przekroc|limit czasu"):
            self.run_program(source)

    def test_refused_connection_is_reported_cleanly(self):
        source = '''
        program {
            zajeb_moduł "siec"
            kurwa odp = siec.wjeb("http://127.0.0.1:65535/ping")
        }
        '''
        with self.assertRaisesRegex(InterpreterError, "połączenie|odrzucone|refused|nie odpowiada"):
            self.run_program(source)

    def test_text_body_is_sent_as_text_not_json(self):
        source = f'''
        program {{
            zajeb_moduł "siec"
            kurwa odp = siec.wyślij("{self.server_url}/echo-text", "żółć 😎", {{"Content-Type": "text/plain; charset=utf-8"}})
            pierdol odp["tekst_kurwa"]
        }}
        '''
        self.assertEqual(self.run_program(source), "żółć 😎\n")


if __name__ == "__main__":
    unittest.main()
