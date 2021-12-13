#!/usr/bin/env python3

from pyquery import PyQuery as pq
from glob import glob
from pathlib import Path
import json
import re

def normalize_name(name):
    m = {
        "_": " ",
        "-": " ",
        "cmv12000": "CMV12000",
        "axiom": "AXIOM",
        "cmv12k": "CMV12000",
        "sd": "SD",
        "pmod": "PMOD",
    }
    name = name.replace("_", " ")
    name = name.replace("-", "_")
    for f, to in m.items():
        name = name.replace(f, to)
    return " ".join(part[0].upper() + part[1:] for part in name.split())

def read_copyright_license(name):
    copy = 'SPDX-FileCopyrightText: '
    lic = 'SPDX-License-Identifier: '
    copyright = []
    for line in Path(str(name) + ".license").read_text().splitlines():
        line = line.strip()
        if line.startswith(copy):
            copyright.append(line.removeprefix(copy))
        elif line.startswith(lic):
            license = line.removeprefix(lic)
    return copyright, license


infos = []
for sch in sorted(glob("boards/*.sch")):
    sch = Path(sch)
    base = sch.name
    m = re.search(r"(.*)[_-](v[\.\d]*[a-z]?([_-]r[\.\d]*[a-z]?)?)([_-]([^0-9]*))?.sch", base)

    if m is not None:
        name = m.group(1)
        version = m.group(2)[1:].replace('_', ' ').replace('-', ' ')
        tag = m.group(5)
    else:
        name = base.removesuffix(".sch")
        version = None
        tag = None
    name = normalize_name(name)

    variants = ["default"]
    d = pq(sch.read_bytes())
    variants += [v.attr("name") for v in d("variantdef").items()]

    info = {
        "name": name,
        "version": version,
        "tag": tag,
        "base": base.removesuffix(".sch"),
        "variants": variants
    }

    brd = sch.with_suffix(".brd")
    sch_copy, sch_lic = read_copyright_license(sch)
    brd_copy, brd_lic = read_copyright_license(brd)
    eagle6 = 'eagle version="6' in Path(brd).read_text()
    info["sch"] = {
        "license": sch_lic,
        "copyright": sch_copy
    }
    info["brd"] = {
        "license": brd_lic,
        "copyright": brd_copy
    }
    info["eagle_version"] = 6 if eagle6 else 7
    infos.append(info)

Path("info.json").write_text(json.dumps(infos, sort_keys=True))
