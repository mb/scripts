#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2024-01-12

import pandas as pd
import json
from collections import defaultdict

# Sample data as a string (replace with your actual data)
# Load the data into a DataFrame
df = pd.read_csv("../../early-hints-preload_experiment_data_2024_01_12.tsv", delim_whitespace=True)

d = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

# aggregate page load timings by client
for i in range(len(df)):
    for branch in ["eh-preload-enabled", "eh-disabled"]:
        for metric in ["first_contentful_paint", "page_load_time"]:
            times = df.loc[i, metric]
            if type(times) != type(""):
                continue
            branch = df.loc[i, "experiment_branch"]
            client_id = df.loc[i, "client_id"]
            for ms, num in json.loads(times).items():
                ms = int(ms)
                if num != 0:
                    d[branch][metric][client_id][ms] += num

d2 = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

# normalize each clients page load timings
for branch in ["eh-preload-enabled", "eh-disabled"]:
    for metric in ["first_contentful_paint", "page_load_time"]:
        for client in d[branch][metric].values():
            s = sum(client.values())
            for ms, num in client.items():
                d2[branch][metric][ms] += num / s

# print out the result
print(json.dumps(d2))
