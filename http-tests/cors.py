#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-08-31
# Bugzilla: https://bugzilla.mozilla.org/show_bug.cgi?id=1849831#c5

# Additionally having this in `/etc/hosts`:
# ```
# 127.0.0.1       foo.example.com
# 127.0.0.1       bar.example.com
# 127.0.0.1       a.test
# 127.0.0.1       b.test
# 127.0.0.1       c.test
# ```
# and doing fetch("http://c.test:8080/hello") from devtools on the first 4 origins.
#
# This creates a http server that always sets CORS headers to allow the fetch
# content is always "ok"

import socket

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 8080))
        s.listen()
        while True:
            conn, addr = s.accept()
            host = b""
            print('connected by', addr)
            for line in conn.makefile("rb"):
                print("line", line)
                if line.strip() == b"":
                    out = b"""HTTP/1.0 200 OK\r\n\
Access-Control-Allow-Origin: """ + host + b"""\r\n\
Access-Control-Allow-Headers: *\r\n\
Connection: close\r\n\
Content-Length: 2\r\n\
Cache-Control: max-age=604800\r\n\
\r\n\
ok"""
                    print("resp:", out)
                    conn.sendall(out)
                    conn.close()
                    break
                if line.startswith(b"Origin:"):
                    host = line.split(b":", 1)[1].strip()

if __name__ == '__main__':
    main()
