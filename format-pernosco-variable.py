#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Author: Manuel Bucher <dev@manuelbucher.com>
# Date: 2025-02-26

import sys

def main():
    file = open(sys.argv[1]).read()
    out = ""
    whitespace = False
    is_escape_char = False
    is_str_literal = False
    indent = 0
    for c in file:
        # skip over string literals
        if is_str_literal:
            out += c
            if is_escape_char:
                is_escape_char = False
            elif c == '\\':
                is_escape_char = True
            elif c == '"':
                is_str_literal = False
            continue

        # normalize spaces
        if c.strip() == '':
            if whitespace == False:
                out += " "
                whitespace = True
            continue
        whitespace = False

        if c == '{':
            indent += 1
            whitespace = True
            out += '{\n' + '  ' * indent
            continue
        if c == '}':
            indent -= 1
            out += '\n' + '  ' * indent + '}'
            continue
        if c == ',':
            whitespace = True
            out += ',\n' + '  ' * indent
            continue
        if c == '"':
            is_str_literal = True
        out += c
    print(out)

if __name__ == '__main__':
    main()

