#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-11-02

import matplotlib.pyplot as plt
import numpy as np
import re
import sys
from collections import defaultdict
from datetime import datetime

#2023-11-02 13:32:28.450290 UTC - [Parent 31525: Socket Thread]: I/neqo_transport::* [neqo_transport::cc::classic_cc] packet_sent this=0x7f84d3d31100, pn=111, ps=36
#2023-11-02 13:32:28.477635 UTC - [Parent 31525: Socket Thread]: I/neqo_transport::* [neqo_transport::cc::classic_cc] packet_acked this=0x7f84d3d31100, pn=111, ps=36, ignored=0, lost=0
#2023-11-02 13:55:02.954829 UTC - [Parent 41203: Socket Thread]: I/neqo_transport::* [neqo_transport::cc::classic_cc] packet_lost this=0x7f2864efcc80, pn=308694, ps=1337
PATTERN = r" ([a-z_]+) this=0x([0-9a-f]+), pn=(\d+), ps=(\d+)"
events = re.compile(PATTERN)

#2023-11-02 13:32:28.477655 UTC - [Parent 31525: Socket Thread]: I/neqo_transport::* [neqo_transport::cc::classic_cc] on_packets_acked this=0x7f84d3d31100, limited=1, bytes_in_flight=0, cwnd=13370, state=SlowStart, new_acked=36
PATTERN = r" on_packets_acked this=0x([0-9a-f]+), limited=(\d+), bytes_in_flight=(\d+), cwnd=(\d+), state=([a-zA-Z]+), new_acked=(\d+)"
acked = re.compile(PATTERN)
#2023-11-02 13:55:02.954909 UTC - [Parent 41203: Socket Thread]: I/neqo_transport::* [neqo_transport::cc::classic_cc] on_packets_lost this=0x7f2864efcc80, bytes_in_flight=690883, cwnd=1520187, state=RecoveryStart
PATTERN = r" on_packet_lost this=0x([0-9a-f]+), bytes_in_flight=(\d+), cwnd=(\d+), state=([a-zA-Z]+)"
lost = re.compile(PATTERN)

def get_time(line):
    return datetime.strptime(line.split(" UTC", 1)[0], "%Y-%m-%d %H:%M:%S.%f")

def main():
    if len(sys.argv) < 2:
        print("usage:", sys.argv[0], "LOG_FILE")
        return

    data = defaultdict(lambda: {
        "time": [],
        "cwnd": [],
        "bif": [],
        "bif_limited": [],
        "bif_limited_time": [],
        "last_bytes_in_flight": 0,
        "last_state": ("SlowStart", 0),

        # event occurences
        "p": {}, # pn -> y-axis (bytes in flight after packet sent)
        "ps": defaultdict(lambda: defaultdict(lambda: [])), # x/y coords of packet_sent/_acked/_lost
    })

    for line in open(sys.argv[1]):
        if (result := acked.search(line)) is not None:
            this = result.group(1)
            now = get_time(line)
            data[this]["time"].append(now)
            data[this]["limited"] = bool(int(result.group(2)))
            data[this]["last_bytes_in_flight"] = int(result.group(3))
            data[this]["bif"].append(data[this]["last_bytes_in_flight"])
            data[this]["cwnd"].append(int(result.group(4)))
            state = result.group(5)
            data[this]["last_state"] = (state, now)
            data[this]["new_acked"] = result.group(6)
            if data[this]["limited"]:
                data[this]["bif_limited"].append(data[this]["last_bytes_in_flight"])
                data[this]["bif_limited_time"].append(now)
        elif (result := events.search(line)) is not None:
            this = result.group(2)
            now = get_time(line)
            event = result.group(1)
            pn = int(result.group(3))
            packet_size = int(result.group(4))
            if event == "packet_sent" or event == "packet_acked" or event == "packet_lost":
                if event == 'packet_sent':
                    data[this]["last_bytes_in_flight"] += packet_size
                    data[this]["p"][pn] = data[this]["last_bytes_in_flight"]
                    if data[this]["last_state"][0] == 'RecoveryStart':
                        data[this]["last_state"] = ('CongestionAvoidance', now)
                    if data[this]["last_state"] == 'PersistentCongestion':
                        data[this]["last_state"] = ('SlowStart', now)
                # only remember events for packets where we sent the packet
                if pn in data[this]["p"]:
                    data[this]["ps"][event]["time"].append(now)
                    data[this]["ps"][event]["bif"].append(data[this]["p"][pn])
                    data[this]["ps"][event]["pn"].append(pn)
        elif (result := lost.search(line)) is not None:
            this = result.group(1)
            now = get_time(line)
            data[this]["time"].append(now)
            data[this]["last_bytes_in_flight"] = int(result.group(3))
            data[this]["bif"].append(last_bytes_in_flight)
            data[this]["cwnd"].append(int(result.group(4)))
            state = result.group(5)
            data[this]["last_state"] = (state, now)

    output = ""
    output_num = 0
    for el in data:
        if len(data[el]["time"]) > output_num:
            output_num = len(data[el]["time"])
            output = el

    COLORS = {
            'packet_sent': 'black',
            'packet_lost': 'red',
            'packet_acked': 'green',
    }
 
    fig, ax = plt.subplots()
    if len(sys.argv) > 2 and sys.argv[2] == "pn":
        for event in ['packet_sent', 'packet_acked', 'packet_lost']:
            ax.scatter(data[output]["ps"][event]["time"], data[output]["ps"][event]["pn"], label=event, s=10, color=COLORS[event])
    else:
        ax.plot(data[output]["time"], data[output]["cwnd"], label='cwnd')
        ax.plot(data[output]["time"], data[output]["bif"], '.-', label='bytes in flight')
        ax.plot(data[output]["bif_limited_time"], data[output]["bif_limited"], 's', label='app_limited')
        for (event, color) in ['packet_sent', 'packet_lost']:
            ax.scatter(data[output]["ps"][event]["time"], data[output]["ps"][event]["bif"], label=event, s=10, color=COLORS[event])
        ax.set_xlabel('time in s')
        ax.set_ylabel('bytes')
        ax.set_title(sys.argv[1].split('/')[-1])
    plt.legend()
    ax.grid()
    plt.show()

if __name__ == '__main__':
    main()
