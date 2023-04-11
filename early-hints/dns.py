#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-03-20

# A python script to lookup ips behind each domain

# sqlite
# domain date ipv4

# DOH
DOH_SERVER = "cloudflare-dns.com"
import requests
s = requests.Session()
def doh_query(name, type='A', server=DOH_SERVER, path="/dns-query", verbose=False):
    import json
    retval = None
    req = s.get("https://%s%s?name=%s&type=%s" % (server, path, name, type), headers={"Accept": "application/dns-json"})
    reply = req.json()

    if "Answer" in reply:
        answer = reply["Answer"]
        retval = [_["data"] for _ in answer]
    else:
        retval = []

    return retval

def get_sqlite(filename):
    import sqlite3
    con = sqlite3.connect(filename)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS dns(host, ip, timestamp);")
    con.commit()
    return con

def get_domain_names(filename):
    import urllib.parse
    domains = {}
    with open(filename) as f:
        for row in f:
            row = row.split(',')
            domain = urllib.parse.urlparse(row[0]).netloc
            if domain not in domains:
                domains[domain] = None
    return domains.keys()

def sqlite_contains(cur, domain):
    res = cur.execute("SELECT host FROM dns WHERE host = ?", (domain,))
    return res.fetchone() is not None

def get_existing_domains(cur):
    res = cur.execute("SELECT host FROM dns")
    res = {domain[0]: None for domain in res.fetchall()}
    print(res)
    return res

def sqlite_add(cur, domain, ips):
    import datetime
    time = datetime.datetime.now()
    if len(ips) == 0:
        ips = [None]
    data = [(domain, ip, time) for ip in ips]
    cur.executemany("INSERT INTO dns(host, ip, timestamp) VALUES (?, ?, ?)", data)

def main():
    import argparse
    parser = argparse.ArgumentParser(prog = 'dns.py',
                                     description = 'Fetch ips of domains not yet requested specified in csv file')
    parser.add_argument('filename', help='filename of the csv file to parse')
    parser.add_argument('--sqlite', default='ips.sqlite', help='sqlite file to store the result')
    args = parser.parse_args()

    sqlite = get_sqlite(args.sqlite)
    cur = sqlite.cursor()

    domains = list(get_domain_names(args.filename))
    existing_domains = get_existing_domains(cur)
    print(len(domains))
    #import random
    #random.shuffle(domains)
    import tqdm
    for domain in tqdm.tqdm(domains):
        #if not sqlite_contains(cur, domain):
        if not domain in existing_domains:
            tqdm.tqdm.write(domain)
            sqlite_add(cur, domain, doh_query(domain))
            sqlite.commit()

    sqlite.close()

if __name__ == '__main__':
    main()
