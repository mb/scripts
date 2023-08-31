#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-07-06

import sys
import json
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

def init():
    # server response -> branch
    return {
            'preconnect': {},
            'preload': {},
            'preconnect_preload': {},
    }

def add_histogram(data, branch, rel, hist, bins):
    hist = json.loads(hist)
    if rel not in data:
        data[rel] = {}
    if branch not in data[rel]:
        data[rel][branch] = {}
    for val in hist:
        if int(val) == 0:
            continue
        if int(val) in data[rel][branch]:
            data[rel][branch][int(val)] += hist[val]
        else:
            data[rel][branch][int(val)] = hist[val]
            if int(val) not in bins:
                bins.append(int(val))

def count_num_loads(pgt, fcp):
    return max(sum(json.loads(pgt).values()), sum(json.loads(fcp).values()))

# https://stackoverflow.com/a/52921726
def fix_hist_step_vertical_line_at_end(ax):
    axpolygons = [poly for poly in ax.get_children() if isinstance(poly, mpl.patches.Polygon)]
    for poly in axpolygons:
        poly.set_xy(poly.get_xy()[:-1])

def get_rel():
    return {
            "v1": {
                "p50": {
                    "fcp": {
                    }
                },
                "p75": {
                }
            }
    }

import pandas as pd

def get_ps(item_dict : dict[int, int]) -> (int, int, int):
    print(item_dict)
    df = pd.DataFrame.from_dict(item_dict, orient='index').reset_index()
    df.columns = ['values', 'count']
    df.sort_values('values', inplace=True)
    df['cum_sum'] = df['count'].cumsum()
    total_count = df.iloc[-1, -1]
    print(df)
    p25, p50, p75 = (None, None, None)
    for id, row in df.iterrows():
        if row['cum_sum'] >= int(total_count*0.25) and p25 is None:
            p25 = row['values']
            print("p25", p25)
        if row['cum_sum'] >= int(total_count*0.5) and p50 is None:
            p50 = row['values']
            print("p50", p50)
        if row['cum_sum'] >= int(total_count*0.75) and p75 is None:
            p75 = row['values']
            print("p75", p75)
            return (p25, p50, p75)

def improvements(old, new):
    return (old - new) / new * 100


def bar_chart(data, diagram):
    print(data)
    if 'fcp' not in data['v1']:
        return
    # https://matplotlib.org/stable/gallery/lines_bars_and_markers/barchart.html
    fig, ax = plt.subplots(layout="constrained")
    plt.grid(axis = 'y', zorder=0)

    means = {
            'fcp-v1': (
                improvements(data['v1']['fcp']['eh-disabled'][0], data['v1']['fcp']['eh-enabled'][0]),
                improvements(data['v1']['fcp']['eh-disabled'][1], data['v1']['fcp']['eh-enabled'][1]),
                improvements(data['v1']['fcp']['eh-disabled'][2], data['v1']['fcp']['eh-enabled'][2]),
            ),
            'page-load-v1': (
                improvements(data['v1']['page_load_time']['eh-disabled'][0], data['v1']['page_load_time']['eh-enabled'][0]),
                improvements(data['v1']['page_load_time']['eh-disabled'][1], data['v1']['page_load_time']['eh-enabled'][1]),
                improvements(data['v1']['page_load_time']['eh-disabled'][2], data['v1']['page_load_time']['eh-enabled'][2]),
            ),
            'fcp-v2': (
                improvements(data['v2']['fcp']['eh-disabled'][0], data['v2']['fcp']['eh-enabled'][0]),
                improvements(data['v2']['fcp']['eh-disabled'][1], data['v2']['fcp']['eh-enabled'][1]),
                improvements(data['v2']['fcp']['eh-disabled'][2], data['v2']['fcp']['eh-enabled'][2]),
            ),
            'page-load-v2': (
                improvements(data['v2']['page_load_time']['eh-disabled'][0], data['v2']['page_load_time']['eh-enabled'][0]),
                improvements(data['v2']['page_load_time']['eh-disabled'][1], data['v2']['page_load_time']['eh-enabled'][1]),
                improvements(data['v2']['page_load_time']['eh-disabled'][2], data['v2']['page_load_time']['eh-enabled'][2]),
            ),
    }
    print(means)
    x = np.arange(3)
    width = 0.20
    multiplier = 0
    #color = ["#4285f4", "#ea4335", "#fbbc04", "#34a853"]
    #label_color = ["white", "white", "white"]
    for i, (attribute, measurement) in enumerate(means.items()):
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width*0.95, label=attribute, zorder = 3)
        ax.bar_label(rects, padding=-15, fmt=mpl.ticker.FormatStrFormatter('%.2f%%'))
        multiplier += 1

    if diagram == 'fcp':
        ax.set_title('First Contentful Paint - relative improvements')
    elif diagram == 'lcp':
        ax.set_title('Largest Contentful Paint - relative improvements')
    else:
        ax.set_title(diagram)

    ax.set_xticks(x+width, ("p25", "p50", "p75"))
    ax.legend(loc='upper center', ncols=4)
    loc = mpl.ticker.MultipleLocator(base=5.0)
    ax.yaxis.set_major_locator(loc)
    ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f%%'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # add some text
    plt.savefig("relative-"+diagram+".png")

def main():
    files = ["v1", "v2"]

    rel_imp = {}
    for file in files:
        pgt = init()
        fcp = init()
        first = True
        bins = []

        # count num_loads
        num_loads = 0
        loads_per_client = {}

        for line in open(f"processed-early-hints-performance-{file}.tsv"):
            if first:
                first = False
                continue
            date, client_id, experiment_branch, eh_response_rel, page_load_time_ms, first_contentful_paint_ms = line.split('\t')

            if experiment_branch == 'eh-disabled' and eh_response_rel.endswith('_1'):
                continue

            # generate meta data
            if client_id not in loads_per_client:
                loads_per_client[client_id] = 0
            n = count_num_loads(page_load_time_ms, first_contentful_paint_ms)
            num_loads += n
            loads_per_client[client_id] += n

            # generate cdf data
            bucket = eh_response_rel.rstrip('_0').rstrip('_1')
            # exclude _0, _1 distinction in eh-disabled
            add_histogram(pgt, experiment_branch, bucket, page_load_time_ms, bins)
            add_histogram(fcp, experiment_branch, bucket, first_contentful_paint_ms, bins)

            if (experiment_branch == 'eh-enabled' or experiment_branch == 'eh-preload-enabled') and '_' in eh_response_rel:
                add_histogram(pgt, eh_response_rel, experiment_branch + bucket, page_load_time_ms, bins)
                add_histogram(fcp, eh_response_rel, experiment_branch + bucket, first_contentful_paint_ms, bins)
        bins.sort()

        # user statistics
        lpc = list(loads_per_client.values())
        lpc.sort()
        print(file)
        print("num_clients:", len(loads_per_client))
        print("num_loads:", num_loads)
        print("loads_per_client:", num_loads / len(loads_per_client), "avg,", max(loads_per_client.values()), "max,", np.median(list(loads_per_client.values())), "median")
        fig, ax = plt.subplots()
        n, bins, patches = ax.hist(list(loads_per_client.values()), bins=max(loads_per_client.values()), density=True, cumulative=True, histtype='step', label="loads_per_client")
        ax.set_title(f'early-hints-performance-{file}\nloads per client\ncdf')
        ax.set_xscale('log')
        ax.set_xlabel('number of page loads')
        ax.set_ylabel('percentage of clients')
        ax.xaxis.set_major_formatter(mpl.ticker.ScalarFormatter())
        ax.ticklabel_format(style='sci', scilimits=(-6, 9))
        fix_hist_step_vertical_line_at_end(ax)
        plt.savefig(f"early-hints-performance-{file}_loads_per_client_cdf.png")
    
        # draw cdf diagrams
        for branch in pgt:
            for metric in [fcp, pgt]:
                fig, ax = plt.subplots()
                min_nonzero = 50000
                rels = list(pgt[branch].keys())
                rels.sort()
                metric_name = "fcp"
                if metric != fcp:
                    metric_name = "page_load_time"
                for rel in rels:
                    if rel == 'eh-preload-enabled':
                        continue
                    n, bins, patches = ax.hist(metric[branch][rel], bins=bins, density=True, cumulative=True, histtype='step', label=rel)
                    min_nonzero = min(min_nonzero, min(metric[branch][rel].keys()))
                    if rel in rel_imp.setdefault(branch, {}).setdefault(file, {}).setdefault(metric_name, {}):
                        a = hello
                    rel_imp.setdefault(branch, {}).setdefault(file, {}).setdefault(metric_name, {})[rel]= get_ps(metric[branch][rel])
                print(min_nonzero)
                ax.set_title(f"early-hints-performance-{file}\n{branch}\n{metric_name}")
                ax.legend()
                #ax.set_xscale('log')
                ax.set_xlabel('time in ms')
                ax.set_xlim(left=min_nonzero-1)
                # https://stackoverflow.com/a/61352317
                ax.xaxis.set_major_formatter(mpl.ticker.ScalarFormatter())
                ax.ticklabel_format(style='sci', scilimits=(-6, 9))
                fix_hist_step_vertical_line_at_end(ax)
                plt.savefig(f"early-hints-performance-{file}_{branch}_{metric_name}_cdf.png")
    for branch in rel_imp:
        print(branch)
        bar_chart(rel_imp[branch], branch)

if __name__ == '__main__':
    main()

