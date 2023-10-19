#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-10-18

import matplotlib.pyplot as plt
import numpy as np
import re
import sys

# https://stackoverflow.com/a/58790546
from matplotlib.collections import LineCollection

#CLASSIC_CC packet_sent id=3, now=14457543, pn=202934, ps=1337
#CLASSIC_CC packet_ack id=3, now=14456507, pn=202699, ps=1337, ignored=true, lost=0
#CLASSIC_CC packet_lost id=3, now=21334797, pn=343901, ps=1337
PATTERN = r"CLASSIC_CC ([a-z_]+) id=(\d+), now=(\d+), pn=(\d+), ps=(\d)"
compiled = re.compile(PATTERN)

def main():
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "LOG_FILE", "ID")
        return
    ps_sent = {} # packets pn -> (send_time, next_event_time) with next_event_time either lost_time or ack_time
    ps_ack = {} # packet number
    ps_lost = {} # (lost_time, ack_time)
    idx = int(sys.argv[2])
    max_pn = 0
    for line in open(sys.argv[1]):
        result = compiled.match(line)
        if result is None:
            continue
        if int(result.group(2)) != idx:
            continue
        event = result.group(1)
        time = int(result.group(3))
        pn = int(result.group(4))
        if event == "packet_sent":
            ps_sent[pn] = time
        elif event == "packet_ack":
            ps_ack[pn] = time
        elif event == "packet_lost":
            ps_lost[pn] = time
        
        max_pn = max(max_pn, pn)
    first = np.zeros(max_pn)

    lost_ranges_x = []
    lost_ranges_y1 = []
    lost_ranges_y2 = []
    max_delay = 0
    for i in range(max_pn):
        if i not in ps_sent:
            continue
        if i in ps_lost:
            # received both lost and ack event
            first[i] = ps_lost[i] - ps_sent[i]
            lost_ranges_x.append(i)
            lost_ranges_y1.append(first[i])
            lost_ranges_y2.append(first[i] + ps_ack[i] - ps_lost[i])
            max_delay = max(max_delay, first[i] + ps_ack[i] - ps_lost[i])
        else:
            # normal ack
            first[i] = ps_ack[i] - ps_sent[i]
            max_delay = max(max_delay, first[i])
    segs = np.zeros((max_pn, 2, 2), int)
    segs[:, 0, 0] = np.arange(max_pn) # X-Axis
    segs[:, 0, 1] # keep Y-Axis 0

    segs[:, 1, 0] = np.arange(max_pn) # X-Axis
    segs[:, 1, 1] = first # Y-Axis
    print(segs)

    line_segments = LineCollection(segs, linewidths=(1), colors=['blue']) # the color_map will be used by "complete segment"

    segs_lost = np.zeros((len(lost_ranges_x), 2, 2), int)
    segs_lost[:, 0, 0] = lost_ranges_x # X-Axis
    segs_lost[:, 0, 1] = lost_ranges_y1

    segs_lost[:, 1, 0] = lost_ranges_x # X-Axis
    segs_lost[:, 1, 1] = lost_ranges_y2
    line_segments_lost = LineCollection(segs_lost, linewidths=(1), colors=['red']) # the color_map will be used by "complete segment"
    print(line_segments)

    # https://matplotlib.org/stable/gallery/lines_bars_and_markers/bar_stacked.html
    fig, ax = plt.subplots()
    ax.add_collection(line_segments)
    ax.add_collection(line_segments_lost)
    ax.set_title('Plot test:lines with LineCollection')
    plt.grid()
    plt.xlim((0, max_pn))
    plt.ylim((0, max_delay))
    plt.show()

if __name__ == '__main__':
    main()

