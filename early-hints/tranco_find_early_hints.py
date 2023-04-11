#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-04-11

# This script uses curl to scrape the top x websites for Early Hints.  It
# essentially just downloads the main page of each domain (with and without
# the 'www.' prefix) including the http headers and stores the result in the
# 'early-hint/' directory. It uses the tranco list[1] as input.
# To get a list of the domains the following bash commands can be used
# 
#     $ rg '^HTTP/' | rg ' 103' | awk -F '_' '{ print $1 }' | sed 's/+.*+//' | sed 's/www\.//' | sort | uniq | tee ../domains.csv | wc -l
#     $ xsv join --no-headers 1 ../domains.csv 2 ../tranco_PZJ8J.csv | xsv select 2,3 | sort -h | tee top100.csv
#
# Using ripgrep[2] and xsv[3] utilities. The resulting top100.csv can be found
# in the same directory.  It would have been better to store the headers
# separatly with `-D headers.txt` as described in the `-i` introduction blog
# post[4].
# 
# [1]: https://tranco-list.eu/
# [2]: https://github.com/BurntSushi/ripgrep
# [3]: https://github.com/BurntSushi/xsv
# [4]: https://daniel.haxx.se/blog/2022/03/24/easier-header-picking-with-curl/

import os.path
import time
import subprocess

from multiprocessing import Process, Value, Lock

# https://eli.thegreenplace.net/2012/01/04/shared-counter-with-pythons-multiprocessing
class Counter(object):
    def __init__(self, initval=0):
        self.val = Value('i', initval)
        self.lock = Lock()

    def increment(self):
        ret = 0
        with self.lock:
            self.val.value += 1
            ret = self.val.value
        return ret

    def value(self):
        with self.lock:
            return self.val.value


def get_urls():
    l = open('tranco_PZJ8J.csv').readlines()
    urls = []
    for (cur, line) in enumerate(l):
        urls.append((cur,line))
        if cur > 30000:
            return urls

URLS = get_urls()

def process(k, c):
    while True:
        idx = c.increment()
        if idx >= len(URLS):
            print("done", k)
            return
        cur, line = URLS[idx]
        url1 = line.strip().split(',', 1)[1]
        url2 = 'www.' + line.strip().split(',', 1)[1]
        print(cur)
        for i in range(2):
            request(url1, i, cur)
            request(url2, i, cur)

def process0(c):
    process(0, c)

def process1(c):
    process(1, c)

def process2(c):
    process(2, c)

def process3(c):
    process(3, c)

def process4(c):
    process(4, c)

def process5(c):
    process(5, c)

def process6(c):
    process(6, c)

def process7(c):
    process(7, c)

def process8(c):
    process(8, c)

def process9(c):
    process(9, c)

def process10(c):
    process(10, c)

def request(host, i, rank):
    fname = "early-hints/+"+str(rank) +"+"+ host + "_" + str(i) + ".out"
    if os.path.isfile(fname):
        return
    print(host, i)
    out = subprocess.run(["curl", "--connect-timeout", "6", "-iL", "https://" + host], capture_output=True)
    with open(fname, "wb") as f:
        f.write(out.stdout)
        f.close()
    time.sleep(1)

def main():
    c = Counter()
    ps = [
            Process(target=process0, args=(c,)),
            Process(target=process1, args=(c,)),
            Process(target=process2, args=(c,)),
            Process(target=process3, args=(c,)),
            Process(target=process4, args=(c,)),
            Process(target=process5, args=(c,)),
            Process(target=process6, args=(c,)),
            Process(target=process7, args=(c,)),
            Process(target=process8, args=(c,)),
            Process(target=process9, args=(c,)),
            Process(target=process10, args=(c,)),
          ]
    for p in ps:
        p.start()

if __name__ == '__main__':
    main()
