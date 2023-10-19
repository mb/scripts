#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-10-19

import matplotlib.pyplot as plt
import re
import sys
from collections import defaultdict

#CLASSIC_CC packet_sent id=3, now=14457543, pn=202934, ps=1337
#CLASSIC_CC packet_ack id=3, now=14456507, pn=202699, ps=1337, ignored=true, lost=0
#CLASSIC_CC packet_lost id=3, now=21334797, pn=343901, ps=1337
PATTERN = r"CLASSIC_CC ([a-z_]+) id=(\d+), now=(\d+), pn=(\d+), ps=(\d)"
compiled = re.compile(PATTERN)

def main():
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "LOG_FILE", "ID")
        return

    ps = defaultdict(lambda: ([], []))
    idx = int(sys.argv[2])
    for line in open(sys.argv[1]):
        result = compiled.match(line)
        if result is None:
            continue
        if int(result.group(2)) != idx:
            continue
        event = result.group(1)
        time = int(result.group(3))
        pn = int(result.group(4))
        if event == "packet_sent" or event == "packet_ack" or event == "packet_lost":
            ps[event][0].append(time / 1000000)
            ps[event][1].append(pn)

    fig, ax = plt.subplots()
    for event in ['packet_sent', 'packet_ack', 'packet_lost']:
        ax.scatter(ps[event][0], ps[event][1], label=event, s=10)
    ax.set_xlabel('time in s')
    ax.set_ylabel('packet number')
    plt.legend()
    ax.grid()
    plt.show()

if __name__ == '__main__':
    main()
