#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-02-20

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def try_load(browser, domain):
    try:
        browser.get("https://" + domain)
        browser.save_screenshot("screenshots/" + domain + ".png")
        print(domain + ","+ browser.current_url)
        time.sleep(0.2)
    except:
        try:
            browser.get("https://www." + domain)
            browser.save_screenshot("screenshots/" + domain + ".png")
            print(domain.strip() + ","+ browser.current_url)
            time.sleep(0.2)
        except:
            print(domain.strip() + ",")

def add_urls(browser, path, url_idx, added):
    with open(path) as f:
        for line in f:
            if line.strip() == '':
                continue
            url = line.split(',')[url_idx].strip()
            if url in added:
                continue
            added[url] = None
            eprint(url)
            try_load(browser, url.strip())

def main():
    added = {}
    with open('redirect.csv') as f:
        for line in f:
            domain = line.split(',')[0]
            added[domain] = None
    options = Options()
    options.headless = True
    browser = webdriver.Firefox(options=options)
    browser.implicitly_wait(10)
    add_urls(browser, 'htmlstrip-alexa.csv', 0, added)
    browser.quit()

if __name__ == '__main__':
    main()
