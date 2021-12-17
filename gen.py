#!/usr/bin/env python3

import configparser
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path
import copy
import json
import sys

from pyquery import PyQuery as pq

from gerber import load_layer
from gerber.render.theme import THEMES
from gerber.render.cairo_backend import GerberCairoContext

import pikepdf

from skimage import transform as i_transform
from skimage import io as i_io

def overlay(pdf_base_path, text, out):
    pdf_text = pikepdf.open(text)
    pdf_base = pikepdf.open(pdf_base_path)

    for text_page, base_page in zip(pdf_text.pages, pdf_base.pages):
        base_page_contents = base_page.Contents.read_bytes()

        text_page.Contents = pikepdf.Stream(pdf_text, b"q\n" + base_page_contents + b"Q\n" + strip_not_text(text_page))


    pdf_text.save(out)
    pdf_text.close()
    pdf_base.close()

def strip_not_text(page):
    stream = []

    # page.page_contents_coalesce()
    for operands, operator in pikepdf.parse_content_stream(page, ''):
        operator_as_string = str(operator)

        if (operator_as_string not in ["q", "Q", "cm", "BT", "ET", "gs"]) and (not operator_as_string.startswith('T')):
            pass
        else:
            stream.append((operands, operator))

    lines = []

    def convert(op):
        try:
            return op.unparse()
        except AttributeError:
            return str(op).encode('ascii')


    for operands, operator in stream:
        line = b' '.join(convert(op) for op in operands) + b' ' + operator.unparse()
        lines.append(line)

    return b"q\n3 Tr\n" + b'\n'.join(lines) + b"Q"

def get(config, name):
    val: str = config[name]
    val = val.removeprefix('"')
    val = val.removesuffix('"')
    return val

def to_inch(val: str):
    if val.endswith("mil"):
        return float(val[:-3]) * (1 / 1000.0)
    elif val.endswith("cm"):
        return float(val[:-2]) * (1 / 2.54)
    elif val.endswith("mm"):
        return float(val[:-2]) * (1 / 25.4)
    elif val.endswith("inch"):
        return float(val[:-4])

def gen_output(board, variant, config, eagle_version):
    layer_mappings = layer_mapping(board)
    if variant == "default":
        variant = ""
    output_name = str(Path(board).stem) + get(config, "Output")
    wheel_name = str(Path(board).stem) + get(config, "Wheel")
    device = get(config, 'Device')
    layers = [layer_mappings[layer] if layer in layer_mappings else layer for layer in get(config, 'Layers').split() if (layer in layer_mappings and layer_mappings[layer] is not None) or layer not in layer_mappings]

    enc_flags = get(config, 'Flags')
    default_flags = '0 0 0 1 0 1 1'.split()
    flag_keys = 'm r u c q O f'.split()
    flags = []
    for i, flag in enumerate(enc_flags.split()):
        if flag != default_flags[i]:
            flags.append(f"-{flag_keys[i]}{'+' if flag == '1' else '-'}")

    offset_x, offset_y = get(config, 'Offset').split()
    offset_x = to_inch(offset_x)
    offset_y = to_inch(offset_y)
    offset_x = ['-x', str(offset_x)]
    offset_y = ['-y', str(offset_y)]

    board_relative = Path(board).name
    surpress_prompts = ["-N+"]
    eagle_cmd = ["eagle", "-A", variant] + surpress_prompts + flags + ["-X", "-d", device] + ["-o", output_name] + ["-W", wheel_name] + offset_x + offset_y + [board_relative] + layers
    subprocess.check_call(eagle_cmd, cwd=Path(board).parent)
    return output_name

def gen_pdf(board, variant):
    out_base = f"{board}-{variant}"
    if Path(out_base + ".pdf").exists():
        return
    if variant == "default":
        variant = ""
    sch_file = board + ".sch"
    template = f"edit .sch; SET CONFIRM NO; VARIANT '{variant}'; PRINT - paper a3 landscape 1.0 sheets all -caption FILE {{}}; QUIT"
    sch = Path(sch_file).read_text()
    Path(sch_file).write_text(sch.replace('alwaysvectorfont="no"', 'alwaysvectorfont="yes"'))
    without_text = out_base + "_without_text.pdf"
    subprocess.check_call(["eagle", "-C", template.format(without_text), sch_file])
    Path(sch_file).write_text(sch.replace('alwaysvectorfont="yes"', 'alwaysvectorfont="no"'))
    with_text = out_base + "_with_text.pdf"
    subprocess.check_call(["eagle", "-C", template.format(with_text), sch_file])
    Path(sch_file).write_text(sch)
    overlay(pdf_base_path=out_base + "_without_text.pdf", text=out_base + "_with_text.pdf", out=out_base + ".pdf")
    Path(without_text).unlink()
    Path(with_text).unlink()

def preview_pngs(board):
    ctx = GerberCairoContext(scale=1200)
    stem = str(Path(board).with_suffix(""))
    top_full = stem + '_top.png'
    bottom_full = stem + '_bottom.png'
    top_preview = stem + '_top-preview.png'
    bottom_preview = stem + '_bottom-preview.png'

    if not (Path(top_full).exists() and Path(bottom_full).exists()):
        print("generating full res previews for", stem, Path(top_full).exists(), Path(bottom_full).exists())
        theme = THEMES['OSH Park']
        drill = load_layer(stem + '.drills.xln')

        top_copper = load_layer(stem + '.toplayer.ger')
        top_mask = load_layer(stem + '.topsoldermask.ger')
        top_silk = load_layer(stem + '.topsilkscreen.ger')
        ctx.render_layer(top_copper, settings=theme.top)
        ctx.render_layer(top_mask, settings=theme.topmask)
        ctx.render_layer(top_silk, settings=theme.topsilk)
        ctx.render_layer(drill, settings=theme.drill)
        ctx.dump(stem + '_top.png')


        bottom_drill = copy.copy(theme.drill)
        bottom_drill.mirror = True

        ctx.clear()
        bottom_copper = load_layer(stem + '.bottomlayer.ger')
        bottom_mask = load_layer(stem + '.bottomsoldermask.ger')
        bottom_silk = load_layer(stem + '.bottomsilkscreen.ger')
        ctx.render_layer(bottom_copper, settings=theme.bottom)
        ctx.render_layer(bottom_mask, settings=theme.bottommask)
        ctx.render_layer(bottom_silk, settings=theme.bottomsilk)
        ctx.render_layer(drill, settings=bottom_drill)
        ctx.dump(stem + '_bottom.png')

    print("generating previews for", stem)
    if not Path(top_preview).exists() or not Path(bottom_preview).exists():
        top = i_io.imread(top_full)
        bottom = i_io.imread(bottom_full)

        height, width, _ = top.shape
        if height > width * 1.5:
            top = i_transform.rotate(top, angle=-90, resize=True)
            bottom = i_transform.rotate(bottom, angle=-90, resize=True)
            height, width, _ = top.shape

        if width > 1.5 * height:
            factor = 1000 / width
        else:
            factor = 500 / width

        # TODO(robin): once we upgrade to skimage 0.19: multichannel=True -> channel_axis=-1
        top_p = i_transform.rescale(top, factor, anti_aliasing=True, multichannel=True)
        bottom_p = i_transform.rescale(bottom, factor, anti_aliasing=True, multichannel=True)
        i_io.imsave(top_preview, top_p)
        i_io.imsave(bottom_preview, bottom_p)


def board_file(board, variant):
    return f"boards/{board['base']}-{variant}.brd"

def layer_mapping(board_file):
    d = pq(Path(board_file).read_bytes())
    tsilk = d("[name='_tSilk']")("layer").attr("number")
    if tsilk is None:
        tsilk = d("[name='_tsilk']")("layer").attr("number")
    bsilk = d("[name='_bSilk']")("layer").attr("number")
    if bsilk is None:
        bsilk = d("[name='_bsilk']")("layer").attr("number")
    # assert tsilk is not None
    # assert bsilk is not None
    return {
        "53": tsilk,
        "54": bsilk
    }

def process(board):
    all_existing = all(Path(board_file(board, variant)).exists() for variant in board["variants"])
    force_recam = False
    if not all_existing:
        for variant in board["variants"]:
            Path(board_file(board, variant)).unlink(missing_ok=True)
        subprocess.check_call(["eagle", board['base'] + ".sch", "-C", "run ../gen-brd-variants.ulp; QUIT"], cwd="boards")
        force_recam = True

    for variant in board["variants"]:
        base = f"boards/{board['base']}-{variant}"
        print(f"processing {base}")
        base = f"boards/{board['base']}-{variant}"

        zipfile = base + ".zip"

        if not Path(zipfile).exists() or force_recam:
            with ZipFile(zipfile, "w", ZIP_DEFLATED) as gerber_zip:
                for section in config.sections():
                    section = config[section]
                    if "Device" in section:
                        out = gen_output(base + ".brd", variant, section, board["eagle_version"])
                        gerber_zip.write(Path("boards") / out, out)
        gen_pdf(f"boards/{board['base']}", variant)
        preview_pngs(f"boards/{board['base']}-{variant}.brd")



CAM_JOB = "oshpark-4layer.cam"
config = configparser.ConfigParser(strict=False)
config.read(CAM_JOB)

boards = json.loads(Path("info.json").read_text())[:20]

if len(sys.argv) == 3:
    shard = int(sys.argv[1])
    total = int(sys.argv[2])
    print(f"processing shard {shard} of {total}")
    per_shard = (len(boards) + total - 1) // total
    boards = boards[shard * per_shard:(shard + 1) * per_shard]

from multiprocessing import Pool
with Pool() as pool:
    # for board in boards:
    #     process(board)
    res = list(pool.imap_unordered(process, boards))
