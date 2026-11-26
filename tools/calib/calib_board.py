"""Writes the KiCad project of one calibration board.

Run with the Python of KiCad, which has the module `pcbnew`:

    flatpak run --command=python3 org.kicad.KiCad calib_board.py \
        <footprint library directory> <board number> <output directory>

The footprint library directory holds the `<library>.pretty` directories of
KiCad's footprint library.  The output directory receives
`hardware/calib-<n>.kicad_pcb`, `.kicad_pro`, `.kicad_sch` and
`hardware/gates.toml`.  Every part of the table is placed once on the top
side, as `T<cell>`, and once on the bottom side, as `B<cell>`, at the same
place; the reference and the footprint's name are written on the silk next
to the part, and a triangle on the silk points at the part's pin 1.
"""

import math
import os
import sys
import uuid

import pcbnew

import calib_data as d

NS = uuid.UUID("5d6a8f0e-2f55-4c7e-9f0d-3c2f6a1b7e10")


def mm(v):
    return pcbnew.FromMM(v)


def point(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def add_text(board, text, x, y, layer, size=0.9, mirrored=False):
    """Text that starts at `x` and reads, as one looks at the side it is on, away from `x`: toward +x on
    top and toward -x on the bottom, where KiCad mirrors it."""
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(point(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(0.15))
    t.SetMirrored(mirrored)
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)
    return t


def add_line(board, x1, y1, x2, y2, layer, width=0.12):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(point(x1, y1))
    s.SetEnd(point(x2, y2))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    board.Add(s)


def add_triangle(board, tip, direction, layer, size=1.4):
    """A filled triangle of the silk whose tip is at `tip` (millimetres) and which points along `direction`."""
    dx, dy = direction
    px, py = -dy, dx
    bx, by = tip[0] - dx * size, tip[1] - dy * size
    pts = [point(*tip), point(bx + px * size * 0.5, by + py * size * 0.5),
           point(bx - px * size * 0.5, by - py * size * 0.5)]
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_POLY)
    s.SetPolyPoints(pts)
    s.SetFilled(True)
    s.SetLayer(layer)
    s.SetWidth(mm(0.1))
    board.Add(s)


def pin1_mark(board, fp, layer):
    """A silk triangle just outside pin 1 of `fp`, pointing at it."""
    pads = list(fp.Pads())
    one = [p for p in pads if p.GetNumber() == "1"] or pads[:1]
    cx = sum(p.GetPosition().x for p in pads) / len(pads)
    cy = sum(p.GetPosition().y for p in pads) / len(pads)
    p1 = one[0]
    vx = p1.GetPosition().x - cx
    vy = p1.GetPosition().y - cy
    norm = math.hypot(vx, vy)
    if norm < mm(0.01):
        vx, vy, norm = -1.0, 0.0, 1.0
    ux, uy = vx / norm, vy / norm
    half = max(p1.GetSizeX(), p1.GetSizeY()) / 2.0
    away = half + mm(0.45)
    tip = ((p1.GetPosition().x + ux * away) / 1e6, (p1.GetPosition().y + uy * away) / 1e6)
    add_triangle(board, tip, (-ux, -uy), layer)


def has_holes(fp):
    """Whether `fp` has a drilled pad."""
    return any(p.GetDrillSizeX() > 0 for p in fp.Pads())


def load_footprint(libdir, footprint):
    lib, name = footprint.split(":", 1)
    fp = pcbnew.FootprintLoad(os.path.join(libdir, lib + ".pretty"), name)
    if fp is None:
        raise SystemExit("footprint not found: " + footprint)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def sch_text(name, parts):
    """The schematic: one pinless symbol for each placed part, with the footprint and the LCSC field."""
    def u(*key):
        return str(uuid.uuid5(NS, "/".join(str(k) for k in key)))

    out = ['(kicad_sch', '\t(version 20250114)', '\t(generator "eeschema")', '\t(generator_version "9.0")',
           '\t(uuid "%s")' % u(name, "sheet"), '\t(paper "A1")', '\t(lib_symbols',
           '\t\t(symbol "calib:Part"', '\t\t\t(exclude_from_sim no)', '\t\t\t(in_bom yes)', '\t\t\t(on_board yes)',
           '\t\t\t(property "Reference" "U" (at 0 2 0) (effects (font (size 1.27 1.27))))',
           '\t\t\t(property "Value" "Part" (at 0 -2 0) (effects (font (size 1.27 1.27))))',
           '\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
           '\t\t\t(property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
           '\t\t\t(property "Description" "A part with no pins" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
           '\t\t\t(symbol "Part_0_1"',
           '\t\t\t\t(rectangle (start -4 -1) (end 4 1) (stroke (width 0.254) (type default)) (fill (type none)))',
           '\t\t\t)', '\t\t\t(embedded_fonts no)', '\t\t)', '\t)']
    n = 0
    for side in ("top", "bottom"):
        for p in parts:
            n += 1
            ref = d.reference(side, p["cell"])
            x = 30 + ((n - 1) % 8) * 60
            y = 30 + ((n - 1) // 8) * 20
            out += ['\t(symbol', '\t\t(lib_id "calib:Part")', '\t\t(at %d %d 0)' % (x, y), '\t\t(unit 1)',
                    '\t\t(exclude_from_sim no)', '\t\t(in_bom yes)', '\t\t(on_board yes)', '\t\t(dnp no)',
                    '\t\t(uuid "%s")' % u(name, "sym", ref),
                    '\t\t(property "Reference" "%s" (at %d %d 0) (effects (font (size 1.27 1.27))))' % (ref, x, y - 2),
                    '\t\t(property "Value" "%s" (at %d %d 0) (effects (font (size 1.27 1.27))))' % (p["value"], x, y + 2),
                    '\t\t(property "Footprint" "%s" (at %d %d 0) (effects (font (size 1.27 1.27)) (hide yes)))' % (p["footprint"], x, y),
                    '\t\t(property "Datasheet" "~" (at %d %d 0) (effects (font (size 1.27 1.27)) (hide yes)))' % (x, y),
                    '\t\t(property "LCSC" "%s" (at %d %d 0) (effects (font (size 1.27 1.27)) (hide yes)))' % (p["part"], x, y),
                    '\t\t(instances (project "%s" (path "/" (reference "%s") (unit 1))))' % (name, ref), '\t)']
    out += ['\t(sheet_instances (path "/" (page "1")))', '\t(embedded_fonts no)', ')']
    return "\n".join(out) + "\n"


PRO = """{
  "board": {"design_settings": {"rule_severities": {}}},
  "meta": {"filename": "%s.kicad_pro", "version": 3},
  "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
  "sheets": [["%s", "Root"]]
}
"""

GATES = """# The parts carry no net, so the checks that compare copper of different nets
# see conflicts between pads of one footprint (the pads of a QFN's exposed
# area, the two rows of a USB-C receptacle, the pads of a 0201) and between
# the pads of a top and a bottom shell pin.  The board is a calibration
# of the placement preview and is not made to work; it is not a judgment of
# the footprints.
[bom]
part_field = "LCSC"

[severity.drc]
clearance = "ignore"
solder_mask_bridge = "ignore"

# The symbol is one pinless symbol of a library that is not installed.
[severity.erc]
lib_symbol_issues = "ignore"
"""


def build(libdir, number, parts, outdir):
    name = "calib-%d" % number
    width, height = d.board_size(len(parts))
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    board.GetDesignSettings().SetBoardThickness(mm(1.6))
    x0, y0 = 20.0, 20.0

    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetStart(point(x0, y0))
    edge.SetEnd(point(x0 + width, y0 + height))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mm(0.1))
    board.Add(edge)

    for layer, mirrored, side in ((pcbnew.F_SilkS, False, "TOP"), (pcbnew.B_SilkS, True, "BOTTOM")):
        add_text(board, "%s: %s side, cells 1 to %d, T = top and B = bottom, the same cell is the same part"
                 % (name, side, len(parts)), x0 + width - 4 if mirrored else x0 + 4, y0 + 6, layer, size=1.0,
                 mirrored=mirrored)
        for c in range(d.COLUMNS + 1):
            gx = x0 + d.MARGIN + c * d.PITCH_X
            add_line(board, gx, y0 + d.MARGIN, gx, y0 + d.MARGIN + d.rows_for(len(parts)) * d.PITCH_Y, layer)
        for r in range(d.rows_for(len(parts)) + 1):
            gy = y0 + d.MARGIN + r * d.PITCH_Y
            add_line(board, x0 + d.MARGIN, gy, x0 + d.MARGIN + d.COLUMNS * d.PITCH_X, gy, layer)

    for p in parts:
        cx, cy = d.cell_centre(p["cell"])
        cx, cy = x0 + cx, y0 + cy
        for side in ("top", "bottom"):
            fp = load_footprint(libdir, p["footprint"])
            ref = d.reference(side, p["cell"])
            fp.SetReference(ref)
            fp.SetValue(p["value"])
            fp.SetField("LCSC", p["part"])
            fp.GetField("LCSC").SetVisible(False)
            fp.Reference().SetVisible(False)
            fp.Value().SetVisible(False)
            dx = 0.0
            if has_holes(fp):
                dx = (fp.GetBoundingBox(False).GetWidth() / 1e6 / 2.0 + 1.0) * (-1 if side == "top" else 1)
            fp.SetPosition(point(cx + dx, cy - 2.0))
            board.Add(fp)
            layer = pcbnew.F_SilkS
            if side == "bottom":
                fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
                layer = pcbnew.B_SilkS
            pin1_mark(board, fp, layer)
            mirrored = side == "bottom"
            near = cx + d.PITCH_X / 2 - 0.8 if mirrored else cx - d.PITCH_X / 2 + 0.8
            add_text(board, ref + " " + p["part"], near, cy - d.PITCH_Y / 2 + 1.2, layer, size=1.0, mirrored=mirrored)
            for i, line in enumerate(d.label_lines(p["footprint"])):
                add_text(board, line, near, cy + 6.4 + i * 1.1, layer, size=0.8, mirrored=mirrored)

    hw = os.path.join(outdir, "hardware")
    os.makedirs(hw, exist_ok=True)
    pcbnew.SaveBoard(os.path.join(hw, name + ".kicad_pcb"), board)
    with open(os.path.join(hw, name + ".kicad_sch"), "w") as f:
        f.write(sch_text(name, parts))
    with open(os.path.join(hw, name + ".kicad_pro"), "w") as f:
        f.write(PRO % (name, str(uuid.uuid5(NS, name + "/root"))))
    with open(os.path.join(hw, "gates.toml"), "w") as f:
        f.write(GATES)
    return name


def main(argv):
    libdir, number, outdir = argv[1], int(argv[2]), argv[3]
    here = os.path.dirname(os.path.abspath(__file__))
    parts = d.of_board(d.read_parts(os.path.join(here, "parts.csv")), number)
    if not parts:
        raise SystemExit("no part for board %d" % number)
    print(build(libdir, number, parts, outdir))


if __name__ == "__main__":
    main(sys.argv)
