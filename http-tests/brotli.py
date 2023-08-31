#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-06-28
# Bugzilla: https://bugzilla.mozilla.org/show_bug.cgi?id=1715401

from http.server import HTTPServer, BaseHTTPRequestHandler
import brotli
import time

class BrotliServer(BaseHTTPRequestHandler):
    def br(self, length, truncated):
        self.send_header("Content-Encoding", "br")
        content = b"\x01\x03"+ b"\x06"*length # + b"\x03"
        if not truncated:
            content += b"\x03"
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def br_test(self):
        self.send_header("Content-Encoding", "br")
        content = b"\x0b\x0a\x09"
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        self.send_response(200)
        print(self.path)
        if self.path == "/":
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            content = b"""<html>
<body>
<script type="module">
{
let request = await fetch("http://localhost:8000/br/10/");
let response = await request.text();
console.log(response);
}
{
let request = await fetch("http://localhost:8000/br/10/truncated");
let response = await request.text();
console.log(response);
}
{
let request = await fetch("http://localhost:8000/br/1000/");
let response = await request.text();
console.log(response);
}
{
let request = await fetch("http://localhost:8000/br/1000/truncated");
let response = await request.text();
console.log(response);
}
{
let request = await fetch("http://localhost:8000/br_test");
let response = await request.text();
console.log(response);
}
</script>
</body>
</html>
"""
            self.send_header("Content-Length", len(content))
            self.wfile.write(content)
        elif self.path == "/br_test":
            self.br_test()
        elif self.path.startswith("/br/"):
            _, _, length, truncated = self.path.split("/")
            self.br(int(length), truncated == "truncated")
        

if __name__ == '__main__':
    HTTPServer(("127.0.0.1", 8000), BrotliServer).serve_forever()
