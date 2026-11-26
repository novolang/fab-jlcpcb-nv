"""Makes the dry-run kits of the calibration boards.

For each board number: writes the KiCad project with `calib_board.py`,
copies the saved part pages, runs the program that makes the order
package (the example of the package's README, built as an executable,
which runs the gates of `hardware-gates-nv` and then `fjpack.prepare`),
and writes the kit: the files to upload, a README that says what to do at
JLCPCB's order form, and a `results.md` with a table of every part to be
read from the screenshots.

    python3 calib_kit.py --pages <saved part pages> --prepare <program> \
        --work <work directory> --out <kits directory> [--boards 1,2,3]

The part pages are the public pages `https://jlcpcb.com/partdetail/<number>`
saved as `<number>.html`.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

import calib_data as d

HERE = os.path.dirname(os.path.abspath(__file__))

UPLOAD = ["bom.csv", "cpl.csv", "corrections.txt", "order-sheet.md"]


def parse_corrections(text):
    """`corrections.txt` as a dictionary from designator to the board's rotation, the rotation written,
    the layer and the source in words."""
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z]+[0-9]+): rotation (-?[0-9.]+) -> (-?[0-9.]+), (Top|Bottom): (.*)$", line)
        if not m:
            continue
        source = re.split(r"; (?:bottom side|position|field)", m.group(5))[0]
        out[m.group(1)] = {"board": m.group(2), "written": m.group(3), "layer": m.group(4), "source": source}
    return out


def family_words(source):
    """What the rotation of a part came from, short, for a table."""
    if source.startswith("family row "):
        return "row " + source.split(" ")[2]
    if source.startswith("verified part"):
        return "part entry (verified on this side)"
    if source.startswith("proposed part"):
        return "part entry (proposed)"
    if source.startswith("part "):
        return "part entry (seen on the other side only)"
    if source.startswith("the board's own value"):
        return "no row"
    if source.startswith("rotation field"):
        return "rotation field"
    return source


def library_of(html):
    """Basic, Extended or Preferred, from a saved part page; the empty string when the page names none."""
    m = re.search(r"detail-info-badge[^>]*>(Basic|Extended|Preferred)<", html)
    return m.group(1) if m else ""


def assembly_of(html):
    """The assembly class a saved part page names, `Economic and Standard` or `Standard Only`."""
    m = re.search(r"PCBA Type</dt><dd[^>]*><div[^>]*><span[^>]*>([^<]*)</span>", html)
    return m.group(1) if m else ""


def families(parts, corr):
    """The sources of the rotations of a board, each with the cells that take it: the cells on both sides, on
    the top side only and on the bottom side only, in order of first use."""
    rows = {}
    for p in parts:
        seen = {}
        for side in ("top", "bottom"):
            c = corr.get(d.reference(side, p["cell"]))
            if c is not None:
                seen[side] = family_words(c["source"])
        for key in dict.fromkeys(seen.values()):
            sides = [x for x in seen if seen[x] == key]
            kind = "both" if len(sides) == 2 else sides[0]
            rows.setdefault(key, {"both": [], "top": [], "bottom": []})[kind].append(p["cell"])
    return rows


def cells_words(cells):
    """Cell numbers as `01, 03`."""
    return ", ".join("%02d" % c for c in cells)


def results_md(number, parts, corr):
    """The `results.md` of a kit: the table of parts to read from the screenshots, with the answers empty."""
    out = ["# Results of calibration kit %d" % number, "",
           "Fill in the table from the screenshots of the order form's placement preview. Write `y` when the "
           "part is drawn right (the model's pin 1 mark on the silk triangle beside the footprint, or the "
           "model's polarity mark on the footprint's), `n` when it is not, and `-` when the form draws no model. "
           "For an `n`, write the rotation that draws it right in the last column.", "",
           "| Reference | Part number | Footprint | Family row | Rotation written | Drawn right? y/n | Rotation that draws it right |",
           "| --- | --- | --- | --- | --- | --- | --- |"]
    for p in parts:
        for side in ("top", "bottom"):
            ref = d.reference(side, p["cell"])
            c = corr.get(ref, {"written": "?", "source": "?"})
            out.append("| %s | %s | %s | %s | %s | | |" % (ref, p["part"], d.footprint_name(p["footprint"]),
                                                          family_words(c["source"]), c["written"]))
    out += ["", "Anything else that looked wrong (reference, how):", "", "## The assembly page", "",
            "What the form detected (size, layers):",
            "Layout the form filed the board under, PCBA Type offered, Assembly Side offered:",
            "Size the form made the board, and any edge rails:",
            "Every message of Process BOM&CPL, and the header counts of the parts page:",
            "Lines whose part number differs from `bom.csv`:", "", "## The quote page (read only)", "",
            "Price lines:", "Lead times:", "", "## Stopped", "",
            "I did not press Save to cart or Secure Checkout: yes / no",
            "A cart item appeared by itself: yes / no   I removed it: yes / no", ""]
    return "\n".join(out)


def readme_md(number, parts, corr, pages, size, counts):
    """The README of a kit."""
    name = "calib-%d" % number
    n = len(parts)
    unconfirmed = [p for p in parts if p["status"] == "unconfirmed"]
    fams = families(parts, corr)
    lines = [
        "# Calibration kit %d: %s" % (number, d.TITLES[number]), "",
        "This kit is for one session at JLCPCB's web order form. You upload the files, take the screenshots "
        "listed below, write what you see into `results.md`, and stop before the cart. Nothing is ordered and "
        "nothing is paid.", "",
        "One screenshot of the form's placement preview checks many rows of the rotation tables at once: the "
        "board holds %d parts, each placed once on the top side (`T01` to `T%02d`) and once on the bottom side "
        "(`B01` to `B%02d`) at the same place, laid out on a grid. The same cell number is the same part. The "
        "reference, the part number and the footprint's name are written on the silkscreen of each cell, and a "
        "white triangle on the silk points at pin 1 of the footprint." % (n, n, n), "",
        "The board is a test board, not a design: the parts carry no nets, the tracks do not exist, and the "
        "ignored rules of `gates.toml` are the ones that no-net pads of one footprint trip. It is written by "
        "`tools/calib` of `fab-jlcpcb-nv` from the footprints of KiCad 10.0.8's library, and the order package by "
        "`hardware-gates-nv` and `fab-jlcpcb-nv`. The board is %s by %s mm with 2 copper layers and 1.6 mm "
        "thickness." % (fmt(size[0]), fmt(size[1])), "",
        "**Assumptions, not confirmed on the form:** the board is at least 70 mm on each side, which is the least "
        "of the Standard class (70 by 70 mm), so the form is expected to keep the board at its own size with no "
        "edge rails. The parts are on both sides, and the form greyed out Assembly Side Both Sides under Economic "
        "on 2026-11-26, so PCBA Type is Standard. Write down what the form says about the size and the type.", "",
        "## Files", "",
        "| File | Goes to |", "| --- | --- |",
        "| `%s-rev-A-gerbers.zip` | step 1: the Gerber upload |" % name,
        "| `bom.csv` | step 3: %d lines, %d parts |" % (counts["bom"], 2 * n),
        "| `cpl.csv` | step 3: %d rows, %d `Top` and %d `Bottom`, millimetres, relative to the board's auxiliary origin |"
        % (2 * n, n, n),
        "| `order-sheet.md`, `corrections.txt` | for you: the rotation written for every part and where it came from |",
        "| `results.md` | the answers |",
        "| `%s.kicad_pcb` | the board, to open in KiCad |" % name, "",
        "## Steps", "",
        "Mark each box when done. \"Write down\" means a line in `results.md`.", "",
        "### 1. Start and the board", "",
        "- [ ] Open https://jlcpcb.com/ and press Instant Quote. Upload the Gerber zip. Write down what the form "
        "**detected**: size and layers. Our sheet says **%s by %s mm, 2 layers**." % (fmt(size[0]), fmt(size[1])),
        "- [ ] Set layers **2**, thickness **1.6 mm**, quantity **5**. Write down every warning about the board and the "
        "surface finish the form has preselected. Do not change options to make a warning go away.", "",
        "### 2. The assembly", "",
        "- [ ] Switch **PCB Assembly** on. Choose Assembly Side **Both Sides**, PCBA Type **Standard**, PCBA Qty **5**; leave the "
        "other options. Write down what the form offers and what it greys out, and whether it changes the board's size "
        "or adds edge rails.",
        "- [ ] Confirm, then NEXT.", "",
        "### 3. The bill and the placement file", "",
        "- [ ] Upload `bom.csv` and `cpl.csv`, press **Process BOM&CPL**. Write down every message and the counts of the "
        "header (parts detected, confirmed, inventory shortage, not selected). A part with no stock cannot be drawn; "
        "write its reference down.",
        "- [ ] Write down every line whose part number is not the one in `bom.csv`. No window should open; write down any "
        "that does. NEXT.", "",
        "### 4. The placements: the screenshots", "",
        "The preview shows one side at a time. Take, for the **top** side and again for the **bottom** side:", "",
        "- [ ] the whole board;",
        "- [ ] a zoom on each quadrant (upper left, upper right, lower left, lower right), close enough that the "
        "model's pin 1 mark and the white triangle beside it are both visible.", "",
        "That is 10 screenshots. For a part drawn wrong, select it and try the rotations in the box beside it; write "
        "down the one that draws it right. Note that the model of a symmetric part (a resistor, a capacitor) shows a "
        "quarter-turn error and does not show a half-turn error; the white triangle is the reference for pin 1 of "
        "the footprint, and a two-pad part has pin 1 at the triangle's end.", "",
        "### 5. Stop", "",
        "You are on the Quote & Order page. Write down the price lines and the lead times. **Do not press \"Save to "
        "cart\"** and do not press \"Secure Checkout\". If a cart item appears by itself, remove it and write that "
        "down. Close the tab.", "",
        "## What the rotation of each part came from", "",
        "`corrections.txt` names the source of each rotation. For this board the rows of the family table and the "
        "part entries are:", "", "| Source | Parts |", "| --- | --- |"]
    for k, cells in fams.items():
        said = []
        if cells["both"]:
            said.append("cells %s on both sides" % cells_words(cells["both"]))
        if cells["top"]:
            said.append("cells %s on the top side only" % cells_words(cells["top"]))
        if cells["bottom"]:
            said.append("cells %s on the bottom side only" % cells_words(cells["bottom"]))
        lines.append("| %s | %s |" % (k, "; ".join(said)))
    lines += ["", "## The parts", "",
              "Part numbers are those of JLCPCB's public part pages, read on 2026-11-26; the page gives the library "
              "and the assembly class. A part number is **confirmed** when its page names a manufacturer part and a "
              "package that fit the footprint, and **unconfirmed** when it does not, with the reason below.", "",
              "| Cell | Part number | Library | Part | Footprint | Status |", "| --- | --- | --- | --- | --- | --- |"]
    for p in parts:
        html = pages.get(p["part"], "")
        lib = library_of(html) or "?"
        if assembly_of(html) == "Standard Only":
            lib += ", Standard only"
        lines.append("| %02d | %s | %s | %s | %s | %s |" % (p["cell"], p["part"], lib, p["value"],
                                                       d.footprint_name(p["footprint"]), p["status"]))
    notes = [p for p in parts if p["note"]]
    if notes:
        lines += ["", "Notes on the parts:", ""]
        for p in notes:
            lines.append("- `%s` (cell %02d, %s): %s" % (p["part"], p["cell"], p["status"], p["note"]))
    if unconfirmed:
        lines += ["", "**Unconfirmed part numbers on this board:** " + ", ".join(
            "`%s` (cell %02d)" % (p["part"], p["cell"]) for p in unconfirmed) +
            ". A wrong picture for these may be a wrong part for the footprint, not a wrong rotation."]
    else:
        lines += ["", "No part number of this board is unconfirmed."]
    lines += ["", "## Where to stop", "",
              "You stop at the **Quote & Order** page. You may read the price there. **Do not press \"Save to cart\"** and **do "
              "not press \"Secure Checkout\"** or anything about payment.", ""]
    return "\n".join(lines)


def fmt(v):
    return ("%g" % v)


def run(cmd, **kw):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write(r.stdout)
        raise SystemExit("failed: " + " ".join(cmd))
    return r.stdout


def make(number, args, parts_all):
    parts = d.of_board(parts_all, number)
    name = "calib-%d" % number
    work = os.path.join(args.work, name)
    hw = os.path.join(work, "hardware")
    if os.path.isdir(hw):
        shutil.rmtree(hw)
    run(args.kicad.split() + [os.path.join(HERE, "calib_board.py"), args.library_dir, str(number), work])
    os.makedirs(os.path.join(hw, "parts"), exist_ok=True)
    pages = {}
    for p in parts:
        src = os.path.join(args.pages, p["part"] + ".html")
        shutil.copy(src, os.path.join(hw, "parts", p["part"] + ".html"))
        with open(src, errors="replace") as f:
            pages[p["part"]] = f.read()
    log = run([args.prepare, work, "rev-A", name, str(args.qty)])
    pack = os.path.join(hw, "fab", "rev-A", "jlcpcb")
    kit = os.path.join(args.out, name)
    os.makedirs(kit, exist_ok=True)
    for f in UPLOAD + ["%s-rev-A-gerbers.zip" % name]:
        shutil.copy(os.path.join(pack, f), os.path.join(kit, f))
    shutil.copy(os.path.join(hw, "gates.toml"), os.path.join(kit, "gates.toml"))
    shutil.copy(os.path.join(hw, name + ".kicad_pcb"), os.path.join(kit, name + ".kicad_pcb"))
    with open(os.path.join(pack, "corrections.txt")) as f:
        corr = parse_corrections(f.read())
    with open(os.path.join(pack, "bom.csv")) as f:
        bom_lines = len(f.read().strip().splitlines()) - 1
    with open(os.path.join(kit, "results.md"), "w") as f:
        f.write(results_md(number, parts, corr))
    with open(os.path.join(kit, "README.md"), "w") as f:
        f.write(readme_md(number, parts, corr, pages, d.board_size(len(parts)), {"bom": bom_lines}))
    with open(os.path.join(kit, "package.log"), "w") as f:
        f.write(log)
    print(name, "ok")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", required=True)
    ap.add_argument("--prepare", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boards", default="")
    ap.add_argument("--qty", type=int, default=5)
    ap.add_argument("--library-dir", default="/app/extensions/Library/footprints")
    ap.add_argument("--kicad", default="flatpak run --command=python3 org.kicad.KiCad")
    args = ap.parse_args(argv)
    parts = d.read_parts(os.path.join(HERE, "parts.csv"))
    faults = d.check_parts(parts)
    if faults:
        raise SystemExit("\n".join(faults))
    wanted = [int(x) for x in args.boards.split(",") if x] or d.boards(parts)
    for b in wanted:
        make(b, args, parts)


if __name__ == "__main__":
    main(sys.argv[1:])
