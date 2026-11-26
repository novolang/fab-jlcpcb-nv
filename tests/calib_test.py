"""Tests of the calibration boards' part table and grid (no KiCad needed).

Run:  python3 -I -m unittest discover -s tests -p 'calib_test.py'
from the package directory, with `tools/calib` on the path as below.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..", "tools", "calib")
sys.path.insert(0, TOOLS)

import calib_data as d  # noqa: E402
import calib_kit as k  # noqa: E402


class GridTests(unittest.TestCase):
    def test_a_board_is_at_least_70_mm_on_each_side(self):
        for count in (1, 11, 29, 30):
            w, h = d.board_size(count)
            self.assertGreaterEqual(w, 70.0)
            self.assertGreaterEqual(h, 70.0)

    def test_thirty_cells_are_five_rows_of_six(self):
        self.assertEqual(d.rows_for(30), 5)
        self.assertEqual(d.rows_for(31), 6)
        self.assertEqual(d.rows_for(1), 1)
        self.assertEqual(d.board_size(30), (172.0, 148.0))

    def test_cells_run_left_to_right_then_down(self):
        self.assertEqual(d.cell_centre(1), (26.0, 26.0))
        self.assertEqual(d.cell_centre(6), (146.0, 26.0))
        self.assertEqual(d.cell_centre(7), (26.0, 50.0))

    def test_the_last_cell_is_inside_the_board(self):
        for count in (11, 29, 30):
            w, h = d.board_size(count)
            x, y = d.cell_centre(count)
            self.assertLess(x + d.PITCH_X / 2, w)
            self.assertLess(y + d.PITCH_Y / 2, h)

    def test_references_pair_the_two_sides_by_cell(self):
        self.assertEqual(d.reference("top", 7), "T07")
        self.assertEqual(d.reference("bottom", 7), "B07")

    def test_a_footprint_name_is_broken_after_underscores_at_the_label_width(self):
        self.assertEqual(d.label_lines("L:R_0603_1608Metric"), ["R_0603_1608Metric"])
        lines = d.label_lines("L:QFN-40-1EP_5x5mm_P0.4mm_EP3.6x3.6mm")
        self.assertEqual("_".join(lines), "QFN-40-1EP_5x5mm_P0.4mm_EP3.6x3.6mm")
        self.assertEqual(lines, ["QFN-40-1EP_5x5mm_P0.4mm", "EP3.6x3.6mm"])
        self.assertTrue(all(len(x) <= d.LABEL_WIDTH for x in lines))
        # A piece longer than the width stays whole on a line of its own.
        self.assertEqual(d.label_lines("L:" + "x" * 30), ["x" * 30])


def row(board, cell, part="C1", status="confirmed", note="", footprint="L:F"):
    return {"board": board, "cell": cell, "footprint": footprint, "value": "v",
            "part": part, "status": status, "note": note}


class TableTests(unittest.TestCase):
    def test_the_table_of_the_package_is_sound(self):
        parts = d.read_parts(os.path.join(TOOLS, "parts.csv"))
        self.assertEqual(d.check_parts(parts), [])
        self.assertEqual(d.boards(parts), [1, 2, 3])

    def test_no_board_holds_more_than_thirty_parts_on_a_side(self):
        parts = d.read_parts(os.path.join(TOOLS, "parts.csv"))
        for b in d.boards(parts):
            self.assertLessEqual(len(d.of_board(parts, b)), 30)

    def test_every_unconfirmed_part_says_why(self):
        parts = d.read_parts(os.path.join(TOOLS, "parts.csv"))
        for p in parts:
            if p["status"] == "unconfirmed":
                self.assertTrue(p["note"], p["part"])

    def test_faults_are_named(self):
        faults = d.check_parts([row(1, 1), row(1, 1), row(1, 3, part="X1"), row(1, 4, status="maybe"),
                                row(1, 5, status="unconfirmed"), row(1, 6, footprint="nolib")])
        text = "\n".join(faults)
        self.assertIn("board 1 cell 1 is used twice", text)
        self.assertIn("not C and digits", text)
        self.assertIn("status 'maybe'", text)
        self.assertIn("an unconfirmed part has no note", text)
        self.assertIn("has no library", text)
        self.assertIn("the cells are not 1 to", text)

    def test_more_than_thirty_parts_is_a_fault(self):
        faults = d.check_parts([row(1, c) for c in range(1, 32)])
        self.assertIn("board 1 holds 31 parts on a side, at most 30", faults)


CORRECTIONS = """T01: rotation 0 -> 270, Top: family row ^LQFP- (adds 270; unverified)
T02: rotation 0 -> 0, Top: the board's own value (unverified)
B02: rotation 180 -> 180, Bottom: the board's own value (unverified); bottom side: rotation is 180 minus the board's
B01: rotation 180 -> 90, Bottom: part C1 (adds 90; seen right on top on 2026-11-26, not on this side; unverified); bottom side: rotation is 180 minus the board's; position is the pad centre, 1.46 mm from the anchor
T03: rotation 0 -> 90, Top: verified part C3 (adds 90; seen right on top on 2026-11-26)
2 row(s) have a verified part rotation, 0 a proposed one
"""

PARTS = [
    {"board": 1, "cell": 1, "footprint": "Package_QFP:LQFP-48_7x7mm_P0.5mm", "value": "MCU", "part": "C1",
     "status": "confirmed", "note": ""},
    {"board": 1, "cell": 2, "footprint": "Resistor_SMD:R_0603_1608Metric", "value": "10k", "part": "C2",
     "status": "unconfirmed", "note": "fit not compared"},
]


class KitTests(unittest.TestCase):
    def test_corrections_are_read_by_designator_with_the_source_cut_before_the_side_and_position_notes(self):
        c = k.parse_corrections(CORRECTIONS)
        self.assertEqual(sorted(c), ["B01", "B02", "T01", "T02", "T03"])
        self.assertEqual(c["T01"], {"board": "0", "written": "270", "layer": "Top",
                                    "source": "family row ^LQFP- (adds 270; unverified)"})
        self.assertEqual(c["B02"]["source"], "the board's own value (unverified)")
        self.assertEqual(c["B01"]["layer"], "Bottom")
        self.assertEqual(c["B01"]["source"],
                         "part C1 (adds 90; seen right on top on 2026-11-26, not on this side; unverified)")

    def test_a_source_is_named_by_its_row_or_its_kind(self):
        self.assertEqual(k.family_words("family row ^LQFP- (adds 270; unverified)"), "row ^LQFP-")
        self.assertEqual(k.family_words("verified part C3 (adds 90; x)"), "part entry (verified on this side)")
        self.assertEqual(k.family_words("proposed part C3 (adds 90; x)"), "part entry (proposed)")
        self.assertEqual(k.family_words("part C1 (adds 90; x)"), "part entry (seen on the other side only)")
        self.assertEqual(k.family_words("the board's own value (unverified)"), "no row")
        self.assertEqual(k.family_words("rotation field of the part (adds 90; unverified)"), "rotation field")
        self.assertEqual(k.family_words("something else"), "something else")

    def test_the_library_and_the_assembly_class_are_read_from_a_saved_part_page(self):
        page = ('<span class="detail-info-badge x">Extended</span>'
                '<dt>PCBA Type</dt><dd class="a"><div class="b"><span class="c">Standard Only</span></div></dd>')
        self.assertEqual(k.library_of(page), "Extended")
        self.assertEqual(k.assembly_of(page), "Standard Only")
        self.assertEqual(k.library_of("<html>"), "")
        self.assertEqual(k.assembly_of("<html>"), "")

    def test_the_results_table_has_a_row_for_every_part_on_both_sides_with_the_rotation_written(self):
        text = k.results_md(1, PARTS, k.parse_corrections(CORRECTIONS))
        self.assertIn("| T01 | C1 | LQFP-48_7x7mm_P0.5mm | row ^LQFP- | 270 | | |", text)
        self.assertIn("| B01 | C1 | LQFP-48_7x7mm_P0.5mm | part entry (seen on the other side only) | 90 | | |", text)
        self.assertIn("| T02 | C2 | R_0603_1608Metric | no row | 0 | | |", text)
        self.assertIn("| B02 | C2 | R_0603_1608Metric | no row | 180 | | |", text)
        self.assertIn("I did not press Save to cart or Secure Checkout: yes / no", text)
        # A reference the package did not write is shown with a question mark.
        self.assertIn("| ? |", k.results_md(1, [dict(PARTS[0], cell=9)], {}))

    def test_the_families_group_the_cells_by_source_and_by_side(self):
        f = k.families(PARTS, k.parse_corrections(CORRECTIONS))
        self.assertEqual(f["row ^LQFP-"], {"both": [], "top": [1], "bottom": []})
        self.assertEqual(f["part entry (seen on the other side only)"], {"both": [], "top": [], "bottom": [1]})
        self.assertEqual(f["no row"], {"both": [2], "top": [], "bottom": []})
        self.assertEqual(k.cells_words([1, 12]), "01, 12")

    def test_the_readme_names_the_screenshots_the_stop_and_the_unconfirmed_part_numbers(self):
        pages = {"C1": '<span class="detail-info-badge x">Extended</span>', "C2": ""}
        text = k.readme_md(1, PARTS, k.parse_corrections(CORRECTIONS), pages, (172.0, 76.0), {"bom": 2})
        self.assertIn("# Calibration kit 1: ", text)
        self.assertIn("172 by 76 mm", text)
        self.assertIn("the whole board;", text)
        self.assertIn("a zoom on each quadrant", text)
        self.assertIn("**Do not press \"Save to cart\"**", text)
        self.assertIn("**Unconfirmed part numbers on this board:** `C2` (cell 02)", text)
        self.assertIn("| 01 | C1 | Extended | MCU | LQFP-48_7x7mm_P0.5mm | confirmed |", text)
        self.assertIn("- `C2` (cell 02, unconfirmed): fit not compared", text)
        self.assertIn("at least 70 mm on each side", text)
        self.assertIn("| row ^LQFP- | cells 01 on the top side only |", text)
        self.assertIn("| part entry (seen on the other side only) | cells 01 on the bottom side only |", text)
        self.assertIn("| no row | cells 02 on both sides |", text)
        self.assertIn("No part number of this board is unconfirmed.",
                      k.readme_md(1, PARTS[:1], k.parse_corrections(CORRECTIONS), pages, (172.0, 76.0), {"bom": 1}))


if __name__ == "__main__":
    unittest.main()
