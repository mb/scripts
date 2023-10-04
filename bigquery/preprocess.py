#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-06-30
# Bugzilla: https://bugzilla.mozilla.org/show_bug.cgi?id=1841626

# This script is used in combination with `experiment-data.sql`

import sys
import csv
import random
import json

# Define your custom dialect with doublequote=True
csv.register_dialect('mydialect', doublequote=True)

def prepare_histogram(inp):
    if inp == "":
        return
    inp = json.loads(inp)
    out = {key: inp["values"][key] for key in inp["values"] if inp["values"][key] != 0}
    if len(out) == 0:
        return
    return out

def main():
    with open(sys.argv[1], newline='') as f:
        reader = list(csv.reader(f, dialect='mydialect'))[1:]
    data = {}
    for row in reader:
        uuid, branch, response, page_load, fcp = row
        #if day < "2023-05-16" or day > "2023-06-08": # experiment 1 date range
        #if day < "2023-06-14" or day > "2023-07-04": # experiment 2 date range
        #if day < "2023-09-20" or day > "2023-10-17": # experiment 2 date range
            #continue
        if branch == "control":
            branch = "eh-disabled"
        elif branch == "treatment-a":
            branch = "eh-enabled"
        elif branch == "disabled":
            branch = "eh-disabled"
        elif branch == "preconnect-preload":
            branch = "eh-enabled"
        elif branch == "preload":
            branch = "eh-preload-enabled"
        #if day not in data:
            #data = {}
        if uuid not in data:
            data[uuid] = {}
        if branch not in data[uuid]:
            data[uuid][branch] = {}
        if response not in data[uuid][branch]:
            data[uuid][branch][response] = {'page_load': {}, 'fcp': {}}

        page_load = prepare_histogram(page_load)
        fcp = prepare_histogram(fcp)
        if page_load is not None:
            data[uuid][branch][response]['page_load'] = data[uuid][branch][response]['page_load'] | page_load
        if fcp is not None:
            data[uuid][branch][response]['fcp'] = data[uuid][branch][response]['fcp'] | fcp
    uuids = list(set([row[0] for row in reader]))
    random.shuffle(uuids)
    uuids = {uuid: i for (i, uuid) in enumerate(uuids)}
    maxi = len(uuids)
    ids = {v: k for k, v in uuids.items()}

    with open(sys.argv[2], 'w', newline='') as f:
        w = csv.writer(f, delimiter='\t', quotechar="\\")
        w.writerow(["date", "client_id", "experiment_branch", "eh_response_rel", "page_load_time_ms", "first_contentful_paint_ms"])
        for client in range(maxi):
            client_uuid = ids[client]
            if client_uuid in data:
                for branch in data[client_uuid]:
                    for response in data[client_uuid][branch]:
                        w.writerow([client, branch, response, json.dumps(data[client_uuid][branch][response]['page_load']), json.dumps(data[client_uuid][branch][response]['fcp'])])

if __name__ == '__main__':
    main()

