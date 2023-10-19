#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-10-19

import re
import sys

#CLASSIC_CC on_packets_acked id=0, now=74806, limited=1, bytes_in_flight=0, cwnd=13370, state=SlowStart, new_acked=65
PATTERN = "CLASSIC_CC on_packets_acked id=(\d+), now=(\d+), limited=(\d+), bytes_in_flight=(\d+), cwnd=(\d+), state=([a-zA-Z]+), new_acked=(\d+)"
acked = re.compile(PATTERN)

def main():
    if len(sys.argv) != 4:
        print("usage:", sys.argv[0], "LOG_FILE", "ID", "TIME_IN_S")
        return
    idx = int(sys.argv[2])
    time = int(sys.argv[3])

    num_limited = 0
    total = 0

    for line in open(sys.argv[1]):
        if (result := acked.match(line)) is not None:
            if int(result.group(1)) != idx:
                continue
            now = int(result.group(2)) / 1_000_000
            if time > now:
                continue
            limited = bool(int(result.group(3)))
            total += 1
            if limited:
                num_limited += 1

    print(num_limited, "out of", total, f"limited ({num_limited/total*100:.2f}%)")
if __name__ == '__main__':
    main()
