#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import ast
import json
import math
from collections import defaultdict

# Sample data as a string (replace with your actual data)
# Load the data into a DataFrame
df = pd.read_csv("../../early-hints-preconnect_experiment_data_2023_10_10.tsv", delim_whitespace=True)

d = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

# aggregate page load timings by client
for i in range(len(df)):
    for branch in ["eh-preconnect-enabled", "eh-disabled"]:
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
for branch in ["eh-preconnect-enabled", "eh-disabled"]:
    for metric in ["first_contentful_paint", "page_load_time"]:
        for client in d[branch][metric].values():
            s = sum(client.values())
            for ms, num in client.items():
                d2[branch][metric][ms] += num / s

# print out the result
print(json.dumps(d2))
