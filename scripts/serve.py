"""개발용 로컬 서버: 브라우저가 예전 HTML / CSS / JS / JSON을 캐시해 쓰지 않도록 no-cache 헤더를 붙임.

사용법 (ProGear 폴더에서): py scripts/serve.py [포트(기본 5500)]
"""

import functools
import http.server
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5500
    handler = functools.partial(NoCacheHandler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"http://localhost:{port} 에서 ProGear 실행 중 (Ctrl+C로 종료)", flush=True)
        server.serve_forever()
