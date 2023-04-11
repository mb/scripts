#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-01-23

# https://beautiful-soup-4.readthedocs.io/en/latest/#searching-the-tree
from bs4 import BeautifulSoup, NavigableString

def unstyle_html(html):
    soup = BeautifulSoup(html, features="html.parser")

    # remove all attributes except for `src` and `href`
    for tag in soup.descendants:
        keys = []
        if not isinstance(tag, NavigableString):
            for k in tag.attrs.keys():
                if k not in ["src", "href"]:
                    keys.append(k)
            for k in keys:
                del tag[k]

    # remove all script and style tags
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    # return html text
    return soup.prettify()

def main():
    import sys
    print(unstyle_html(sys.stdin.read()))

if __name__ == '__main__':
    main()
