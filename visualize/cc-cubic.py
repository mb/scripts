#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-09-28

# Visualizing the congestion window from manually logging in neqo

import matplotlib.pyplot as plt
import numpy as np
import re

cwnd_increase_pattern = r'CUBIC bytes_for_cwnd_increase\(curr_cwnd: (\d+), new_acked_bytes: (\d+), min_rtt: ([\d.]+)ms, now: Instant { tv_sec: (\d+), tv_nsec: (\d+) }\) -> ([\d.]+) \(Cubic { last_max_cwnd: ([\d.]+), estimated_tcp_cwnd: ([\d.]+), k: ([\d.]+), w_max: ([\d.]+), ca_epoch_start: Some\(Instant { tv_sec: (\d+), tv_nsec: (\d+) }\), tcp_acked_bytes: ([\d.e-]+) }\)'

def main():
    acked_bytes = 0
    start_time = None
    time = 0.0
    reduce_cwnd = []
    increase_cwnd_x = []
    increase_cwnd_y = {
        'curr_cwnd': [],
        'new_acked_bytes': [],
        'min_rtt': [],
        'result_value': [],
        'last_max_cwnd': [],
        'k_value': [],
        'w_max': [],
        'epoch_start': [],
        'estimated_tcp_cwnd': [],
        'tcp_acked_bytes': [],
    }


    #for line in open('tmp-h3-5.txt'):
    for line in open('tmp-h3-8.txt'):
        if not line.startswith('CUBIC'):
            continue
        if line.startswith('CUBIC bytes_for_cwnd_increase'):
            match = re.match(cwnd_increase_pattern, line.strip())
            now = int(match.group(4)) + (int(match.group(5)) / 1e9)
            if start_time is None:
                start_time = now
            time = now - start_time
            increase_cwnd_x.append(time)
            increase_cwnd_y['curr_cwnd'].append(int(match.group(1)))
            increase_cwnd_y['new_acked_bytes'].append(int(match.group(2)))
            increase_cwnd_y['min_rtt'].append(float(match.group(3)))
            increase_cwnd_y['result_value'].append(float(match.group(6)))
            increase_cwnd_y['last_max_cwnd'].append(float(match.group(7)))
            increase_cwnd_y['estimated_tcp_cwnd'].append(float(match.group(8)))
            increase_cwnd_y['k_value'].append(float(match.group(9)))
            increase_cwnd_y['w_max'].append(float(match.group(10)))
            epoch_start = int(match.group(11)) + (int(match.group(12)) / 1e9) - start_time
            increase_cwnd_y['epoch_start'].append(epoch_start)
            increase_cwnd_y['tcp_acked_bytes'].append(float(match.group(13)))
    
    # Plot cwnd increase over time
    plt.figure(figsize=(10, 6))
    #plt.plot(increase_cwnd_x, increase_cwnd_y['tcp_acked_bytes'], label='Acked bytes')
    plt.plot(increase_cwnd_x, increase_cwnd_y['w_max'], label='w_max - window size just after the reduction')
    plt.plot(increase_cwnd_x, increase_cwnd_y['curr_cwnd'], label='Current cwnd')
    plt.plot(increase_cwnd_x, increase_cwnd_y['last_max_cwnd'], label='Last Max cwnd')
    plt.plot(increase_cwnd_x, increase_cwnd_y['estimated_tcp_cwnd'], label='estimated tcp cwnd')
    plt.xlabel('Time (seconds)')
    plt.ylabel('cwnd')
    plt.legend()
    plt.title('Cubic Congestion Window (cwnd) Over Time')
    plt.grid(True)

    # Show the plot
    plt.show()

if __name__ == '__main__':
    main()
