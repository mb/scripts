#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-04-11

import subprocess

def run_one_experiment(browser, early_hints, url):
    print(browser, early_hints, url)
    # ./mach raptor --browsertime -t browsertime --app chrome --browsertime-driver /usr/bin/chromedriver --browsertime-arg test_script=pageload --browsertime-arg browsertime.url="https://sourceforge.net" --browsertime-arg iterations=3 --browsertime-visualmetrics
    command = [
            # adjust to the location of gecko repository, where `./mach build` was ran
            "/home/user/dev/gecko/mach", "raptor",
            "--browsertime",
            "-t", "browsertime",
            #"--no-first-run",
            "--browsertime-arg", "test_script=pageload",
            "--browsertime-arg", "browsertime.url=" + url,
            "--browsertime-arg", "iterations=3",
            "--browsertime-visualmetrics"
    ]
    if browser == "chrome":
        command += [
                "--app", "chrome",
                "--binary", "/usr/bin/google-chrome-stable",
                "--browsertime-chromedriver", "/usr/bin/chromedriver",
        ]
        if not early_hints:
            command += [
                    "--browsertime-arg", 'chrome.args=disable-features=EarlyHintsPreloadForNavigation',
            ]
    else:
        raise ValueError("unsupported browser")
    out = subprocess.run(command)

def main():
    domains = [domain.strip() for domain in open("domains.txt")]
    for domain in domains:
        run_one_experiment("chrome", False, "https://" + domain)
    for domain in domains:
        run_one_experiment("chrome", True, "https://" + domain)

if __name__ == '__main__':
    main()
