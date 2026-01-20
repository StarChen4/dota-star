#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = 53000

# 如果你想校验 token，把 cfg 里的 token 填到这里
EXPECTED_TOKEN = "CHANGE_ME_TO_A_LONG_RANDOM_TOKEN"

class GSIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)

        print("\n" + "=" * 80)
        print(f"POST {self.path}  from {self.client_address[0]}:{self.client_address[1]}")

        print("\n=== HEADERS ===")
        for k, v in self.headers.items():
            print(f"{k}: {v}")

        print("\n=== RAW BODY (utf-8) ===")
        try:
            body_text = raw.decode("utf-8", errors="replace")
        except Exception:
            body_text = str(raw)
        print(body_text)

        # 尝试 JSON pretty print + token 校验（可选）
        try:
            data = json.loads(body_text)
            token = (data.get("auth") or {}).get("token")
            # if EXPECTED_TOKEN and token != EXPECTED_TOKEN:
            #     print("\n[WARN] auth.token mismatch!")
            #     print(f"  received: {token}")
            #     print(f"  expected: {EXPECTED_TOKEN}")

            print("\n=== JSON PRETTY ===")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print("\n[WARN] JSON parse failed:", e)

        # 回复 200 OK
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK\n")

    def log_message(self, format, *args):
        # 关闭 BaseHTTPRequestHandler 默认的访问日志（避免刷屏）
        return

def main():
    print(f"Listening on http://{HOST}:{PORT}/")
    print("Press Ctrl+C to stop.\n")
    HTTPServer((HOST, PORT), GSIHandler).serve_forever()

if __name__ == "__main__":
    main()