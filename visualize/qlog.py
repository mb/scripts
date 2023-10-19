#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-10-06

import sys
import json
import matplotlib.pyplot as plt

def main():
    # Parse log file
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <log_filename>")
        sys.exit(1)

    qlog = json.load(open(sys.argv[1]))
    events = qlog['traces'][0]['events']
    for event in events:
        relative_time, category, event_type, data = event
        print(event)

if __name__ == '__main__':
    main()

