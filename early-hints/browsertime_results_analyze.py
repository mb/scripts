#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-04-13

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.ticker import FormatStrFormatter
import matplotlib.ticker as plticker
import numpy as np
import json

try:
    import tikzplotlib
    OUTPUT_TEX = True
except:
    OUTPUT_TEX = False
    print("For .tex output run: pip install tikzplotlib")

CONNS = ['cable', '3g', '3gfast', '4g']
METRICS = ['fcp', 'lcp']

def to_dataframe(data):
    group = []
    for i in range(len(data[0])):
        if i < len(data[0]) / 2:
            group += ['control']
        else:
            group += ['early hints']
    print(len(group))
    df = pd.DataFrame({'Group': group,
                       'cable': data[0], '3g': data[1], '3gfast': data[2], '4g': data[3]})
    df = df[['Group', 'control', 'early hints']]
    dd = pd.melt(df, id_vars=['Group'], value_vars= ['control', 'early hints'])
    return dd


def get_data(browser):
    fcp, lcp = [], []
    for conn in CONNS:
        data = json.loads(open(browser + "_" + conn + ".json").read())
        fcp += [
                data['fcp']['false'],
                data['fcp']['true'],
        ]
        print(len(fcp[-1]))
        lcp += [
                data['lcp']['false'],
                data['lcp']['true'],
        ]
        print(len(lcp[-1]))
    return fcp, lcp

def improvements(data, i, j, percent):
    new = data[j][int(len(data[j]) * percent)]
    old = data[i][int(len(data[i]) * percent)]
    return (old - new) / new * 100

def bar_chart(data, diagram):
    # https://matplotlib.org/stable/gallery/lines_bars_and_markers/barchart.html
    fig, ax = plt.subplots(layout="constrained")
    plt.grid(axis = 'y', zorder=0)
    for arr in data:
        arr.sort()

    means = {
            'cable':  (improvements(data, 0, 1, 0.5), improvements(data, 0, 1, 0.75)),
            '3g':     (improvements(data, 2, 3, 0.5), improvements(data, 2, 3, 0.75)),
            '3gfast': (improvements(data, 4, 5, 0.5), improvements(data, 4, 5, 0.75)),
            '4g':     (improvements(data, 6, 7, 0.5), improvements(data, 6, 7, 0.75)),
    }
    x = np.arange(2)
    width = 0.20
    multiplier = 0
    color = ["#4285f4", "#ea4335", "#fbbc04", "#34a853"]
    label_color = ["white", "white", "black", "white"]
    for i, (attribute, measurement) in enumerate(means.items()):
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width*0.95, label=attribute, color=color[i], zorder = 3)
        ax.bar_label(rects, padding=-15, color=label_color[i], fmt=FormatStrFormatter('%.2f%%'))
        multiplier += 1

    if diagram == 'fcp':
        ax.set_title('First Contentful Paint - relative improvements')
    elif diagram == 'lcp':
        ax.set_title('Largest Contentful Paint - relative improvements')
    else:
        raise ValueError("Unsupported diagram")

    ax.set_xticks(x+width, ("p50", "p75"))
    ax.legend(loc='upper center', ncols=4)
    loc = plticker.MultipleLocator(base=5.0)
    ax.yaxis.set_major_locator(loc)
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f%%'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # add some text
    plt.savefig("relative-"+diagram+".png")
    plt.savefig("relative-"+diagram+".svg")
    plt.savefig("relative-"+diagram+".pgf")
    if OUTPUT_TEX:
        plt.savefig("relative-"+diagram+".tex")

# https://stackoverflow.com/a/16598291
def set_box_colors(bp):
    plt.setp(bp['boxes'][0], facecolor='white')
    plt.setp(bp['fliers'][0], marker='.', markeredgecolor='#00000050')
    plt.setp(bp['medians'][0], color='black')

    plt.setp(bp['boxes'][1], facecolor='darkorange')
    plt.setp(bp['medians'][1], color='black')
    plt.setp(bp['fliers'][1], marker='.', markeredgecolor='#00000050')


def generate_plot(browser, data, label):
    # https://matplotlib.org/stable/gallery/statistics/boxplot_demo.html
    fig, ax = plt.subplots()
    ax.set_facecolor("#ebebeb")

    bp = ax.boxplot(data[0:2], positions = [1, 2], widths = 0.9, patch_artist=True)
    set_box_colors(bp)

    bp = ax.boxplot(data[2:4], positions = [4, 5], widths = 0.9, patch_artist=True)
    set_box_colors(bp)

    bp = ax.boxplot(data[4:6], positions = [7, 8], widths = 0.9, patch_artist=True)
    set_box_colors(bp)

    bp = ax.boxplot(data[6:8], positions = [10, 11], widths = 0.9, patch_artist=True)
    set_box_colors(bp)
    plt.ylim(0)

    if label == "fcp":
        ax.set_title("First Contentful Paint")
    elif label == "lcp":
        ax.set_title("Largest Contentful Paint")
    else:
        raise ValueError("Unexpected title")

    plt.grid(color="white")
    ax.set_xticks(np.arange(4)*3+1.5, tuple(CONNS))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.legend([bp["boxes"][0], bp["boxes"][1]], ["control", "early hints"], loc='center right')
    plt.savefig("boxplot-"+label+".png")
    plt.savefig("boxplot-"+label+".pgf")
    plt.savefig("boxplot-"+label+".svg")
    if OUTPUT_TEX:
        plt.savefig("boxplot-"+label+".tex")

def main():
    browser = "chrome"
    fcp, lcp = get_data(browser)
    generate_plot(browser, fcp, "fcp")
    generate_plot(browser, lcp, "lcp")
    bar_chart(fcp, "fcp")
    bar_chart(lcp, "lcp")

if __name__ == '__main__':
    main()

