#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-03-20

# This file is for classificating domains from the bigquery list into (non-top million, 
# Ranking domains by popularity and classifying into shopify, cloudflare, independent

import sqlite3
from ipaddress import IPv4Address, IPv4Network
import urllib.parse

def get_cloudflare():
    CLOUDFLARE = """
        103.21.244.0/22
        103.22.200.0/22
        103.31.4.0/22
        104.16.0.0/13
        104.24.0.0/14
        108.162.192.0/18
        131.0.72.0/22
        141.101.64.0/18
        162.158.0.0/15
        172.64.0.0/13
        173.245.48.0/20
        188.114.96.0/20
        190.93.240.0/20
        197.234.240.0/22
        198.41.128.0/17
    """.strip().split()
    # Bigcommerce Inc. hosted by cloudflare
    CLOUDFLARE += ["192.200.160.0/24", "63.141.128.0/24"]
    CLOUDFLARE += """
        1.0.0.0/24
        103.21.244.0/24
        103.22.200.0/24
        103.22.201.0/24
        103.22.202.0/24
        103.22.203.0/24
        103.81.228.0/24
        104.16.0.0/12
        104.16.0.0/20
        104.16.112.0/20
        104.16.128.0/20
        104.16.144.0/20
        104.16.160.0/20
        104.16.16.0/20
        104.16.176.0/20
        104.16.192.0/20
        104.16.208.0/20
        104.16.224.0/20
        104.16.240.0/20
        104.16.32.0/20
        104.16.48.0/20
        104.16.64.0/20
        104.16.80.0/20
        104.16.96.0/20
        104.17.0.0/20
        104.17.112.0/20
        104.17.128.0/20
        104.17.144.0/20
        104.17.160.0/20
        104.17.16.0/20
        104.17.176.0/20
        104.17.192.0/20
        104.17.208.0/20
        104.17.224.0/20
        104.17.240.0/20
        104.17.32.0/20
        104.17.48.0/20
        104.17.64.0/20
        104.17.80.0/20
        104.17.96.0/20
        104.18.0.0/20
        104.18.112.0/20
        104.18.128.0/20
        104.18.144.0/20
        104.18.160.0/20
        104.18.16.0/20
        104.18.176.0/20
        104.18.192.0/20
        104.18.208.0/20
        104.18.224.0/20
        104.18.240.0/20
        104.18.32.0/19
        104.18.32.0/20
        104.18.32.0/24
        104.18.33.0/24
        104.18.34.0/24
        104.18.35.0/24
        104.18.36.0/24
        104.18.37.0/24
        104.18.38.0/24
        104.18.39.0/24
        104.18.40.0/24
        104.18.41.0/24
        104.18.42.0/24
        104.18.43.0/24
        104.18.44.0/24
        104.18.45.0/24
        104.18.46.0/24
        104.18.47.0/24
        104.18.48.0/24
        104.18.49.0/24
        104.18.50.0/24
        104.18.51.0/24
        104.18.52.0/24
        104.18.53.0/24
        104.18.54.0/24
        104.18.55.0/24
        104.18.56.0/24
        104.18.57.0/24
        104.18.58.0/24
        104.18.59.0/24
        104.18.60.0/24
        104.18.61.0/24
        104.18.62.0/24
        104.18.63.0/24
        104.18.64.0/20
        104.18.80.0/20
        104.18.96.0/20
        104.19.0.0/20
        104.19.112.0/20
        104.19.128.0/20
        104.19.144.0/20
        104.19.160.0/20
        104.19.16.0/20
        104.19.176.0/20
        104.19.192.0/20
        104.19.208.0/20
        104.19.224.0/20
        104.19.240.0/20
        104.19.32.0/20
    """.strip().split()
    CLOUDFLARE = [IPv4Network(network) for network in CLOUDFLARE]

        #23.227.38.32/24
    SHOPIFY = """
        23.227.32.0/19
    """.strip().split()
    SHOPIFY = [IPv4Network(network) for network in SHOPIFY]

    # https://api.fastly.com/public-ip-list
    FASTLY = ["23.235.32.0/20","43.249.72.0/22","103.244.50.0/24","103.245.222.0/23","103.245.224.0/24","104.156.80.0/20","140.248.64.0/18","140.248.128.0/17","146.75.0.0/17","151.101.0.0/16","157.52.64.0/18","167.82.0.0/17","167.82.128.0/20","167.82.160.0/20","167.82.224.0/20","172.111.64.0/18","185.31.16.0/22","199.27.72.0/21","199.232.0.0/16"]
    FASTLY = [IPv4Network(network) for network in FASTLY]

    WIX = """
        185.230.60.0/24
        185.230.61.0/24
        185.230.62.0/24
        185.230.63.0/24
        199.15.160.0/24
        199.15.163.0/24
        204.2.207.0/24
    """.strip().split()
    WIX = [IPv4Network(network) for network in WIX]

    con = sqlite3.connect('ips.sqlite')
    cur = con.cursor()
    res = cur.execute("SELECT host, ip FROM dns")
    cdns = {'cloudflare': {}, 'shopify': {}, 'fastly': {}, 'wix': {}, 'unknown': {}}
    dom = {}
    wix_domains = []
    res = res.fetchall()
    for (host, ip) in res:
        if ip is None:
            continue
        if ip.endswith('.'):
            continue
        if host in dom:
            continue
        ip = IPv4Address(ip.lower())
        for c in CLOUDFLARE:
            if ip in c:
                cdns['cloudflare'][host] = None
                dom[host] = None
                continue
        for c in SHOPIFY:
            if ip in c:
                cdns['shopify'][host] = None
                dom[host] = None
                continue
        for c in FASTLY:
            if ip in c:
                cdns['fastly'][host] = None
                dom[host] = None
                continue
        for c in WIX:
            if ip in c:
                cdns['wix'][host] = None
                dom[host] = None
                continue

        """
        if ip.endswith('.fastly.net.'):
            cdns['fastly'][host] = None
            continue
        elif ip.endswith('.wixdns.net.'):
            cdns['wix'][host] = None
            continue
        elif ip.endswith('.myshopify.com.') or ip.endswith('.shopify.com.'):
            cdns['shopify'][host] = None
            continue
        elif ip.endswith('.cloudflare.net.'):
            cdns['cloudflare'][host] = None
        elif ip.endswith('.'):
            print(host,ip)
            continue
        if host in cdns['cloudflare']:
            continue
        for c in CLOUDFLARE:
            if IPv4Address(ip) in c:
                cdns['cloudflare'][host] = None
        """

    for (host, ip) in res:
        # no ip range available
        if host in dom or ip is None:
            continue
        ip = ip.lower()
        if ip.endswith('.wixdns.net.'):
            cdns['wix'][host] = None
            dom[host] = None
            continue

    unknown = {}
    for (host, ip) in res:
        if host in dom or ip is None:
            continue
        ip = ip.lower()
        if host in unknown:
            unknown[host].append(ip)
        else:
            unknown[host] = [ip]
            cdns['unknown'][host] = None
    output = {}
    for cdn in cdns:
        print(cdn, len(cdns[cdn]))
        for domain in cdns[cdn]:
            output[domain] = cdn
    
    return output

def main():
    # get cdn for each host
    c = get_cloudflare()
    #for cdn in c:
    #    print(cdn, len(c[cdn]))

    # get domain ranking host -> ranking
    ranking = {}
    for line in open('../top1000/tranco_PZJ8J.csv'):
        rank, d = line.strip().split(",")
        rank = int(rank)
        ranking[d.strip()] = rank

    requests = {}
    # go through desktop sites to find the rank for each
    for line in open('desktop-bq-results-20230227-143130-1677508423153.csv'):
        url, eh = line.split(",", 1)
        eh = eh[1:-2].replace('""', '"')
        domain = urllib.parse.urlparse(url).netloc
        import tldextract
        domain = tldextract.extract(domain)
        domain = domain[1] + "." + domain[2]
        if domain not in c:
            continue
        """
        if c[domain] != "fastly":
            continue
        #"""
        if domain not in ranking:
            continue
        rank = ranking[domain]
        if rank in requests:
            requests[rank][1].append((url, eh))
        else:
            requests[rank] = (domain, [(url, eh)])
    output = dict(sorted(requests.items()))
    for idx, el in enumerate(output):
        if idx == 100:
            break
        print(el,",", c[output[el][0]],",", output[el])


if __name__ == '__main__':
    main()
