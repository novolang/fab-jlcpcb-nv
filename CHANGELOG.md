# Changelog

All notable changes to fab-jlcpcb-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## [0.1.2] — 2026-11-26

### Changed

- The four `proposed` entries of `fjdata.part_rotations` are `verified`, seen on the top side on 2026-11-26: `C295747` (S2B-PH-SM4-TB, adds 0: the contacts sit on the signal pads), `C2895249` (nRF52833 QFN-40, adds 0: the model's dot and pin 1 mark sit on the silk triangle), `C2652978` (TXB0106RGYR VQFN-16, adds 270: the dot sits on the silk mark) and `C404280` (MHPA1010RGBDT RGB LED, adds 90: "1+" sits at the marked corner). The table holds 33 entries, all verified. The status `proposed` and its handling in the placement file, the sheet and the check `rotations` stay for the next part a preview draws wrong.

### Added

- `fjdata.economic_rows`, the manufacturer's table "PCB Specs for Economic PCB Assembly" as the order form showed it on 2026-11-26 (layers, thickness, solder mask colours, surface finishes, quantity), and `fjdata.economic_choices`, the rows that hold for a board's layers and thickness and for a chosen quantity.
- The check `economic-table` (a warning): the rows of the table that keep the board Economic, or why there is none. An 8-layer board has none: the table lists 2, 4 and 6 layers, and the form offered the 8-layer feather PCBA Type Standard only, with Economic greyed out. The check also fails for a board with placed parts on both sides: the form greyed out Assembly Side Both Sides under Economic on 2026-11-26. The package has twenty checks.
- The step 2 of "On the web form" in the order sheet of an Economic board names the surface finish and the solder mask colour to set before PCB Assembly is switched on, from the table's rows for the board, and says that the finish the form preselects can rule Economic out: on 2026-11-26 the form greyed out Economic on a 2-layer, 1.6 mm, green board until the Surface Finish was set to "LeadFree HASL"; the form had preselected OSP, which is in no row of the table, and the default may change.
- The section "The assembly" of the order sheet lists the combinations of colour, finish and quantity on the form that keep the board Economic, or says that none exists and why (the layer count, the thickness, the quantity, or parts on both sides). For an Economic board it also states what the form showed on 2026-11-26 with Economic selected on a 2-layer, 33.29 by 18.06 mm board: the board kept its own size with no edge rails, tooling holes were added by JLCPCB, Assembly Side offered Top Side or Bottom Side only, and PCBA Qty offered 5 or 2.

- An open question of the order sheet names the other PCB choices that the form preselects and a board file does not hold, as observed on 2026-11-26 on a 2-layer board: with PCB Assembly off, Via Plating Method Not Specified and no Material Type or Via Plating Method charge line (OSP $4.10, LeadFree HASL $5.20); with PCB Assembly on and Economic selected, Material Type FR4 TG135 and Via Plating Method Horizontal Electroless Copper Plating, 3.32 each; whether Standard does the same was not observed. It adds that OSP is the cheaper finish on the bare board and rules Economic out.

- `tools/calib`: three calibration boards for a dry-run suite, each part of a footprint family placed once on the top and once on the bottom side on a labelled grid, with a silk triangle at pin 1, written as KiCad projects from KiCad's footprint library; `parts.csv` with 70 parts and their JLCPCB part numbers, each `confirmed` or `unconfirmed` against its public part page; `calib_kit.py`, which makes the order package of each board and writes a kit with a README of the steps and screenshots and a `results.md` table. The tests are `tests/fj_calib_tests.nv` and `tests/calib_test.py`.

### Known

- Four parts of the 8-layer board were not drawn in the preview of 2026-11-26 for lack of stock (U1, U2 the nPM1300, U4 and the crystal Y1); they have no entry.

## [0.1.1] — 2026-11-25

### Added

- `fjdata.part_rotations`, a table of rotations keyed by JLCPCB part number: for a part number, the rotation to add, the offset, a status (`verified` when the preview of the order form drew the part right with the value, `proposed` when the preview drew it wrong with the family value and the entry holds the value read from the picture), the sides seen and the date. The preview draws each part from its own model, so the rotation a part needs follows its part number. The table holds 29 verified entries and four proposed ones (`C295747`, `C2895249`, `C2652978`, `C404280`), all from the dry runs of 2026-11-25.
- The lookup order for a part: its part-number entry when it has one, otherwise the family table. `fjcpl.rows_for` takes the entries and the bill; `fjcpl.rows` keeps the family table alone. `fjbom.part_of` reads the part number of a designator.
- A source for the rotation of every placed part: verified part, proposed part, part verified on the other side only, family row, rotation field, or the board's own value. `corrections.txt` has a line for every placed part with its source, and the order sheet names it for each part in the section of the rotation of every placed part.
- The order sheet has a section near the top, `Rotations not verified`, that lists the parts whose rotation no preview has shown right with the value written and says to check each in the form's preview before ordering. A board whose every rotation is verified has one line in its place.
- `host_only = true` in the manifest: the package declares itself host-only.

### Changed

- The check `rotations` warns for a proposed part entry, a part entry seen on the other side only, a family row that adds a rotation and a rotation field; a verified part entry is no longer a correction to review.
- `corrections.txt` lists every placed part, not only the parts whose rotation or position changed, and ends with the count of rows for each source.

### Fixed

- The rotation of a `SOT-23-5` footprint. The table row `^SOT-23` gave 180 degrees to the three-lead and the five-lead package alike, and JLCPCB's preview drew the five-lead parts a quarter turn off. The row `^SOT-23-5` at 270 degrees stands before `^SOT-23`, which keeps 180 for the other footprints it matches.
- The rotation of the parts that the family table drew wrong in the preview of 2026-11-25: the nRF52833 QFN-40 (`^QFN-`), the JST PH connector (`^JST_PH_S`), a VQFN-16 level shifter and an RGB LED that have no row. Each has a proposed part entry.
- The order sheet names the PCBA Type to select on the form (Economic or Standard) in its first lines and says that the form may preselect the other type. A quote taken with the type left alone was priced as Standard assembly.

### Known

- The four proposed entries are read from pictures and not yet seen right; each is named in the order sheet of a board that has the part.
- The preview has shown `SOT-23` at 180 and `SOT-23-5` at 270. It has not shown `SOT-23-5_HandSoldering`, which the row `^SOT-23-5` matches on the ground that its pads are those of `SOT-23-5`; nor `SOT-23-6`, `SOT-23-8`, `SOT-23W`, `SOT-23_Handsoldering`, `TSOT-23-5`, `TSOT-23-6` or `D_SOT-23`, whose rows are the Toolkit's.
- Three parts of the 8-layer board were not drawn in the preview (the module, the nPM1300 and the flash) and a crystal had no model; they have no entry.

## [0.1.0] — 2026-11-24

The package is the one published as fab-package-nv 0.1.0 on 2026-11-24, under the name that says which manufacturer it is for, with the changes that a first dry run on JLCPCB's form called for.

### Added

- `fjpack.prepare`, the JLCPCB order package of a revision that passed its gates: the Gerber and drill zip, the bill of materials, the placement file, the list of corrections, the order sheet and a manifest with hashes.
- `fjcpl`, the placement file with the rotation and position corrections of the Fabrication Toolkit, and `fjdata`, the Toolkit's rotation table and the manufacturer's limits as data with their sources.
- `fjcheck`, nineteen checks of the design against the manufacturer's published limits and against itself; `fjbom`, `fjboard`, `fjsheet` and `fjzip`.
- `fjoverlay`, the check `placement-on-gerber`: every numbered pad of every placed part, laid out from its placement row, must lie on its own flash in the copper layers, and `positions-agree` compares the rows with KiCad's own position export. A placement file that does not share the Gerbers' origin cannot be written.
- `fjcatalog`, the saved public part pages: library, assembly class, and the checks `part-pages`, `part-assembly-class` and `extended-parts`. A part that only Standard assembly places forces the order into Standard and is an error on a board that is Economic by itself.
- A part with no part number is never left to JLCPCB's matcher: it is an error and the package writes only the sheet, or it is listed under `[do_not_place]` in the policy with its reason and is in neither file.

### Fixed

- The origin of the placement file and the Gerber files: the Gerbers and the drill files are now written relative to the auxiliary axis origin (hardware-gates-nv 0.1.1), the same origin as the placement file. A first order drew every part about 12 mm off.
- A via is held to the drill and diameter limits (0.15 mm hole, 0.25 mm across, 0.1 mm over its drill); the annular ring limit is for plated pads, as the capability page states it.

### Known

- Nothing was uploaded to the manufacturer by the package or by its author. A person ran a first dry run on the form by hand on 2026-11-24 and stopped before the cart.
- The placements in the preview have not been seen after the origin fix, and no board with parts on the bottom has been through the form.
