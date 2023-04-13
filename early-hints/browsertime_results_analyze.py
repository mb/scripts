#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-04-13

import matplotlib.pyplot as plt
import numpy as np
import json

def main():
    chrome_3gfast = json.loads(open("chrome_3gfast.json").read())
    data = [chrome_3gfast['fcp']['false'], chrome_3gfast['fcp']['true']]

    fig, ax1 = plt.subplots(figsize=(2, 6))

    bp = ax1.boxplot(data, notch=False)

    plt.show()

if __name__ == '__main__':
    main()

