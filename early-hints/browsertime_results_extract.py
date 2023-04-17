#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-04-12

import os
import os.path
import json

def get_metric_dict():
    return {
            'fcp': {True: [], False: []},
            'lcp': {True: [], False: []},
    }

def get_connection_dict():
    return {
            'cable': get_metric_dict(),
            '4g': get_metric_dict(),
            '3g': get_metric_dict(),
            '3gfast': get_metric_dict(),
    }

def main():
    files = os.listdir()
    dirs = [d for d in os.listdir() if not os.path.isfile(d)]
    results = {
            'chrome': get_connection_dict(),
            #'firefox': get_connection_dict(),
    }
    for d in dirs:
        print(d)
        _, browser, time, connection, domain, eh = d.split('_')
        if domain == "www.ozon.ru" or \
                domain == "www.thredup.com" or \
                domain == "www.vseinstrumenti.ru" or \
                domain == "www.fiverr.com" or \
                domain == "padlet.com":
            # skip domains where I ran into rate limits
            continue
        eh = eh == "earlyhints" # true for earhy hints enabled
        browsertime_info = d + "/browsertime.har"
        inp = json.loads(open(browsertime_info).read())
        for p in inp['log']['pages']:
            # TODO: '_domInteractiveTime': 3179, '_domContentLoadedTime': 3179, 'onContentLoad': 3192.512, 'onLoad': 4521.977,
            results[browser][connection]['fcp'][eh].append(p['pageTimings']['_firstContentfulPaint'])
            results[browser][connection]['lcp'][eh].append(p['pageTimings']['_largestContentfulPaint'])

    for browser in results:
        for connection in results[browser]:
            with open(browser+"_"+connection+".json", "w") as f:
                f.write(json.dumps(results[browser][connection]))

if __name__ == '__main__':
    main()
