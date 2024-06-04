#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2024-06-04

# Goes through commit history of tor browser and organizes patches to be
# uplifted.

import subprocess
import yaml # pyyaml
from collections import defaultdict
import re

# dependency can be removed when using python 3.13: https://github.com/python/cpython/issues/73435
from wcmatch import pathlib 
#import pathlib

def parse_mots(filename):
    mots = yaml.safe_load(open(filename))
    modules = {}
    for module in mots["modules"]:
        if "includes" not in module or module["includes"] is None:
            # not needed for path -> bugzilla component resolution
            continue
        modules[module["name"]] = {
            "includes": module["includes"],
            "machine_name": module["machine_name"]
        }
        if "meta" in module and module["meta"] is not None and "components" in module["meta"]:
            modules[module["name"]]["bugzilla"] = module["meta"]["components"]
    return modules

MOTS = parse_mots("/home/user/dev/gecko/mots.yaml")

def append_components(filename, components):
    filename = pathlib.Path(filename)
    matches = []
    for component in MOTS:
        for pattern in MOTS[component]["includes"]:
            #print(filename, pattern)
            if filename.match(pattern, flags=pathlib.GLOBSTAR):
                components[component] += 1

def parse_commit(ref):
    p = subprocess.run(["git", "show", "--format=raw", ref], capture_output=True)
    out = p.stdout.decode()

    # Collect info about the commit
    info = {}
    files = {}
    components = defaultdict(int)
    section = 0
    commit_message = ""
    num_changes = 0
    for line in out.split('\n'):
        # There are three sections: header, commit message, changed lines
        if section < 2 and line == "":
            section += 1
            if section == 2:
                # apply some heuristics to stop on first non-tor commit
                if "Differential Revision: https://phabricator.services.mozilla.com/" in commit_message:
                    return None
                if "r=" in commit_message or "r?" in commit_message:
                    return None
                if "release+treescript@mozilla.org" in info["author"]:
                    return None
                if "CLOSED TREE" in commit_message:
                    return None
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
                append_components(filename, components)
                files[filename] = components

    # get bug information
    bugs = re.findall(r"Bug \d+", commit_message)

    return info["parent"]

def main():
    commit = "HEAD"
    while True:
        print("next_commit", commit)
        commit = parse_commit(commit)
        if commit is None:
            break

if __name__ == '__main__':
    main()

