#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher
# Date: 2023-03-20

# using https://screenspan.net/blog/webpagetest-api-with-python/ as basis

import requests
import config
import urllib.parse

def test_url(url, eh: bool, firefox: bool, connectivity):
    """
    connectivity: Cable, 3G, 3g-fast, 4G
    """
    if firefox:
        browser = "Firefox"
    else:
        browser = "Chrome"
    if connectivity == "Cable" or connectivity == "3G" or connectivity == "4G" or connectivity == "3G-Fast":
        pass
    else:
        raise ValueError('unexpected connectivity')

    domain = urllib.parse.urlparse(url).netloc
    endpoint = f'https://www.webpagetest.org/runtest.php?url={url}'

    test_options = {
            "label": f'{domain} - EH {eh} - Firefox: {firefox} - Connectivity - {connectivity}'
            "k": config.wpt_api_key,
            "f": "json",
            "runs": 1,
            "location": f"ec2-eu-central-1:{browser}.{connectivity}"
            "private": 0 #make it accessible
            "mobile": int(connectivity != "Cable")
    }
    # enable/disable early hints
    if firefox:
        script = f"""
firefoxPref netwerk.early-hints.enabled {int(eh)}
firefoxPref netwerk.early-hints.preconnect.enabled {int(eh)}
"""
        test_options['script'] = script
    else:
        # --enable-features=EarlyHintsPreloadForNavigation
        pass

    response = requests.get(endpoint)
    print(response.json())

def main():
    pass

if __name__ == '__main__':
    main()
