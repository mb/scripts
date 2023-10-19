#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-10-19

import matplotlib.pyplot as plt
import numpy as np
import re
import sys
from collections import defaultdict

# https://stackoverflow.com/a/58790546
from matplotlib.collections import LineCollection

#CLASSIC_CC packet_sent id=3, now=14457543, pn=202934, ps=1337
#CLASSIC_CC packet_ack id=3, now=14456507, pn=202699, ps=1337, ignored=true, lost=0
#CLASSIC_CC packet_lost id=3, now=21334797, pn=343901, ps=1337
#CLASSIC_CC on_packets_acked id=0, now=74806, limited=1, bytes_in_flight=0, cwnd=13370, state=SlowStart, new_acked=65
PATTERN = "CLASSIC_CC on_packets_acked id=(\d+), now=(\d+), limited=(\d+), bytes_in_flight=(\d+), cwnd=(\d+), state=([a-zA-Z]+), new_acked=(\d+)"
compiled = re.compile(PATTERN)

def main():
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "LOG_FILE", "ID")
        return

    time = []
    cwnd = []
    bif = []
    ps = defaultdict(lambda: ([], []))
    idx = int(sys.argv[2])
    for line in open(sys.argv[1]):
        result = compiled.match(line)
        if result is None:
            continue
        if int(result.group(1)) != idx:
            continue
        time.append(int(result.group(2)) / 1_000_000)
        limited = bool(int(result.group(3)))
        bif.append(int(result.group(4)))
        cwnd.append(int(result.group(5)))
        state = result.group(6)
        new_acked = result.group(7)

    fig, ax = plt.subplots()
    ax.plot(time, cwnd, label='cwnd')
    ax.plot(time, bif, label='bytes in flight')
    ax.set_xlabel('time in s')
    ax.set_ylabel('bytes')
    plt.legend()
    ax.grid()
    plt.show()

if __name__ == '__main__':
    main()
