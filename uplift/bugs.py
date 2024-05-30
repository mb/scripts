#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: Manuel Bucher

# Goes through commit history of tor browser and organizes patches to be
# uplifted.

import subprocess
import yaml # pyyaml
import pathlib

def parse_mots(filename):
    mots = yaml.safe_load(open(filename))
    modules = {}
    for module in mots["modules"]:
        if "includes" not in module or module["includes"] is None:
            # not needed for path -> bugzilla component resolution
            continue
        modules[module["name"]] = {
            "includes": [pathlib.PurePath(f) for f in module["includes"]],
            "machine_name": module["machine_name"]
        }
        if "meta" in module and module["meta"] is not None and "components" in module["meta"]:
            modules[module["name"]]["bugzilla"] = module["meta"]["components"]
    return modules

MOTS = parse_mots("/home/user/dev/gecko/mots.yaml")

def get_components(filename):
    matches = []
    for component in MOTS:
        for pattern in MOTS[component]["includes"]:
            print(filename, pattern)
            if pattern.full_match(filename):
                print("match:", component)

def parse_commit(ref):
    p = subprocess.run(["git", "show", "--format=raw", ref], capture_output=True)
    out = p.stdout.decode()
    info = {}
    files = {}
    components = []
    section = 0
    commit_message = ""
    num_changes = 0
    for line in out.split('\n'):
        # There are three sections: header, commit message, changed lines
        if section < 2 and line.strip() == "":
            section += 1
            continue
        if section == 0:
            name, value = line.strip().split(" ", 1)
            info[name] = value
        elif section == 1:
            commit_message += line.strip() + "\n"
        else:
            # TODO: figure out potential bugzilla component
            num_changes += 1
            if line.startswith('diff --git a/'):
                filename = line.split(' ')[2]
                filename = filename[2:]
                components = get_components(filename)
                files[filename] = components

def main():
    parse_commit("HEAD")

if __name__ == '__main__':
    main()

