#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Little script to gather the docstrings together nicely.
"""

from kernmagic import mymagics


def main():
    magics = []
    for name in mymagics.__all__:
        if not name.startswith('magic_'):
            continue
        realname = name.replace('magic_', '', 1)
        magics.append((realname, getattr(mymagics, name)))
    magics.sort()
    for i, (name, magic) in enumerate(magics):
        print magic.__doc__
        if i < len(magics)-1:
            print '-' * 80
            print


if __name__ == '__main__':
    main()

