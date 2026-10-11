#!/usr/bin/env python3
"""
Servidor ARENA - Inclui Python Web Framework
Pode rodar mesmo sem instalação Python (usa o embutido)
"""

import http.server
import socketserver
import os
import json
from pathlib import Path

PORT = 8000
BASE_DIR = Path(__file__).parent

class ArenaHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """<!DOCTYPE html>
<html>
<head><title>ARENA</title></head>
<body>
<h1>ARENA Console</h1>
<p>Servidor funcionando!</p>
</body>
</html>"""
            self.wfile.write(html.encode())
        else:
            super().do_GET()

if __name__ == '__main__':
    print(f"Servidor ARENA rodando na porta {PORT}")
    print(f"Acesse: http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), ArenaHandler) as httpd:
        httpd.serve_forever()
