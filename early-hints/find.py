#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-02-27

def main():
    domains = {}
    with open('../top1000/htmlstrip-alexa.csv') as f:
        for (idx, el) in enumerate(f):
            domains[el.strip()] = idx

    with open('domains-sort.txt') as f:
        for cur_domain in f:
            domain = cur_domain.strip().split('.')
            tld = domain[-2] + '.' + domain[-1]
            if tld in domains:
                #print(tld, domains[tld], cur_domain.strip())
                print(domains[tld], tld)

if __name__ == '__main__':
    main()
