#!/usr/bin/env python3

from pyquery import PyQuery as pq
import re
import sys
from collections import defaultdict
from pathlib import Path
from glob import glob

def copying(filename):
    d = pq(filename.read_bytes())
    copying = d("text:contains('Copyright')").text().strip()
    copying += "\n" + d("text:contains('Licensed')").text().strip()
    return copying.strip()

def normalize_author(author):
    m = {
        "Herbert Pötzl": "Herbert Poetzl <herbert@13thfloor.at>",
        "Herbert Poetzl": "Herbert Poetzl <herbert@13thfloor.at>",
        "H.Poetzl": "Herbert Poetzl <herbert@13thfloor.at>",
        "H.Pötzl": "Herbert Poetzl <herbert@13thfloor.at>",
        "H. Pötzl": "Herbert Poetzl <herbert@13thfloor.at>",
    }
    if author in m:
        return m[author]
    else:
        print(f"unknown author: {author}")
        return author

def write_license_info(filename, info, info2):
    license_info_file = Path(str(filename) + ".license")
    if license_info_file.exists():
        return

    copyright_template = 'SPDX-FileCopyrightText: © '
    license_template = 'SPDX-License-Identifier: '
    info = info.replace("\n", " ")


    author_years = defaultdict(lambda: 9999)

    found = False
    print(info)
    for a in re.findall(r"\(C\)[ ]+(20\d\d)(-20\d\d)? (.*?)(Lic|$)", info):
        found = True
        year = int(a[0])
        author = normalize_author(a[2].strip())
        author_years[author] = min(author_years[author], year)
    if not found:
        print(f"no author for {filename}")
        exit(-1)

    license_info = ""

    for author, year in author_years.items():
        license_info += copyright_template + f"{year} {author}\n"

    for i in [info, info2]:
        if "CERN OHL v.1.2" in i or "CERN OHL v1.2" in i:
            license = "CERN-OHL-1.2"
            break
        elif "CERN OHL v.1.1" in i:
            license = "CERN-OHL-1.1"
            break
    else:
        print(f"{filename}: no license for: {info}")
        exit(-1)

    license_info += license_template + license + "\n"
    license_info_file.write_text(license_info)

for filename in glob("boards/*.sch"):
    print("analyzing", filename)
    filename = Path(filename).with_suffix(".brd")
    copy_brd = copying(filename)
    copy_sch = copying(filename.with_suffix(".sch"))

    if copy_brd == "" and copy_sch == "":
        raise Exception(f"Unknown license for {filename}")
    else:
        if copy_brd == "":
            copy_brd = copy_sch
        if copy_sch == "":
            copy_sch = copy_brd

        write_license_info(filename, copy_brd, copy_sch)
        write_license_info(filename.with_suffix(".sch"), copy_sch, copy_brd)
