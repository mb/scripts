#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-10-11

import matplotlib.pyplot as plt
import json
from itertools import accumulate # https://stackoverflow.com/a/30677070
from collections import defaultdict

def linear_interpolation(p, xs, ys):
    # index of first y value bigger than p
    idx = 0
    for (i, y) in enumerate(ys):
        if y > p:
            idx = i-1
            break

    x1 = xs[idx]
    x2 = xs[idx+1]
    y1 = ys[idx]
    y2 = ys[idx+1]
    inverse_m = (x2-x1) / (y2-y1)
    return x1 + inverse_m * (p - y1)

def main():
    inp = json.load(open("2023-10-10_agg_data.json"))
    inp = json.load(open("2023-10-11_agg_data_norm.json"))
    fig, axs = plt.subplots(2, 2)
    fig.suptitle("Early Hints Preconnect experiment")
    for i, metric in enumerate(["first_contentful_paint", "page_load_time"]):
        ps = [.01, .05, .25, .5, .75, .95, .99]
        pcts = defaultdict(lambda: list())
        ps2 = [i / 100 for i in range(1, 100)]
        pcts2 = defaultdict(lambda: list())
        for branch in ["eh-preconnect-enabled", "eh-disabled"]:
            data = inp[branch][metric]
            hist_x = list(data)
            hist_x = [int(x) for x in hist_x]
            hist_x.sort()
            hist_y = [data[str(x)] for x in hist_x]

            cumulative_y = list(accumulate(hist_y))

            # normalized
            max_cum_y = max(cumulative_y)
            norm_cum_y = [y / max_cum_y for y in cumulative_y]
            norm_y = [y / max_cum_y for y in hist_y]

            # calculate interpolated percentiles
            for p in ps:
                pcts[branch].append(linear_interpolation(p, hist_x, norm_cum_y))
            for p in ps2:
                pcts2[branch].append(linear_interpolation(p, hist_x, norm_cum_y))

            axs[0][i].plot(hist_x, hist_y, label=branch)
            axs[0][i].set_title(f"{metric} pdf")
            #axs[0][i].plot(hist_x, cumulative_y, title="", label=branch)

            #axs[1][i].plot(hist_x, norm_y, label=branch)
            axs[1][i].plot(hist_x, norm_cum_y, label=branch)
            axs[1][i].set_title(f"{metric} cdf")
        print(f"{metric}: load time increase by enabling early hints (negative numbers are good for early hints)")
        for (i, p) in enumerate(ps):
            old = pcts["eh-disabled"][i]
            new = pcts["eh-preconnect-enabled"][i]
            # https://stackoverflow.com/a/28404036
            print(f"{p}: {(new - old) / old * 100:.2f}%")
        increase = []
        for (i, p) in enumerate(ps):
            old = pcts["eh-disabled"][i]
            new = pcts["eh-preconnect-enabled"][i]
            # https://stackoverflow.com/a/28404036
            increase.append((new - old) / old * 100)
        average = sum(increase) / len(increase)
        print(f"average: {average:.2f}%")
    for ax in axs:
        for a in ax:
            a.legend()
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()

