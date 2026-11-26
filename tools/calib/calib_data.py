"""The part table and the grid of the calibration boards.

This module has no dependency outside the standard library, so that its
logic is tested without KiCad (tests/calib_test.py).  `calib_board.py`
turns what it computes into KiCad files.
"""

import csv
import re

# The grid: six columns of cells, each cell PITCH_X by PITCH_Y millimetres,
# inside a margin of MARGIN millimetres.  A board is at least MIN_SIDE
# millimetres on each side.
COLUMNS = 6
PITCH_X = 24.0
PITCH_Y = 24.0
MARGIN = 14.0
MIN_SIDE = 70.0

# The most parts a board holds on one side.
MAX_PER_SIDE = 30

# The longest line of the footprint name written on the silk, in characters.
LABEL_WIDTH = 24

STATUSES = ("confirmed", "unconfirmed")

# What each board holds, in a phrase.
TITLES = {
    1: "integrated circuits: the package families that have a row in the rotation table, and a few that have none",
    2: "transistors, diodes, resistors, capacitors and inductors, most of them with no row in the rotation table",
    3: "connectors, a switch, crystals and LEDs",
}


def read_parts(path):
    """The rows of the part table as dictionaries; `board` and `cell` are integers."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["board"] = int(r["board"])
        r["cell"] = int(r["cell"])
    return rows


def boards(parts):
    """The board numbers of the table, in order."""
    return sorted({p["board"] for p in parts})


def of_board(parts, board):
    """The rows of one board, in cell order."""
    return sorted((p for p in parts if p["board"] == board), key=lambda p: p["cell"])


def rows_for(count):
    """The number of grid rows that `count` cells need."""
    return (count + COLUMNS - 1) // COLUMNS


def board_size(count):
    """The width and height of a board of `count` cells, in millimetres."""
    width = COLUMNS * PITCH_X + 2 * MARGIN
    height = rows_for(count) * PITCH_Y + 2 * MARGIN
    return (max(width, MIN_SIDE), max(height, MIN_SIDE))


def cell_centre(cell):
    """The centre of cell number `cell` (counting from 1), from the board's top left corner."""
    index = cell - 1
    col = index % COLUMNS
    row = index // COLUMNS
    return (MARGIN + PITCH_X * (col + 0.5), MARGIN + PITCH_Y * (row + 0.5))


def reference(side, cell):
    """The reference of the part of cell `cell` on a side: T07 on top, B07 on the bottom."""
    return "%s%02d" % ("T" if side == "top" else "B", cell)


def footprint_name(footprint):
    """The name of a footprint without its library."""
    return footprint.split(":", 1)[1]


def label_lines(footprint):
    """The footprint's name broken after an underscore into lines of at most LABEL_WIDTH characters."""
    pieces = footprint_name(footprint).split("_")
    lines = []
    for piece in pieces:
        if lines and len(lines[-1]) + 1 + len(piece) <= LABEL_WIDTH:
            lines[-1] += "_" + piece
        else:
            lines.append(piece)
    return lines


def check_parts(parts):
    """The faults of the part table, as sentences; empty when it is sound."""
    faults = []
    seen = set()
    for p in parts:
        key = (p["board"], p["cell"])
        if key in seen:
            faults.append("board %d cell %d is used twice" % key)
        seen.add(key)
        if not re.fullmatch(r"C[0-9]+", p["part"]):
            faults.append("%s: the part number %r is not C and digits" % (reference("top", p["cell"]), p["part"]))
        if p["status"] not in STATUSES:
            faults.append("board %d cell %d: status %r" % (p["board"], p["cell"], p["status"]))
        if p["status"] == "unconfirmed" and not p["note"]:
            faults.append("board %d cell %d: an unconfirmed part has no note" % (p["board"], p["cell"]))
        if ":" not in p["footprint"]:
            faults.append("board %d cell %d: the footprint %r has no library" % (p["board"], p["cell"], p["footprint"]))
    for b in boards(parts):
        rows = of_board(parts, b)
        if len(rows) > MAX_PER_SIDE:
            faults.append("board %d holds %d parts on a side, at most %d" % (b, len(rows), MAX_PER_SIDE))
        if [r["cell"] for r in rows] != list(range(1, len(rows) + 1)):
            faults.append("board %d: the cells are not 1 to %d" % (b, len(rows)))
    return faults
