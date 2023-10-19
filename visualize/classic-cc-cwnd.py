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
PATTERN = r"CLASSIC_CC ([a-z_]+) id=(\d+), now=(\d+), pn=(\d+), ps=(\d+)"
events = re.compile(PATTERN)
#CLASSIC_CC on_packets_acked id=0, now=74806, limited=1, bytes_in_flight=0, cwnd=13370, state=SlowStart, new_acked=65
PATTERN = "CLASSIC_CC on_packets_acked id=(\d+), now=(\d+), limited=(\d+), bytes_in_flight=(\d+), cwnd=(\d+), state=([a-zA-Z]+), new_acked=(\d+)"
acked = re.compile(PATTERN)
# CLASSIC_CC on_packets_lost id=3 now=21335014, bytes_in_flight=841180, cwnd=134807, state=RecoveryStart
PATTERN = "CLASSIC_CC on_packets_lost id=(\d+), now=(\d+), bytes_in_flight=(\d+), cwnd=(\d+), state=([a-zA-Z]+)"
lost = re.compile(PATTERN)


def main():
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "LOG_FILE", "ID")
        return

    time = []
    cwnd = []
    bif = []
    idx = int(sys.argv[2])
    last_bytes_in_flight = 0
    last_state = ("SlowStart", 0)

    # event occurences
    p = {} # pn -> y-axis (bytes in flight after packet sent)
    ps = defaultdict(lambda: ([], []))
    for line in open(sys.argv[1]):
        if (result := acked.match(line)) is not None:
            if int(result.group(1)) != idx:
                continue
            now = int(result.group(2)) / 1_000_000
            time.append(now)
            limited = bool(int(result.group(3)))
            last_bytes_in_flight = int(result.group(4))
            bif.append(last_bytes_in_flight)
            cwnd.append(int(result.group(5)))
            state = result.group(6)
            last_state = (state, now)
            new_acked = result.group(7)
        elif (result := events.match(line)) is not None:
            if int(result.group(2)) != idx:
                continue
            event = result.group(1)
            now = int(result.group(3))
            pn = int(result.group(4))
            packet_size = int(result.group(5))
            if event == "packet_sent" or event == "packet_ack" or event == "packet_lost":
                if event == 'packet_sent':
                    last_bytes_in_flight += packet_size
                    p[pn] = last_bytes_in_flight
                    if last_state[0] == 'RecoveryStart':
                        last_state = ('CongestionAvoidance', now)
                    if last_state[0] == 'PersistentCongestion':
                        last_state = ('SlowStart', now)
                if pn in p:
                    ps[event][0].append(now / 1_000_000)
                    ps[event][1].append(p[pn])
        elif (result := lost.match(line)) is not None:
            if int(result.group(1)) != idx:
                continue
            now = int(result.group(2)) / 1_000_000
            time.append(now)
            last_bytes_in_flight = int(result.group(3))
            bif.append(last_bytes_in_flight)
            cwnd.append(int(result.group(4)))
            state = result.group(5)
            last_state = (state, now)
 
    fig, ax = plt.subplots()
    ax.plot(time, cwnd, label='cwnd')
    ax.plot(time, bif, '.-', label='bytes in flight')
    for (event, color) in [('packet_sent', 'black'), ('packet_ack', 'green'), ('packet_lost', 'red')][0:1]:
        ax.scatter(ps[event][0], ps[event][1], label=event, s=10, color=color)
    ax.set_xlabel('time in s')
    ax.set_ylabel('bytes')
    plt.legend()
    ax.grid()
    plt.show()

if __name__ == '__main__':
    main()
