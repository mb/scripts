#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-04-11

import subprocess
import datetime
import os

def run_one_experiment(path, browser, early_hints, connectivity, url):
    print(browser, early_hints)
    # /home/user/.mozbuild/node/bin/node /home/user/dev/gecko/tools/browsertime/node_modules/browsertime/bin/browsertime.js
    # /home/user/dev/gecko/testing/raptor/raptor/browsertime/../../browsertime/browsertime_pageload.js
    # --firefox.noDefaultPrefs
    # --browsertime.page_cycle_delay 1000
    # --skipHar
    # --pageLoadStrategy none
    # --webdriverPageload true
    # --firefox.disableBrowsertimeExtension true
    # --pageCompleteCheckStartWait 5000
    # --pageCompleteCheckPollTimeout 1000
    # --timeouts.pageLoad 72000
    # --timeouts.script 72000
    # --browsertime.page_cycles 1
    # --pageCompleteWaitTime 5000
    # --browsertime.url https://unikrn.com
    #--browsertime.post_startup_delay 30000
    # --iterations 3
    # --videoParams.androidVideoWaitTime 20000
    # --browsertime.chimera false
    # --browsertime.test_bytecode_cache false
    # --firefox.perfStats false
    # --browsertime.moz_fetch_dir None
    # --browsertime.commands  --viewPort 1280x1024 --chrome.args=--use-mock-keychain --chrome.args=--no-default-browser-check --chrome.args=--no-first-run --resultDir /home/user/dev/gecko/testing/mozharness/build/blobber_upload_dir/browsertime-results/browsertime --firefox.profileTemplate /tmp/tmp79l41ysg.mozrunner/Default --video true --visualMetrics true --visualMetricsContentful true --visualMetricsPerceptual true --visualMetricsPortable true --videoParams.keepOriginalVideo true --firefox.windowRecorder false --xvfbParams.display 0 --test_script pageload --chrome.args disable-features=EarlyHintsPreloadForNavigation --browsertime.testName browsertime --browsertime.liveSite False --browsertime.loginRequired False
    resultdir = path + "/run_"+browser+"_"+datetime.datetime.now().replace(microsecond=0).isoformat() + "_" + connectivity + "_" + url
    if early_hints:
        resultdir += "_earlyhints"
    else:
        resultdir += "_noearlyhints"
    command = [
            # adjust to the location of gecko repository, where `./mach build` was ran
            "/usr/bin/node", "/home/user/experiment/node_modules/browsertime/bin/browsertime.js",
            "--resultDir", resultdir,
            "--iterations", "3",
            "--viewPort", "1280x1024",
            "--timeToSettle", "30",
            "--flushDNS",
            "--browsertime.cacheClearRaw",
            "--xvfbParams.display", "0",
            #"--xvfb",
            "--prettyPrint",
            "--speedIndex",
            "--visualMetrics",
            "--videoParams.keepOriginalVideo",
            "--screenshot",
            "--connectivity.engine", "throttle",
            "-c", connectivity,
    ]
    if browser == "chrome":
        command += [
                "--browser", "chrome",
                "--chrome.chromedriverPath", "/usr/bin/chromedriver",
                "--chrome.binaryPath", "/usr/bin/google-chrome-stable",
                "--chrome.args=--no-default-browser-check",
        ]
        if not early_hints:
            command += [
                    "--chrome.args", "disable-features=EarlyHintsPreloadForNavigation",
            ]
    else:
        raise ValueError("unsupported browser")
    command += ["https://"+url+"/"]
    print(command)
    out = subprocess.run(command)

def main():
    import sys
    if len(sys.argv) != 2:
        print("usage:", sys.argv[0], "out_path")
    out_path = sys.argv[1] 
    os.makedirs(out_path, exist_ok=True)

    connectivities = ["3gfast", "cable", "4g", "3g"]
    urls = [url.strip() for url in open("domains.txt")]
    for c in connectivities:
        for url in urls:
            run_one_experiment(out_path, "chrome", False, c, url)
            run_one_experiment(out_path, "chrome", True, c, url)

if __name__ == '__main__':
    main()
