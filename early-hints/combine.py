#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# This script combines multiple videos into one side-by-side

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2023-08-09

import subprocess

def get_pos(letter, n):
    if n == 0:
        return "0"
    return "+".join([f"{letter}{i}" for i in range(n)])

def ffmpeg_combine(dir1, dir2):
    command = ["ffmpeg"]
    for i in range(20):
        command += ["-i", f"{dir1}/data/video/{i+1}.mp4"]
    for i in range(20):
        command += ["-i", f"{dir2}/data/video/{i+1}.mp4"]
    vids = "".join([f"[{i}:v]" for i in range(40)])
    vids += "xstack=inputs=40:"
    vids += "|".join([get_pos("w", i % 5) + "_" + get_pos("h", i // 5) for i in range(40)])
    command += [
            "-filter_complex",
            vids,
            "output.webm",
    ]
    subprocess.run(command)

def main():
    import argparse
    parser = argparse.ArgumentParser(prog = "combine multiple browsertime videos into one")
    parser.add_argument("dir1")
    parser.add_argument("dir2")
    args = parser.parse_args()
    ffmpeg_combine(args.dir1, args.dir2)

if __name__ == '__main__':
    main()
