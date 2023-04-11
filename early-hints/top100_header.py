#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-04-11

import os
import subprocess
import time

def request(host):
    fname = "header-out/"+ host + ".out"
    header = "header/"+host+".txt"
    if os.path.isfile(fname):
        return
    print(host)
    out = subprocess.run([
        "curl",
        "--connect-timeout",
        "6",
        "-D",
        header,
        "-i",
        "https://" + host
    ], capture_output=True)
    with open(fname, "wb") as f:
        f.write(out.stdout)
        f.close()
    time.sleep(1)

def get_urls():
    l = open('top100.csv').readlines()
    urls = []
    for line in l:
        line = line.strip().split(",")[1]
        urls.append(line)
    return urls

URLS = get_urls()

def main():
    for url in URLS:
        request(url)
        request('www.'+url)

if __name__ == '__main__':
    main()
